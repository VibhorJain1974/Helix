// src/OfflineIndicator.tsx
/**
 * OfflineIndicator Component
 * Shows when device is offline
 */

import React, { useEffect, useState } from 'react'
import { useConnection } from './ConnectionContext'

export const OfflineIndicator: React.FC = () => {
  const { setOnlineStatus } = useConnection()
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setOnlineStatus(true)
    }
    const handleOffline = () => {
      setIsOnline(false)
      setOnlineStatus(false)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [setOnlineStatus])

  if (isOnline) return null

  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-950 border-b border-yellow-800 px-4 py-2 text-center text-sm text-yellow-200 z-50">
      You are offline. Some features may be limited.
    </div>
  )
}
