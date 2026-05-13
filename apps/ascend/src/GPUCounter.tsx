// src/GPUCounter.tsx
/**
 * GPUCounter Component
 * Displays GPU contribution metrics
 */

import React, { useState, useEffect } from 'react'
import { useConnection } from './ConnectionContext'

interface GPUCounterProps {
  webgpuOk: boolean | null
}

export const GPUCounter: React.FC<GPUCounterProps> = ({ webgpuOk }) => {
  const { state } = useConnection()
  const [totalFrames, setTotalFrames] = useState(0)

  useEffect(() => {
    const total = state.gpuContributions.reduce((sum, c) => sum + c.frames, 0)
    setTotalFrames(total)
  }, [state.gpuContributions])

  const activeGpuCount = state.peers.filter((p) => p.gpuContribution && p.gpuContribution > 0).length

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="bg-slate-800 border border-slate-700 rounded p-3 text-center">
        <div className="text-2xl font-bold text-indigo-400">{activeGpuCount}</div>
        <div className="text-xs uppercase tracking-widest text-slate-400 mt-2">Active GPUs</div>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded p-3 text-center">
        <div className="text-2xl font-bold text-green-400">{totalFrames.toLocaleString()}</div>
        <div className="text-xs uppercase tracking-widest text-slate-400 mt-2">Frames</div>
      </div>
    </div>
  )
}
