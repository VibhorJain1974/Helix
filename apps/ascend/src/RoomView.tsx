// src/RoomView.tsx
/**
 * RoomView Component
 * Shows room code, peer list, participant counter
 */

import React from 'react'
import { useRoom } from './RoomContext'
import { useConnection } from './ConnectionContext'
import { ParticipantCounter } from './ParticipantCounter'

export const RoomView: React.FC = () => {
  const { room, leaveRoom } = useRoom()
  const { state } = useConnection()

  if (!room) return null

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-300">Room Code</h3>
          <div className="text-2xl font-mono font-bold text-indigo-400 mt-1">{room.code}</div>
        </div>
        <button
          onClick={leaveRoom}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-sm transition"
        >
          Leave
        </button>
      </div>

      <div className="border-t border-slate-700 pt-4">
        <ParticipantCounter peers={state.peers} />
      </div>

      {/* Peer List */}
      {state.peers.length > 0 && (
        <div className="border-t border-slate-700 mt-4 pt-4">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Connected Peers ({state.peers.length})
          </h4>
          <div className="space-y-2">
            {state.peers.map((peer) => (
              <div key={peer.peerId} className="flex items-center gap-2 text-sm">
                <div
                  className={`w-2 h-2 rounded-full ${
                    peer.status === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}
                />
                <span className="text-slate-300">{peer.displayName}</span>
                <span className="text-xs text-slate-500">({peer.status})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      <div className="border-t border-slate-700 mt-4 pt-4 text-xs text-slate-500">
        Status: <span className="text-slate-400">{state.state}</span>
      </div>
    </div>
  )
}
