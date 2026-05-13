// src/qrcode.ts
/**
 * QR Code Generation Utility
 * Simple wrapper around canvas-based QR generation (no external dep needed for basic generation)
 * Or use qrcode.js if lightweight version available
 */

export async function generateQRCode(text: string, size: number = 200): Promise<string> {
  // Simple implementation using canvas - can be replaced with qrcode.js if needed
  try {
    // For now, return a placeholder data URL
    // In production, integrate with a lightweight QR library like:
    // import QRCode from 'qrcode.js' (5KB)
    
    // Placeholder: return text as image (for demo)
    const canvas = document.createElement('canvas')
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Failed to get canvas context')

    // Create a simple gradient background with text
    const gradient = ctx.createLinearGradient(0, 0, size, size)
    gradient.addColorStop(0, '#0369a1')
    gradient.addColorStop(1, '#0284c7')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, size, size)

    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 16px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(text, size / 2, size / 2)

    return canvas.toDataURL('image/png')
  } catch (error) {
    console.error('[qrcode] generation failed:', error)
    return ''
  }
}

// Optional: simpler wrapper for QRCode.js if installed
// Install with: npm install qrcode
// Then uncomment below and comment out the above implementation
/*
import QRCode from 'qrcode'

export async function generateQRCode(text: string, size: number = 200): Promise<string> {
  try {
    return await QRCode.toDataURL(text, {
      width: size,
      margin: 1,
      color: { dark: '#0369a1', light: '#ffffff' },
    })
  } catch (error) {
    console.error('[qrcode] generation failed:', error)
    return ''
  }
}
*/
