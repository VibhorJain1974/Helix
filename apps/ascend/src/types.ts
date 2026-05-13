// src/types.ts
/**
 * ASCEND Room and Connection Types
 * Typed models for room management, peer discovery, and connection state.
 */

export interface Room {
  id: string
  code: string
  createdAt: Date
  expiresAt: Date
}

export interface Peer {
  peerId: string
  displayName: string
  status: 'connecting' | 'connected' | 'disconnected'
  gpuContribution?: number
  lastSeen: Date
}

export interface GPUContribution {
  peerId: string
  frames: number
  timestamp: Date
}

export type ASCENDState = 'idle' | 'joining' | 'connected' | 'error' | 'offline'

export interface ConnectionState {
  state: ASCENDState
  room: Room | null
  peers: Peer[]
  localPeerId: string | null
  error: string | null
  isOnline: boolean
  gpuContributions: GPUContribution[]
}

export interface SignalingMessage {
  type: 'offer' | 'answer' | 'candidate' | 'peers' | 'ping'
  peerId: string
  data?: any
}

export interface WebRTCConfig {
  iceServers?: RTCIceServer[]
  signalingUrl?: string
}
