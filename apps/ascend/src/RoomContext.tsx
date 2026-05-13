// src/RoomContext.tsx
/**
 * Room Context and Provider
 * Manages room state: creation, joining, room code persistence via URL hash
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { Room } from './types'

interface RoomContextType {
  room: Room | null
  setRoom: (room: Room | null) => void
  roomCode: string
  createRoom: () => Promise<string>
  joinRoom: (code: string) => Promise<void>
  leaveRoom: () => void
}

const RoomContext = createContext<RoomContextType | undefined>(undefined)

export const RoomProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [room, setRoom] = useState<Room | null>(null)
  const [roomCode, setRoomCode] = useState<string>('')

  // Load room code from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash.slice(1)
    if (hash) {
      setRoomCode(hash)
    }
  }, [])

  // Update URL hash when room code changes
  useEffect(() => {
    if (roomCode) {
      window.location.hash = roomCode
    }
  }, [roomCode])

  const createRoom = useCallback(async (): Promise<string> => {
    // Generate a simple room code (6-8 char alphanumeric)
    const code = Math.random().toString(36).substring(2, 10).toUpperCase()
    const room: Room = {
      id: code,
      code,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24h expiry
    }
    setRoom(room)
    setRoomCode(code)
    return code
  }, [])

  const joinRoom = useCallback(async (code: string): Promise<void> => {
    // Validate code format (alphanumeric, 6-10 chars)
    if (!/^[A-Z0-9]{6,10}$/.test(code)) {
      throw new Error('Invalid room code')
    }
    const room: Room = {
      id: code,
      code,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
    }
    setRoom(room)
    setRoomCode(code)
  }, [])

  const leaveRoom = useCallback(() => {
    setRoom(null)
    setRoomCode('')
    window.location.hash = ''
  }, [])

  return (
    <RoomContext.Provider value={{ room, setRoom, roomCode, createRoom, joinRoom, leaveRoom }}>
      {children}
    </RoomContext.Provider>
  )
}

export const useRoom = (): RoomContextType => {
  const context = useContext(RoomContext)
  if (!context) {
    throw new Error('useRoom must be used within RoomProvider')
  }
  return context
}
