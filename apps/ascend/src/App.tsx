// apps/ascend/src/App.tsx
// ASCEND — Citizen Drug Discovery
// M5 (Rohan): Three.js protein viewer + molecule counter
// M1 (Vibhor): WebGPU WGSL docking kernel — see src/lib/docking.wgsl
import React, { useEffect, useState } from 'react'
import { RoomProvider } from './RoomContext'
import { ConnectionProvider } from './ConnectionContext'
import { AscendShell } from './AscendShell'
import { ErrorBoundary } from './ErrorBoundary'
import { OfflineIndicator } from './OfflineIndicator'

function AppContent() {
  const [webgpuOk, setWebgpuOk] = useState<boolean | null>(null)

  useEffect(() => {
    if ('gpu' in navigator) {
      (navigator as any).gpu.requestAdapter()
        .then((a: any) => setWebgpuOk(!!a))
        .catch(() => setWebgpuOk(false))
    } else {
      setWebgpuOk(false)
    }
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-white font-mono">
      <OfflineIndicator />
      <AscendShell webgpuOk={webgpuOk} />
      {!webgpuOk && webgpuOk !== null && (
        <div className="fixed bottom-4 left-4 right-4 max-w-sm mx-auto p-3 bg-red-950 border border-red-700 rounded text-sm text-red-200 text-center">
          ASCEND requires Chrome 113+. Please open in Chrome.
        </div>
      )}
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <RoomProvider>
        <ConnectionProvider>
          <AppContent />
        </ConnectionProvider>
      </RoomProvider>
    </ErrorBoundary>
  )
}