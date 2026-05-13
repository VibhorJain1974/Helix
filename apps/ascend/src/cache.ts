// src/cache.ts
/**
 * Cache Management Utilities
 * Handles service worker cache versioning and strategies
 */

export const CACHE_VERSION = 'ascend-v1'
export const ASSETS_CACHE = `${CACHE_VERSION}-assets`
export const NETWORK_CACHE = `${CACHE_VERSION}-network`

export async function cacheAsset(request: Request, response: Response): Promise<void> {
  try {
    const cache = await caches.open(ASSETS_CACHE)
    await cache.put(request, response.clone())
  } catch (e) {
    console.warn('[cache] Failed to cache asset:', e)
  }
}

export async function getCachedAsset(request: Request): Promise<Response | undefined> {
  try {
    const cache = await caches.open(ASSETS_CACHE)
    return await cache.match(request)
  } catch (e) {
    console.warn('[cache] Failed to get cached asset:', e)
    return undefined
  }
}

export async function clearOldCaches(): Promise<void> {
  try {
    const cacheNames = await caches.keys()
    const oldCaches = cacheNames.filter((name) => !name.includes(CACHE_VERSION))
    await Promise.all(oldCaches.map((name) => caches.delete(name)))
  } catch (e) {
    console.warn('[cache] Failed to clear old caches:', e)
  }
}

export async function getNetworkCache(): Promise<Cache | null> {
  try {
    return await caches.open(NETWORK_CACHE)
  } catch (e) {
    console.warn('[cache] Failed to open network cache:', e)
    return null
  }
}
