// apps/vera/src/App.tsx
// DISCLAIMER: VERA is a screening tool only. Confirm with qualified health worker.
import React, { useEffect, useRef, useState, useCallback } from 'react'
import { initTF, loadModel, runInference, isModelLoaded, type InferenceResult } from './lib/inference'

type AppState = 'init' | 'ready' | 'camera' | 'scanning' | 'result' | 'error'

const MODEL_URL = '/models/vera/model.json'

export default function App() {
  const videoRef  = useRef<HTMLVideoElement>(null)
  const [state, setState]   = useState<AppState>('init')
  const [tfBackend, setTfBackend] = useState('')
  const [modelLoaded, setModelLoaded] = useState(false)
  const [result, setResult] = useState<InferenceResult | null>(null)
  const [errMsg, setErrMsg] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Init TF.js on mount
  useEffect(() => {
    initTF()
      .then(backend => {
        setTfBackend(backend)
        // Try loading model — fails gracefully if not trained yet
        return loadModel(MODEL_URL)
      })
      .then(() => {
        setModelLoaded(true)
        setState('ready')
      })
      .catch(() => {
        // Model not available yet — camera still works, inference disabled
        setState('ready')
      })
  }, [])

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setState('camera')
        if (modelLoaded) startInferenceLoop()
      }
    } catch (e) {
      setErrMsg('Camera denied: ' + (e as Error).message)
      setState('error')
    }
  }

  const startInferenceLoop = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    intervalRef.current = setInterval(async () => {
      if (!videoRef.current || !isModelLoaded()) return
      try {
        setState('scanning')
        const res = await runInference(videoRef.current)
        setResult(res)
        setState('result')
      } catch { /* keep scanning */ }
    }, 2000)
  }, [])

  useEffect(() => () => {
    if (intervalRef.current) clearInterval(intervalRef.current)
  }, [])

  const confidenceColor = (c: number) => c >= 80 ? '#4ade80' : c >= 60 ? '#facc15' : '#f87171'

  return (
    <div style={{
      background: '#050505', minHeight: '100vh', color: '#fff',
      fontFamily: '"Courier New", monospace', display: 'flex',
      flexDirection: 'column', alignItems: 'center', padding: '24px 16px'
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ fontSize: 10, letterSpacing: 6, color: '#4ade80', marginBottom: 4 }}>
          HELIX · VERA
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: 2 }}>
          DISEASE DIAGNOSIS
        </div>
        <div style={{ fontSize: 10, color: '#444', marginTop: 4 }}>
          {tfBackend ? `TF.js · ${tfBackend.toUpperCase()}` : 'Loading...'} ·{' '}
          {modelLoaded ? '✓ MODEL' : '⚠ NO MODEL (train first)'}
        </div>
      </div>

      {/* Camera feed */}
      <div style={{
        width: '100%', maxWidth: 480, aspectRatio: '4/3',
        background: '#111', borderRadius: 8, overflow: 'hidden',
        border: `1px solid ${state === 'result' ? '#4ade80' : '#222'}`,
        position: 'relative'
      }}>
        <video ref={videoRef} autoPlay playsInline muted
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
        {state === 'scanning' && (
          <div style={{
            position: 'absolute', inset: 0, border: '2px solid #4ade80',
            borderRadius: 8, animation: 'pulse 1s infinite',
            background: 'rgba(74,222,128,0.05)'
          }} />
        )}
        {state !== 'camera' && state !== 'scanning' && state !== 'result' && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center', color: '#333', fontSize: 12
          }}>
            CAMERA INACTIVE
          </div>
        )}
      </div>

      {/* Start button */}
      {(state === 'ready' || state === 'init') && (
        <button onClick={startCamera} style={{
          marginTop: 20, padding: '14px 40px', background: '#4ade80',
          color: '#000', border: 'none', borderRadius: 6, cursor: 'pointer',
          fontFamily: 'inherit', fontSize: 14, fontWeight: 700, letterSpacing: 2
        }}>
          START CAMERA
        </button>
      )}

      {/* Result card */}
      {result && state === 'result' && (
        <div style={{
          marginTop: 20, width: '100%', maxWidth: 480,
          background: '#0f1a0f', border: '1px solid #4ade80',
          borderRadius: 8, padding: '16px 20px'
        }}>
          <div style={{ fontSize: 9, letterSpacing: 4, color: '#4ade80', marginBottom: 8 }}>
            CLASSIFICATION
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
            {result.label.toUpperCase()}
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: confidenceColor(result.confidence) }}>
            {result.confidence}%
          </div>
          <div style={{ fontSize: 10, color: '#666', marginBottom: 12 }}>
            confidence · {result.latencyMs}ms · target {'<'}4000ms
          </div>
          <div style={{ fontSize: 9, letterSpacing: 3, color: '#4ade80', marginBottom: 6 }}>
            TREATMENT PROTOCOL
          </div>
          <div style={{ fontSize: 12, color: '#ccc', lineHeight: 1.6 }}>
            {result.treatment}
          </div>
          {/* DISCLAIMER: Required on every result screen per NFR-5 */}
          <div style={{
            marginTop: 12, padding: '8px 12px', background: '#1a1a1a',
            borderRadius: 4, fontSize: 10, color: '#666', lineHeight: 1.5
          }}>
            ⚠ Screening tool only. Confirm with qualified health worker.
            Not a clinical diagnosis.
          </div>
        </div>
      )}

      {/* Error */}
      {state === 'error' && (
        <div style={{ marginTop: 16, color: '#f87171', fontSize: 12 }}>{errMsg}</div>
      )}

      <style>{`
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
      `}</style>
    </div>
  )
}