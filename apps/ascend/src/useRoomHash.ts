// src/useRoomHash.ts
/**
 * Hook for managing room code via URL hash
 * Automatically syncs room code with window.location.hash
 */

import { useEffect, useState } from 'react'

export const useRoomHash = (): { code: string; setCode: (code: string) => void } => {
  const [code, setCodeState] = useState<string>('')

  // Load from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash.slice(1)
    if (hash) {
      setCodeState(hash)
    }
  }, [])

  // Update URL hash and state when code changes
  const setCode = (newCode: string) => {
    setCodeState(newCode)
    if (newCode) {
      window.location.hash = newCode
    } else {
      window.location.hash = ''
    }
  }

  return { code, setCode }
}
