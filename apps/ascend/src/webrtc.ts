// src/webrtc.ts
/**
 * WebRTC Peer Manager
 * Manages peer connections with DataChannel support
 * Gracefully handles connection failures
 */

import { env } from './env'

export interface PeerConnection {
  peerId: string
  connection: RTCPeerConnection
  dataChannel: RTCDataChannel | null
  isInitiator: boolean
}

export class PeerManager {
  private peers: Map<string, PeerConnection> = new Map()
  private localPeerId: string = ''
  private onPeerConnected: ((peerId: string) => void) | null = null
  private onPeerDisconnected: ((peerId: string) => void) | null = null
  private onDataMessage: ((peerId: string, data: any) => void) | null = null

  createPeerConnection(remotePeerId: string, isInitiator: boolean): RTCPeerConnection {
    const config: RTCConfiguration = {
      iceServers: env.iceServers,
    }

    const pc = new RTCPeerConnection(config)

    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate) {
        if (env.enableDevLogs) {
          console.log(`[webrtc] ICE candidate for ${remotePeerId}`)
        }
      }
    }

    // Handle connection state changes
    pc.onconnectionstatechange = () => {
      if (env.enableDevLogs) {
        console.log(`[webrtc] connection state: ${pc.connectionState}`)
      }

      if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
        this.removePeer(remotePeerId)
        this.onPeerDisconnected?.(remotePeerId)
      } else if (pc.connectionState === 'connected') {
        this.onPeerConnected?.(remotePeerId)
      }
    }

    // Create or handle data channel
    if (isInitiator) {
      const dc = pc.createDataChannel('ascend', { ordered: true })
      this.setupDataChannel(remotePeerId, dc)
    } else {
      pc.ondatachannel = (event) => {
        this.setupDataChannel(remotePeerId, event.channel)
      }
    }

    // Store peer connection
    const peerConn: PeerConnection = {
      peerId: remotePeerId,
      connection: pc,
      dataChannel: null,
      isInitiator,
    }

    this.peers.set(remotePeerId, peerConn)
    return pc
  }

  private setupDataChannel(peerId: string, dc: RTCDataChannel): void {
    dc.onopen = () => {
      if (env.enableDevLogs) console.log(`[webrtc] data channel open: ${peerId}`)
    }

    dc.onclose = () => {
      if (env.enableDevLogs) console.log(`[webrtc] data channel closed: ${peerId}`)
    }

    dc.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.onDataMessage?.(peerId, data)
      } catch (e) {
        console.warn('[webrtc] failed to parse data channel message:', e)
      }
    }

    dc.onerror = (error) => {
      console.error('[webrtc] data channel error:', error)
    }

    const peer = this.peers.get(peerId)
    if (peer) {
      peer.dataChannel = dc
    }
  }

  sendData(peerId: string, data: any): void {
    const peer = this.peers.get(peerId)
    if (!peer?.dataChannel || peer.dataChannel.readyState !== 'open') {
      console.warn(`[webrtc] data channel not ready for ${peerId}`)
      return
    }

    try {
      peer.dataChannel.send(JSON.stringify(data))
    } catch (e) {
      console.error('[webrtc] failed to send data:', e)
    }
  }

  broadcast(data: any): void {
    this.peers.forEach((peer) => {
      this.sendData(peer.peerId, data)
    })
  }

  getPeer(peerId: string): PeerConnection | undefined {
    return this.peers.get(peerId)
  }

  getPeers(): PeerConnection[] {
    return Array.from(this.peers.values())
  }

  removePeer(peerId: string): void {
    const peer = this.peers.get(peerId)
    if (peer) {
      peer.connection.close()
      this.peers.delete(peerId)
    }
  }

  closeAll(): void {
    this.peers.forEach((peer) => {
      peer.connection.close()
    })
    this.peers.clear()
  }

  setLocalPeerId(peerId: string): void {
    this.localPeerId = peerId
  }

  onPeerConnectedCallback(cb: (peerId: string) => void): void {
    this.onPeerConnected = cb
  }

  onPeerDisconnectedCallback(cb: (peerId: string) => void): void {
    this.onPeerDisconnected = cb
  }

  onDataMessageCallback(cb: (peerId: string, data: any) => void): void {
    this.onDataMessage = cb
  }
}

export function createPeerManager(): PeerManager {
  return new PeerManager()
}
