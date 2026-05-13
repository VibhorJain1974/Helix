// src/RoomForm.tsx
/**
 * RoomForm Component
 * Create or join room with code input
 */

import React, { useState } from 'react'
import { useRoom } from './RoomContext'
import { useConnection } from './ConnectionContext'

export const RoomForm: React.FC = () => {
  const { createRoom, joinRoom } = useRoom()
  const [codeInput, setCodeInput] = useState('')
  const [mode, setMode] = useState<'create' | 'join'>('create')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    try {
      setLoading(true)
      setError(null)
      await createRoom()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create room')
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)
      if (!codeInput.trim()) {
        throw new Error('Room code required')
      }
      await joinRoom(codeInput.trim().toUpperCase())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join room')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-lg p-6">
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setMode('create')}
            className={`flex-1 py-2 px-4 rounded transition ${
              mode === 'create'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            Create Room
          </button>
          <button
            onClick={() => setMode('join')}
            className={`flex-1 py-2 px-4 rounded transition ${
              mode === 'join'
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            Join Room
          </button>
        </div>

        {mode === 'create' ? (
          <button
            onClick={handleCreate}
            disabled={loading}
            className="w-full py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 text-white font-semibold rounded transition"
          >
            {loading ? 'Creating...' : 'Create New Room'}
          </button>
        ) : (
          <form onSubmit={handleJoin}>
            <input
              type="text"
              placeholder="Enter room code"
              value={codeInput}
              onChange={(e) => setCodeInput(e.target.value)}
              maxLength={10}
              className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded text-white placeholder-slate-500 mb-3 uppercase font-mono"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !codeInput.trim()}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold rounded transition"
            >
              {loading ? 'Joining...' : 'Join Room'}
            </button>
          </form>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-950 border border-red-800 rounded text-sm text-red-200">
            {error}
          </div>
        )}
      </div>
    </div>
  )
}
