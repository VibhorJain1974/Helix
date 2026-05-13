// src/service-worker-template.js
/**
 * SERVICE WORKER TEMPLATE
 * Copy this file to public/service-worker.js
 * 
 * This service worker implements a cache-first strategy for assets
 * and network-first with cache fallback for API calls.
 */

const CACHE_VERSION = 'ascend-v1'
const ASSETS_CACHE = `${CACHE_VERSION}-assets`
const NETWORK_CACHE = `${CACHE_VERSION}-network`

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(ASSETS_CACHE).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((e) => {
        console.warn('[sw] static asset cache failed:', e)
      })
    })
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names
          .filter((name) => !name.includes(CACHE_VERSION))
          .map((name) => caches.delete(name))
      )
    })
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return
  }

  // Strategy: cache-first for assets
  if (
    request.url.includes('.js') ||
    request.url.includes('.css') ||
    request.url.includes('.json') ||
    request.url.includes('.svg') ||
    request.url.includes('.png') ||
    request.url.includes('.jpg')
  ) {
    event.respondWith(
      caches.match(request).then((response) => {
        if (response) return response
        return fetch(request).then((response) => {
          // Cache successful responses
          if (response.status === 200) {
            const cloned = response.clone()
            caches.open(ASSETS_CACHE).then((cache) => {
              cache.put(request, cloned)
            })
          }
          return response
        })
      })
    )
    return
  }

  // Strategy: network-first for API calls and documents
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.status === 200) {
          const cloned = response.clone()
          caches.open(NETWORK_CACHE).then((cache) => {
            cache.put(request, cloned)
          })
        }
        return response
      })
      .catch(() => {
        return caches.match(request).then((response) => {
          if (response) return response
          // Offline fallback for HTML
          if (request.mode === 'navigate') {
            return caches.match('/index.html')
          }
          return new Response('Offline', { status: 503 })
        })
      })
  )
})
