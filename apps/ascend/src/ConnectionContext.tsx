// src/ConnectionContext.tsx
/**
 * Connection Context
 * Manages peer list, connection state, and GPU contributions
 */

import React, { createContext, useContext, useState, useCallback } from 'react'
import { ConnectionState, Peer, GPUContribution, ASCENDState } from './types'

interface ConnectionContextType {
  state: ConnectionState
  setState: (state: ConnectionState) => void
  addPeer: (peer: Peer) => void
  removePeer: (peerId: string) => void
  updatePeerStatus: (peerId: string, status: Peer['status']) => void
  recordGPUContribution: (peerId: string, frames: number) => void
  setConnectionState: (state: ASCENDState) => void
  setError: (error: string | null) => void
  setOnlineStatus: (isOnline: boolean) => void
}

const ConnectionContext = createContext<ConnectionContextType | undefined>(undefined)

const initialState: ConnectionState = {
  state: 'idle',
  room: null,
  peers: [],
  localPeerId: null,
  error: null,
  isOnline: navigator.onLine,
  gpuContributions: [],
}

export const ConnectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<ConnectionState>(initialState)

  const addPeer = useCallback((peer: Peer) => {
    setState((prev) => ({
      ...prev,
      peers: [...prev.peers.filter((p) => p.peerId !== peer.peerId), peer],
    }))
  }, [])

  const removePeer = useCallback((peerId: string) => {
    setState((prev) => ({
      ...prev,
      peers: prev.peers.filter((p) => p.peerId !== peerId),
    }))
  }, [])

  const updatePeerStatus = useCallback((peerId: string, status: Peer['status']) => {
    setState((prev) => ({
      ...prev,
      peers: prev.peers.map((p) => (p.peerId === peerId ? { ...p, status } : p)),
    }))
  }, [])

  const recordGPUContribution = useCallback((peerId: string, frames: number) => {
    setState((prev) => ({
      ...prev,
      gpuContributions: [
        ...prev.gpuContributions,
        { peerId, frames, timestamp: new Date() },
      ],
    }))
  }, [])

  const setConnectionState = useCallback((newState: ASCENDState) => {
    setState((prev) => ({ ...prev, state: newState }))
  }, [])

  const setError = useCallback((error: string | null) => {
    setState((prev) => ({ ...prev, error }))
  }, [])

  const setOnlineStatus = useCallback((isOnline: boolean) => {
    setState((prev) => ({ ...prev, isOnline }))
  }, [])

  return (
    <ConnectionContext.Provider
      value={{
        state,
        setState,
        addPeer,
        removePeer,
        updatePeerStatus,
        recordGPUContribution,
        setConnectionState,
        setError,
        setOnlineStatus,
      }}
    >
      {children}
    </ConnectionContext.Provider>
  )
}

export const useConnection = (): ConnectionContextType => {
  const context = useContext(ConnectionContext)
  if (!context) {
    throw new Error('useConnection must be used within ConnectionProvider')
  }
  return context
}
