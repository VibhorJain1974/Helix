// src/useServiceWorker.ts
/**
 * useServiceWorker Hook
 * Registers service worker with cache versioning
 */

import { useEffect, useState } from 'react'
import { env } from './env'
import { CACHE_VERSION } from './cache'

interface ServiceWorkerStatus {
  registered: boolean
  updateAvailable: boolean
  error: string | null
}

export const useServiceWorker = (): ServiceWorkerStatus => {
  const [status, setStatus] = useState<ServiceWorkerStatus>({
    registered: false,
    updateAvailable: false,
    error: null,
  })

  useEffect(() => {
    if (!env.enableServiceWorker || !('serviceWorker' in navigator)) {
      return
    }

    const register = async () => {
      try {
        const registration = await navigator.serviceWorker.register('/service-worker.js', {
          scope: '/',
        })

        setStatus((prev) => ({ ...prev, registered: true }))

        if (env.enableDevLogs) {
          console.log('[sw] registered:', registration)
        }

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'activated') {
                setStatus((prev) => ({ ...prev, updateAvailable: true }))
                if (env.enableDevLogs) {
                  console.log('[sw] update available')
                }
              }
            })
          }
        })

        // Periodic check for updates
        setInterval(() => {
          registration.update().catch((e) => {
            console.warn('[sw] update check failed:', e)
          })
        }, 60000) // Check every minute
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Registration failed'
        setStatus((prev) => ({ ...prev, error: message }))
        console.error('[sw] registration error:', error)
      }
    }

    // Delay registration slightly to avoid blocking app startup
    const timeoutId = setTimeout(register, 1000)
    return () => clearTimeout(timeoutId)
  }, [])

  // Store cache version for potential offline detection
  useEffect(() => {
    try {
      sessionStorage.setItem('ascend-cache-version', CACHE_VERSION)
    } catch (e) {
      console.warn('[sw] failed to store cache version:', e)
    }
  }, [])

  return status
}
