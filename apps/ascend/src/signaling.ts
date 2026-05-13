// src/signaling.ts
/**
 * Signaling Client
 * WebSocket-based signaling for WebRTC peer discovery
 * Abstracted interface for env-configured endpoint
 */

import { SignalingMessage } from './types'
import { env } from './env'

type SignalingMessageHandler = (msg: SignalingMessage) => void

export interface ISignalingClient {
  connect(peerId: string, roomCode: string): Promise<void>
  disconnect(): void
  send(msg: SignalingMessage): void
  onMessage(handler: SignalingMessageHandler): void
  isConnected(): boolean
}

export class SignalingClient implements ISignalingClient {
  private ws: WebSocket | null = null
  private peerId: string = ''
  private roomCode: string = ''
  private messageHandlers: Set<SignalingMessageHandler> = new Set()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  async connect(peerId: string, roomCode: string): Promise<void> {
    this.peerId = peerId
    this.roomCode = roomCode

    return new Promise((resolve, reject) => {
      try {
        const url = `${env.signalingUrl}?peerId=${peerId}&room=${roomCode}`
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          if (env.enableDevLogs) console.log('[signaling] connected')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const msg: SignalingMessage = JSON.parse(event.data)
            this.messageHandlers.forEach((handler) => handler(msg))
          } catch (e) {
            console.warn('[signaling] failed to parse message:', e)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[signaling] error:', error)
          reject(new Error('Signaling connection failed'))
        }

        this.ws.onclose = () => {
          if (env.enableDevLogs) console.log('[signaling] disconnected')
          this.attemptReconnect()
        }
      } catch (e) {
        reject(e)
      }
    })
  }

  private attemptReconnect = () => {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      if (env.enableDevLogs) console.log(`[signaling] reconnecting in ${delay}ms...`)
      setTimeout(() => {
        this.connect(this.peerId, this.roomCode).catch((e) => {
          console.error('[signaling] reconnect failed:', e)
        })
      }, delay)
    } else {
      console.error('[signaling] max reconnect attempts reached')
      // Optionally reset and allow user to manually reconnect
      // this.reconnectAttempts = 0
    }
  }

  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(msg: SignalingMessage): void {
    if (!this.isConnected()) {
      console.warn('[signaling] not connected, cannot send:', msg)
      return
    }
    try {
      this.ws!.send(JSON.stringify(msg))
    } catch (e) {
      console.error('[signaling] send failed:', e)
    }
  }

  onMessage(handler: SignalingMessageHandler): void {
    this.messageHandlers.add(handler)
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export function createSignalingClient(): ISignalingClient {
  return new SignalingClient()
}
