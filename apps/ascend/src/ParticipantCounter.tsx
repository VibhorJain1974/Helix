// src/ParticipantCounter.tsx
/**
 * ParticipantCounter Component
 * Shows count of active participants
 */

import React from 'react'
import { Peer } from './types'

interface ParticipantCounterProps {
  peers: Peer[]
}

export const ParticipantCounter: React.FC<ParticipantCounterProps> = ({ peers }) => {
  const connectedCount = peers.filter((p) => p.status === 'connected').length
  const total = peers.length

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="bg-slate-800 border border-slate-700 rounded p-3 text-center">
        <div className="text-2xl font-bold text-indigo-400">{total + 1}</div>
        <div className="text-xs uppercase tracking-widest text-slate-400 mt-2">Total Peers</div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded p-3 text-center">
        <div className="text-2xl font-bold text-green-400">{connectedCount}</div>
        <div className="text-xs uppercase tracking-widest text-slate-400 mt-2">Connected</div>
      </div>
    </div>
  )
}
