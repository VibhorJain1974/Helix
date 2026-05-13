// apps/ascend/src/App.tsx
// ASCEND — Citizen Drug Discovery
// M5 (Rohan): Three.js protein viewer + molecule counter
// M1 (Vibhor): WebGPU WGSL docking kernel — see src/lib/docking.wgsl
import React, { useEffect, useRef, useState } from 'react'

export default function App() {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [gpuCount, setGpuCount] = useState(1)
  const [molecules, setMolecules] = useState(0)
  const [webgpuOk, setWebgpuOk] = useState<boolean | null>(null)

  useEffect(() => {
    // Check WebGPU availability
    if ('gpu' in navigator) {
      (navigator as any).gpu.requestAdapter()
        .then((a: any) => setWebgpuOk(!!a))
        .catch(() => setWebgpuOk(false))
    } else {
      setWebgpuOk(false)
    }
  }, [])

  return (
    <div style={{
      background: '#04050f', minHeight: '100vh', color: '#fff',
      fontFamily: '"Courier New", monospace', padding: '24px 16px',
      display: 'flex', flexDirection: 'column', alignItems: 'center'
    }}>
      <div style={{ fontSize: 10, letterSpacing: 6, color: '#818cf8', marginBottom: 4 }}>
        HELIX · ASCEND
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: 2, marginBottom: 4 }}>
        CITIZEN DRUG DISCOVERY
      </div>
      <div style={{ fontSize: 10, color: '#444', marginBottom: 32 }}>
        TARGET: MRSA PBP2a · {webgpuOk === null ? 'Checking WebGPU...' :
          webgpuOk ? '✓ WebGPU available' : '⚠ WebGPU unavailable — Chrome 113+ required'}
      </div>

      {/* Protein viewer placeholder — Three.js goes here (M5/Rohan) */}
      <div ref={canvasRef} style={{
        width: '100%', maxWidth: 480, height: 280,
        background: '#0a0b1a', borderRadius: 8, border: '1px solid #1e2040',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#333', fontSize: 12, marginBottom: 24
      }}>
        [ MRSA PBP2a · Three.js protein viewer · M5 builds here ]
      </div>

      {/* GPU counter */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
        width: '100%', maxWidth: 480, marginBottom: 24
      }}>
        {[
          { label: 'ACTIVE GPUS', value: gpuCount, color: '#818cf8' },
          { label: 'MOLECULES SCORED', value: molecules.toLocaleString(), color: '#4ade80' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{
            background: '#0a0b1a', border: '1px solid #1e2040',
            borderRadius: 8, padding: '16px', textAlign: 'center'
          }}>
            <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
            <div style={{ fontSize: 9, letterSpacing: 3, color: '#444', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {!webgpuOk && webgpuOk !== null && (
        <div style={{
          padding: '12px 20px', background: '#1a0a0a', border: '1px solid #f87171',
          borderRadius: 6, fontSize: 11, color: '#f87171', maxWidth: 480, textAlign: 'center'
        }}>
          ASCEND requires Chrome 113+. Open this URL in Chrome on a laptop.
        </div>
      )}
    </div>
  )
}