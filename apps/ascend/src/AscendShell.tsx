// src/AscendShell.tsx
/**
 * ASCEND Shell Component
 * Main layout with header, content area, and peer list
 */

import React, { useState } from 'react'
import { useRoom } from './RoomContext'
import { useConnection } from './ConnectionContext'
import { RoomForm } from './RoomForm'
import { RoomView } from './RoomView'
import { GPUCounter } from './GPUCounter'

interface AscendShellProps {
  webgpuOk: boolean | null
}

export const AscendShell: React.FC<AscendShellProps> = ({ webgpuOk }) => {
  const { room } = useRoom()
  const { state } = useConnection()

  return (
    <div className="flex flex-col h-screen bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900 px-4 py-4 sm:px-6">
        <div className="text-xs tracking-widest text-indigo-400 uppercase">Helix · ASCEND</div>
        <h1 className="text-2xl font-bold tracking-wider mt-1">Citizen Drug Discovery</h1>
        <p className="text-xs text-slate-500 mt-2">
          TARGET: MRSA PBP2a ·{' '}
          {webgpuOk === null
            ? 'Checking WebGPU...'
            : webgpuOk
              ? '✓ WebGPU available'
              : '⚠ Chrome 113+ required'}
        </p>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col sm:flex-row gap-4 p-4 sm:p-6">
        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-4">
          {!room ? (
            <RoomForm />
          ) : (
            <>
              <RoomView />
              {/* Protein viewer placeholder — Three.js goes here (M5/Rohan) */}
              <div className="flex-1 bg-slate-900 border border-slate-800 rounded-lg flex items-center justify-center text-slate-500 text-sm">
                [ MRSA PBP2a · Three.js protein viewer · M5 builds here ]
              </div>
            </>
          )}
        </div>

        {/* Right Sidebar — Counters & Peer List */}
        <div className="w-full sm:w-64 flex flex-col gap-4">
          <GPUCounter webgpuOk={webgpuOk} />
          {room && <RoomView />}
        </div>
      </div>

      {/* Status Bar */}
      {state.error && (
        <div className="bg-red-950 border-t border-red-800 px-4 py-3 text-sm text-red-200">
          {state.error}
        </div>
      )}
    </div>
  )
}
