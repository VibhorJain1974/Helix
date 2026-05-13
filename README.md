# HELIX

**Discover the drug. Diagnose the disease. Verify the pill. All offline. All free.**

Browser-native zero-infrastructure healthcare sovereignty stack.

## Components
- **VERA** — Skin disease diagnosis via TF.js WebGL. Camera → result in 4s. Offline.
- **VERUM** — Counterfeit medicine detection via CIELab colour + DCT analysis.
- **ASCEND** — Citizen drug discovery via WebGPU compute shaders + WebRTC mesh.

## Quick Start
```bash
git clone https://github.com/VibhorJain1974/Helix.git
cd Helix
pnpm install
pnpm --filter vera dev      # http://localhost:5173
pnpm --filter verum dev     # http://localhost:5174
pnpm --filter ascend dev    # http://localhost:5175
```

## Mobile Testing (HTTPS required for camera)
```bash
ngrok http 5173
# Open the https:// URL on Android Chrome
```

## ML Training
```bash
conda activate helix
python scripts/prep_vera_data.py    # after downloading ISIC 2019
python scripts/train_vera.py --data datasets/vera --output models/vera
python scripts/export_vera.py --checkpoint models/vera/best.pt
```

## Team — FAR AWAY by Zuup
Competing in Japan finale · 4,413 global teams · May 2026

## Disclaimers
VERA and VERUM are screening tools only. Results require confirmation by a qualified health worker.