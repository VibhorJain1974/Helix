// src/env.ts
/**
 * Environment configuration and feature flags
 * Load from import.meta.env, with sensible production defaults.
 */

interface Env {
  signalingUrl: string
  enableDevLogs: boolean
  enableQRCode: boolean
  enableServiceWorker: boolean
  iceServers: RTCIceServer[]
  appVersion: string
}

function getEnv(): Env {
  const isDev = import.meta.env.DEV
  const signalingUrl = import.meta.env.VITE_SIGNALING_URL || 'ws://localhost:3000/ws'
  const enableDevLogs = isDev || import.meta.env.VITE_DEV_LOGS === 'true'
  const enableQRCode = import.meta.env.VITE_QR_CODE !== 'false'
  const enableServiceWorker = import.meta.env.VITE_SERVICE_WORKER !== 'false'
  const appVersion = import.meta.env.VITE_APP_VERSION || 'dev'

  // Default STUN servers (Google's public servers)
  const iceServers: RTCIceServer[] = [
    { urls: ['stun:stun.l.google.com:19302', 'stun:stun1.l.google.com:19302'] },
  ]

  if (import.meta.env.VITE_ICE_SERVERS) {
    try {
      const customServers = JSON.parse(import.meta.env.VITE_ICE_SERVERS)
      iceServers.push(...customServers)
    } catch (e) {
      console.warn('[env] Failed to parse VITE_ICE_SERVERS')
    }
  }

  return {
    signalingUrl,
    enableDevLogs,
    enableQRCode,
    enableServiceWorker,
    iceServers,
    appVersion,
  }
}

export const env = getEnv()
