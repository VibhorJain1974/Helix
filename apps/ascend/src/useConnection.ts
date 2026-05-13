// src/useConnection.ts
/**
 * useConnection Hook
 * Combines SignalingClient + PeerManager for unified WebRTC + signaling flow
 */

import { useEffect, useRef, useCallback } from 'react'
import { SignalingClient, ISignalingClient } from './signaling'
import { PeerManager } from './webrtc'
import { Peer } from './types'
import { env } from './env'

interface UseConnectionOptions {
  peerId: string
  roomCode: string
  onPeerJoined?: (peer: Peer) => void
  onPeerLeft?: (peerId: string) => void
  onError?: (error: string) => void
}

export const useConnection = (options: UseConnectionOptions) => {
  const signalingRef = useRef<ISignalingClient | null>(null)
  const peerManagerRef = useRef<PeerManager | null>(null)
  const connectedPeersRef = useRef<Set<string>>(new Set())

  const connect = useCallback(async () => {
    try {
      signalingRef.current = new SignalingClient()
      peerManagerRef.current = new PeerManager()

      peerManagerRef.current.setLocalPeerId(options.peerId)

      // Setup callbacks
      peerManagerRef.current.onPeerConnectedCallback((peerId) => {
        connectedPeersRef.current.add(peerId)
        if (env.enableDevLogs) console.log(`[useConnection] peer connected: ${peerId}`)
      })

      peerManagerRef.current.onPeerDisconnectedCallback((peerId) => {
        connectedPeersRef.current.delete(peerId)
        options.onPeerLeft?.(peerId)
        if (env.enableDevLogs) console.log(`[useConnection] peer disconnected: ${peerId}`)
      })

      peerManagerRef.current.onDataMessageCallback((peerId, data) => {
        if (env.enableDevLogs) console.log(`[useConnection] data from ${peerId}:`, data)
      })

      // Connect signaling
      await signalingRef.current.connect(options.peerId, options.roomCode)

      // Handle signaling messages
      signalingRef.current.onMessage((msg) => {
        handleSignalingMessage(msg, options)
      })

      if (env.enableDevLogs) console.log('[useConnection] connected to signaling')
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Connection failed'
      console.error('[useConnection] error:', errorMsg)
      options.onError?.(errorMsg)
    }
  }, [options])

  const handleSignalingMessage = useCallback((msg: any, opts: UseConnectionOptions) => {
    const { type, peerId: remotePeerId, data } = msg

    if (type === 'peers') {
      // Received list of peers in room
      const peers = data || []
      peers.forEach((peer: any) => {
        if (peer.peerId !== opts.peerId && !connectedPeersRef.current.has(peer.peerId)) {
          initiateConnection(peer.peerId)
        }
      })
    }

    if (type === 'offer' && remotePeerId && remotePeerId !== opts.peerId) {
      handleOffer(remotePeerId, data)
    }

    if (type === 'answer' && remotePeerId && remotePeerId !== opts.peerId) {
      handleAnswer(remotePeerId, data)
    }

    if (type === 'candidate' && remotePeerId && remotePeerId !== opts.peerId) {
      handleCandidate(remotePeerId, data)
    }
  }, [])

  const initiateConnection = useCallback((remotePeerId: string) => {
    try {
      const pc = peerManagerRef.current!.createPeerConnection(remotePeerId, true)

      pc.createOffer()
        .then((offer) => {
          pc.setLocalDescription(offer)
          signalingRef.current!.send({
            type: 'offer',
            peerId: remotePeerId,
            data: offer,
          })
        })
        .catch((e) => console.error('[useConnection] offer error:', e))
    } catch (e) {
      console.error('[useConnection] initiate connection error:', e)
    }
  }, [])

  const handleOffer = useCallback((remotePeerId: string, offer: RTCSessionDescriptionInit) => {
    try {
      let pc = peerManagerRef.current!.getPeer(remotePeerId)?.connection
      if (!pc) {
        pc = peerManagerRef.current!.createPeerConnection(remotePeerId, false)
      }

      pc.setRemoteDescription(new RTCSessionDescription(offer))
        .then(() => pc!.createAnswer())
        .then((answer) => {
          pc!.setLocalDescription(answer)
          signalingRef.current!.send({
            type: 'answer',
            peerId: remotePeerId,
            data: answer,
          })
        })
        .catch((e) => console.error('[useConnection] answer error:', e))
    } catch (e) {
      console.error('[useConnection] handle offer error:', e)
    }
  }, [])

  const handleAnswer = useCallback((remotePeerId: string, answer: RTCSessionDescriptionInit) => {
    try {
      const pc = peerManagerRef.current!.getPeer(remotePeerId)?.connection
      if (pc) {
        pc.setRemoteDescription(new RTCSessionDescription(answer)).catch((e) => {
          console.error('[useConnection] set remote description error:', e)
        })
      }
    } catch (e) {
      console.error('[useConnection] handle answer error:', e)
    }
  }, [])

  const handleCandidate = useCallback((remotePeerId: string, candidate: RTCIceCandidateInit) => {
    try {
      const pc = peerManagerRef.current!.getPeer(remotePeerId)?.connection
      if (pc && candidate) {
        pc.addIceCandidate(new RTCIceCandidate(candidate)).catch((e) => {
          console.error('[useConnection] add ice candidate error:', e)
        })
      }
    } catch (e) {
      console.error('[useConnection] handle candidate error:', e)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (signalingRef.current) {
      signalingRef.current.disconnect()
    }
    if (peerManagerRef.current) {
      peerManagerRef.current.closeAll()
    }
  }, [])

  const sendData = useCallback((peerId: string, data: any) => {
    if (peerManagerRef.current) {
      peerManagerRef.current.sendData(peerId, data)
    }
  }, [])

  const broadcast = useCallback((data: any) => {
    if (peerManagerRef.current) {
      peerManagerRef.current.broadcast(data)
    }
  }, [])

  const getPeers = useCallback(() => {
    return peerManagerRef.current?.getPeers() || []
  }, [])

  return {
    connect,
    disconnect,
    sendData,
    broadcast,
    getPeers,
    signalingRef,
    peerManagerRef,
  }
}
