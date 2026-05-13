// src/QRJoinFlow.tsx
/**
 * QRJoinFlow Component
 * QR code generation and join flow for mobile
 */

import React, { useState, useEffect } from 'react'
import { useRoom } from './RoomContext'
import { generateQRCode } from './qrcode'

export const QRJoinFlow: React.FC = () => {
  const { room, roomCode } = useRoom()
  const [qrCode, setQrCode] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!room || !roomCode) {
      setQrCode('')
      return
    }

    const generateQR = async () => {
      try {
        setLoading(true)
        const roomUrl = `${window.location.origin}/#${roomCode}`
        const dataUrl = await generateQRCode(roomUrl, 256)
        setQrCode(dataUrl)
      } catch (error) {
        console.error('[QRJoinFlow] QR generation failed:', error)
      } finally {
        setLoading(false)
      }
    }

    generateQR()
  }, [room, roomCode])

  if (!room || !qrCode) {
    return null
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 max-w-sm">
        <h3 className="text-lg font-semibold text-white mb-4">Join via QR Code</h3>
        
        {loading ? (
          <div className="w-64 h-64 bg-slate-800 rounded flex items-center justify-center text-slate-400">
            Generating...
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            {qrCode && (
              <img
                src={qrCode}
                alt="Room QR Code"
                className="w-64 h-64 border-2 border-slate-700 rounded"
              />
            )}
            <div className="text-center">
              <p className="text-sm text-slate-400 mb-2">Or enter code:</p>
              <p className="text-2xl font-mono font-bold text-indigo-400">{roomCode}</p>
            </div>
          </div>
        )}

        <button
          onClick={() => setQrCode('')}
          className="mt-4 w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition"
        >
          Close
        </button>
      </div>
    </div>
  )
}
