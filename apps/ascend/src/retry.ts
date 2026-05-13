// src/retry.ts
/**
 * Retry Utility
 * Exponential backoff for network operations
 */

export interface RetryOptions {
  maxAttempts?: number
  initialDelay?: number
  maxDelay?: number
  backoffMultiplier?: number
  shouldRetry?: (error: any) => boolean
}

const DEFAULT_OPTIONS: RetryOptions = {
  maxAttempts: 5,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
}

export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  let attempt = 0
  let lastError: any

  while (attempt < opts.maxAttempts!) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      attempt++

      if (opts.shouldRetry && !opts.shouldRetry(error)) {
        throw error
      }

      if (attempt >= opts.maxAttempts!) {
        throw error
      }

      const delay = Math.min(
        opts.initialDelay! * Math.pow(opts.backoffMultiplier!, attempt - 1),
        opts.maxDelay!
      )

      await new Promise((resolve) => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

export class ReconnectManager {
  private attempt = 0
  private maxAttempts: number
  private initialDelay: number
  private maxDelay: number
  private backoffMultiplier: number

  constructor(options: RetryOptions = {}) {
    const opts = { ...DEFAULT_OPTIONS, ...options }
    this.maxAttempts = opts.maxAttempts!
    this.initialDelay = opts.initialDelay!
    this.maxDelay = opts.maxDelay!
    this.backoffMultiplier = opts.backoffMultiplier!
  }

  canRetry(): boolean {
    return this.attempt < this.maxAttempts
  }

  getDelay(): number {
    return Math.min(
      this.initialDelay * Math.pow(this.backoffMultiplier, this.attempt),
      this.maxDelay
    )
  }

  recordAttempt(): void {
    this.attempt++
  }

  reset(): void {
    this.attempt = 0
  }
}
