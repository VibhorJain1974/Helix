// src/logger.ts
/**
 * Logger Utility
 * Dev-only logging, no-op in production
 */

import { env } from './env'

export const logger = {
  dev: (message: string, data?: any) => {
    if (env.enableDevLogs) {
      console.log(`[ascend] ${message}`, data || '')
    }
  },
  warn: (message: string, error?: any) => {
    console.warn(`[ascend] ${message}`, error || '')
  },
  error: (message: string, error?: any) => {
    console.error(`[ascend] ${message}`, error || '')
  },
}
