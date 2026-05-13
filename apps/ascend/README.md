# ASCEND — Citizen Drug Discovery

A collaborative WebRTC mesh + PWA frontend for distributed drug discovery simulations.

## 📋 Implementation Summary

This implementation provides a production-ready ASCEND application with:

### ✅ Completed Features

#### **Foundation**
- TypeScript strict mode configuration
- Tailwind CSS setup with responsive design
- Clean component/hook/service folder structure

#### **Core Models & State**
- Typed ASCEND models (Room, Peer, ConnectionState, etc.)
- Environment configuration system
- Room context with URL hash synchronization
- Connection context with peer management
- GPU contribution tracking

#### **Signaling & WebRTC**
- SignalingClient abstraction (WebSocket-based, env-configured)
- PeerManager with DataChannel support
- Integrated signal/peer lifecycle management
- Graceful error handling with exponential backoff reconnects

#### **UI Components**
- AscendShell: Main layout with header and peer list
- RoomForm: Create/join room interface
- RoomView: Room code display and peer list
- ParticipantCounter: Show active peers
- GPUCounter: Track GPU contributions
- ErrorBoundary: Catch React errors
- OfflineIndicator: Show offline status
- QRJoinFlow: QR code generation for mobile sharing

#### **PWA & Offline**
- PWA manifest.json template
- Service worker template with cache strategy
- useServiceWorker hook with auto-updates
- Cache versioning system
- Offline-first asset caching
- Network-first API caching with offline fallback

#### **Utilities**
- Logger with dev-only output
- QR code generation
- Retry logic with exponential backoff
- ReconnectManager for network resilience

## 📁 Project Structure

```
apps/ascend/
├── public/                    # Static assets (PWA manifest, icons)
│   ├── manifest.json         # PWA manifest
│   └── service-worker.js     # Service worker (copy from template)
├── src/
│   ├── components/           # React components
│   │   ├── AscendShell.tsx
│   │   ├── RoomForm.tsx
│   │   ├── RoomView.tsx
│   │   ├── ParticipantCounter.tsx
│   │   ├── GPUCounter.tsx
│   │   ├── QRJoinFlow.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── OfflineIndicator.tsx
│   ├── contexts/             # React contexts
│   │   ├── RoomContext.tsx
│   │   └── ConnectionContext.tsx
│   ├── hooks/                # Custom hooks
│   │   ├── useRoom.ts        (exported from RoomContext)
│   │   ├── useConnection.ts  (exported from ConnectionContext)
│   │   ├── useRoomHash.ts
│   │   ├── useServiceWorker.ts
│   │   └── useOfflineStatus.ts (in OfflineIndicator)
│   ├── services/             # Business logic
│   │   ├── signaling.ts      # WebSocket signaling client
│   │   ├── webrtc.ts         # Peer manager
│   │   ├── cache.ts          # SW cache utilities
│   │   └── env.ts            # Environment config
│   ├── utils/                # Helper utilities
│   │   ├── logger.ts
│   │   ├── qrcode.ts
│   │   └── retry.ts
│   ├── types.ts              # Shared TypeScript types
│   ├── App.tsx               # Root component (with providers)
│   ├── main.tsx              # React entry point
│   ├── index.css             # Tailwind CSS
│   └── service-worker-template.js
├── vite.config.ts
├── tsconfig.json
├── postcss.config.js
├── tailwind.config.js
├── index.html
└── package.json
```

## 🚀 Getting Started

### Installation

```bash
cd apps/ascend
pnpm install
```

### Development

```bash
pnpm dev
```

Opens at `http://localhost:5175` (or configured port).

### Build

```bash
pnpm build
```

### Type Check

```bash
pnpm type-check
```

## 🔧 Configuration

### Environment Variables

Create `.env.local` or set environment vars:

```bash
VITE_SIGNALING_URL=ws://localhost:3000/ws    # WebSocket signaling endpoint
VITE_DEV_LOGS=true                            # Enable dev-only logging
VITE_QR_CODE=true                             # Enable QR code generation
VITE_SERVICE_WORKER=true                      # Enable service worker registration
VITE_ICE_SERVERS='[...]'                      # JSON array of STUN/TURN servers
VITE_APP_VERSION=1.0.0                        # App version
```

### Tailwind Configuration

Edit `tailwind.config.js` to customize colors, theme, etc. Includes ascend color palette:

```js
ascend: { 50, 100, 200, 500, 600, 700, 900 }
```

## 📱 Mobile Support

- Responsive Tailwind classes (sm:, md:, lg: breakpoints)
- Viewport meta tag with safe area support
- Touch-friendly UI
- PWA installable on mobile

## 🔐 Security & Best Practices

- TypeScript strict mode enforced (no 'any', no @ts-ignore without reason)
- All async operations have try/catch
- No sensitive data in localStorage (sessionStorage for cache version only)
- Service worker registration doesn't block app startup
- Error messages user-facing and calm (no stack traces in UI)
- All external network calls are scoped

## 🛠️ Manual Setup Required

### 1. Create Public Directory Files

The `public/` directory needs these files. Copy `service-worker-template.js` to `public/service-worker.js`:

**public/manifest.json** (copy from root or create):
```json
{
  "name": "ASCEND — Citizen Drug Discovery",
  "short_name": "ASCEND",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#000000",
  "theme_color": "#0369a1",
  "icons": [...]
}
```

**public/service-worker.js** (copy `service-worker-template.js`):
- Cache-first strategy for assets
- Network-first for API calls
- Offline fallback

### 2. Implement Signaling Server

ASCEND expects a WebSocket signaling server at `VITE_SIGNALING_URL`. Example flow:

```
Client1 → (signaling)
         ↓ /ws?peerId=X&room=ROOM123
         Signaling Server
         ↓ /ws?peerId=Y&room=ROOM123
Client2 → (offers/answers/candidates exchanged via server)
```

Your signaling server should:
- Accept `/ws` connections with `peerId` and `room` query params
- Broadcast offers/answers/ICE candidates between peers
- Send "peers" list when new peer joins
- Handle reconnections gracefully

### 3. WebGPU & Three.js Integration

Commented placeholders remain for:
- **M5 (Rohan)**: Three.js protein viewer in `AscendShell.tsx`
- **M1 (Vibhor)**: WebGPU WGSL docking kernel (see `.cursorrules`)

Wire these into the existing component structure as needed.

## 🔄 Application Flow

1. **User opens ASCEND** → App checks WebGPU availability
2. **Create/Join Room** → RoomForm triggers room creation/join, sets URL hash
3. **Room established** → RoomView shows code, initiates signaling connection
4. **Peer discovery** → Signaling server sends list of peers, WebRTC connections form
5. **Connected** → Peer list updates, GPU counters track contributions
6. **Offline** → OfflineIndicator shows, cached assets served, graceful degradation
7. **Reconnect** → Exponential backoff, automatic retry with user notification

## 🔌 WebRTC Data Channel

Peers exchange data via DataChannel when connected:

```typescript
// From RoomView/GPU counter component:
broadcast({ type: 'gpu-frame', frames: N })

// Received in PeerManager.onDataMessage callback
```

## 📊 State Management

**RoomContext**:
- `room`: Current room object
- `roomCode`: Room code (synced to URL hash)
- `createRoom()`, `joinRoom(code)`, `leaveRoom()`

**ConnectionContext**:
- `state`: Connection state (idle, joining, connected, error, offline)
- `peers`: List of connected peers
- `gpuContributions`: GPU metrics
- Methods: `addPeer()`, `removePeer()`, `updatePeerStatus()`, etc.

## 📖 API Reference

### useRoom Hook

```typescript
const { room, roomCode, createRoom, joinRoom, leaveRoom } = useRoom()
```

### useConnection Hook

```typescript
const conn = useConnection({
  peerId: 'peer-id',
  roomCode: 'ROOM123',
  onPeerJoined: (peer) => {},
  onPeerLeft: (peerId) => {},
  onError: (error) => {},
})

conn.connect()
conn.disconnect()
conn.sendData(peerId, data)
conn.broadcast(data)
```

### useServiceWorker Hook

```typescript
const { registered, updateAvailable, error } = useServiceWorker()
```

## ⚠️ Known Limitations & TODO

- [ ] Public directory structure needs manual creation (manifest.json, service-worker.js)
- [ ] Signaling server implementation required (not included)
- [ ] Three.js protein viewer integration (M5)
- [ ] WebGPU WGSL docking kernel (M1)
- [ ] QRCode.js optional dependency for true QR codes (current: canvas-based placeholder)
- [ ] Analytics/metrics collection (future)
- [ ] User authentication/authorization (future)

## 🚨 Error Handling

All major operations have try/catch:
- Signaling connection failures → graceful degradation
- WebRTC peer failures → peer removed, retry logic
- Service worker registration → doesn't block startup
- Offline → UI updates, cache served

## 📝 Dev Logs

Dev-only logs via `logger.dev()`:
```typescript
import { logger } from './logger'
logger.dev('message', data)  // Only logs if VITE_DEV_LOGS=true
```

## 🧪 Testing

No tests included yet. Suggested structure:
- Unit tests for utils (retry, logger, cache)
- Integration tests for contexts/hooks
- E2E tests for room create/join flow

## 📄 License

Part of the Helix project. See root LICENSE.

## 🤝 Contributing

See `.cursorrules` for project conventions:
- TypeScript strict mode
- Tailwind CSS (no custom CSS without approval)
- All async ops have try/catch
- Medical disclaimer comments on output screens
- Mobile-first responsive design

---

**Last Updated**: 2026-05-13
**Status**: Alpha (production-ready foundation, missing M5/M1 integrations)
