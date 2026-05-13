# VERUM Photography Protocol
**HELIX — M3 VERUM Database Lead**
FAR AWAY by Zuup | May 2026

---

## Before You Start — What You Need

| Item | Details |
|---|---|
| **Phone** | The exact demo device (rear camera, max resolution) |
| **Calibration card** | Printed A6, laminated — see Section 2 |
| **Medicines** | Purchased from GMP-certified pharmacy — keep receipt |
| **Surfaces** | Plain white A4 paper as background |
| **Lighting rigs** | See Section 3 for each condition setup |

---

## Section 1 — Medicines to Photograph

These are the 5 medicines in scope for VERUM v1:

| # | Medicine | Form | WHO List |
|---|---|---|---|
| 1 | Amoxicillin 500mg | Capsules in blister pack | ✅ Essential |
| 2 | Artemether-Lumefantrine 20/120mg | Tablets in blister pack | ✅ Essential |
| 3 | Metformin 500mg | Tablets in blister pack | ✅ Essential |
| 4 | Paracetamol 500mg | Tablets in blister pack | ✅ Essential |
| 5 | ORS sachets | Sachet | ✅ Essential |

**Buy from a GMP-certified pharmacy only.**
Photograph the pharmacy receipt and the GMP certificate alongside the first sample of each medicine. Store these photos in `datasets/verum/provenance/`.

---

## Section 2 — Calibration Card

The calibration card is photographed with EVERY medicine sample. Without it, colour measurements cannot be normalised across different lighting conditions.

### Print Instructions
- Size: A6 (105mm × 148mm)
- Print at exactly 100% scale — do not scale to fit
- Use a colour laser printer (inkjet colour shifts over time)
- After printing: **laminate immediately**

### Card Contents (in order, left to right)
```
[ 18% Grey Patch ]  [ White Patch ]  [ 5mm Scale Bar ]  [ Medicine Name Label ]
   40mm × 40mm        40mm × 40mm      5mm marked line     e.g. "AMOXICILLIN"
```

### Why Each Element
- **18% grey patch** — standard photographic reference for exposure
- **White patch** — used by `process_verum.py` for white balance normalisation
- **5mm scale bar** — allows geometry vector to convert pixels to millimetres
- **Medicine name label** — prevents mix-ups during bulk photography sessions

### Placement in Every Photo
Place the calibration card **flat on the white background**, touching the left edge of the blister pack. Both card and medicine must be fully in frame. Neither should cast a shadow on the other.

```
Photo frame:
┌─────────────────────────────────┐
│                                 │
│  [Calibration Card] [Medicine]  │
│                                 │
└─────────────────────────────────┘
```

---

## Section 3 — Lighting Conditions

Each medicine must be photographed under all 5 lighting conditions below. This teaches the model that the same authentic medicine looks different under different lights — and prevents false positives from lighting variation.

### Condition 1 — Natural Daylight
- Place setup near a window, no direct sunlight hitting the sample
- Overcast day preferred (diffused light, no harsh shadows)
- Time: between 10am and 3pm only
- **Do not use** on rainy days (colour temperature shifts dramatically)

### Condition 2 — Overhead Fluorescent
- Standard office/pharmacy fluorescent tube light
- Phone held directly above sample at 30cm height
- Turn off all other lights in the room
- Target: 4000K colour temperature (cool white)

### Condition 3 — LED Warm
- Desk lamp with warm LED bulb (2700K)
- Position lamp at 45° angle, 40cm from sample
- Turn off all other lights

### Condition 4 — LED Cool
- Desk lamp with cool LED bulb (6500K daylight)
- Same position as Condition 3
- Turn off all other lights

### Condition 5 — Low Light
- Single desk lamp at 1 metre distance
- Dim but not dark — phone camera should not activate night mode
- If phone auto-enables night mode: move lamp 20cm closer

---

## Section 4 — Camera Settings

These settings apply to every single photo. Do not change mid-session.

| Setting | Value | Why |
|---|---|---|
| **Resolution** | Maximum available | More pixels = better frequency analysis |
| **HDR** | OFF | HDR merges exposures — ruins frequency vector |
| **Flash** | OFF | Flash creates hot spots that break colour vector |
| **AI enhancement** | OFF | AI sharpening alters the print frequency vector |
| **Night mode** | OFF | Only activate if image is completely black |
| **Zoom** | 1x (no zoom) | Digital zoom degrades image quality |
| **Focus** | Tap to focus on medicine | Ensure blister pack text is sharp |
| **Orientation** | Landscape | Consistent framing across all photos |

---

## Section 5 — Shot Protocol

For each medicine × lighting condition:

1. Place white A4 paper flat on table
2. Place calibration card on the left side of the paper
3. Place blister pack on the right side, touching the card
4. Hold phone directly above at 30cm height (use a stack of books as a rest if needed)
5. Tap screen to focus on the blister pack text
6. Wait 2 seconds for exposure to stabilise
7. Take 3 photos without moving anything
8. Check: all 3 photos are sharp, card is fully visible, no shadows on medicine

**Total per medicine:**
30 authentic packs × 5 lighting conditions × 3 shots = **450 images**

**Total across all 5 medicines:**
450 × 5 = **2,250 authentic images**

---

## Section 6 — File Naming Convention

Every photo must follow this exact naming format:

```
{medicine}_{lot}_{condition}_{label}_{shot}.jpg
```

### Examples
```
amox_LOT2024_fluorescent_authentic_001.jpg
amox_LOT2024_fluorescent_authentic_002.jpg
amox_LOT2024_fluorescent_authentic_003.jpg
amox_LOT2024_natural_authentic_001.jpg
paracetamol_LOT2024_led_warm_authentic_001.jpg
artemether_LOT2024_low_light_counterfeit_001.jpg
```

### Medicine Short Codes
| Medicine | Code |
|---|---|
| Amoxicillin | `amox` |
| Artemether-Lumefantrine | `artemether` |
| Metformin | `metformin` |
| Paracetamol | `paracetamol` |
| ORS sachets | `ors` |

### Lighting Condition Codes
| Condition | Code |
|---|---|
| Natural daylight | `natural` |
| Overhead fluorescent | `fluorescent` |
| LED warm 2700K | `led_warm` |
| LED cool 6500K | `led_cool` |
| Low light | `low_light` |

### Label Codes
| Sample type | Code |
|---|---|
| Verified authentic | `authentic` |
| Known counterfeit | `counterfeit` |

---

## Section 7 — Counterfeit Sample Sourcing

Minimum 5 counterfeit samples per medicine are required for model training.

### Approved Sources
1. **WHO/Interpol published seizure databases** — contact WHO Essential Medicines team
2. **Pharmacy school analytical chemistry lab** — university pharmacy departments often hold seized samples for research
3. **Published academic counterfeit medicine research groups** — search PubMed for "counterfeit amoxicillin" + contact corresponding authors

### Rules
- Do NOT purchase medicines across international borders
- Do NOT purchase from unverified online sources
- Keep all sourcing correspondence as documentation
- Counterfeit samples go in a separate labelled bag — never mix with authentic samples

### Photography of Counterfeit Samples
Same protocol as authentic — all 5 lighting conditions, 3 shots each, calibration card in frame. Filename must contain `counterfeit`.

---

## Section 8 — Day 1 Checklist

This is the non-negotiable Day 1 task. Every item must be completed.

- [ ] GMP-certified pharmacy identified and visited
- [ ] Amoxicillin 500mg purchased (minimum 30 blister packs, same lot)
- [ ] Pharmacy receipt photographed → saved to `datasets/verum/provenance/`
- [ ] GMP certificate photographed → saved to `datasets/verum/provenance/`
- [ ] Calibration card printed and laminated
- [ ] All 5 lighting setups tested with a test photo
- [ ] Amoxicillin photographed under all 5 lighting conditions (450 images)
- [ ] All images renamed following Section 6 naming convention
- [ ] Images placed in `datasets/verum/samples/`
- [ ] `build_db.py` run successfully on Day 1 images (partial database is fine)

---

## Section 9 — Quality Check

After each photography session, review photos for:

| Issue | What to look for | Fix |
|---|---|---|
| **Blur** | Blister pack text not readable | Retake — tap to focus again |
| **Shadow on medicine** | Dark patch over blister pack | Move lamp angle, retake |
| **Calibration card cut off** | Card edge outside frame | Move phone higher, retake |
| **Overexposure** | White patches blown out | Reduce lamp brightness, retake |
| **Underexposure** | Dark image, details lost | Increase lamp brightness, retake |
| **Night mode activated** | Soft, painted look | Disable night mode in camera settings |

**Rule: if in doubt, retake.** Storage is free. Bad photos corrupt the database.

---

## Section 10 — Where Photos Go

```
datasets/
└── verum/
    ├── samples/          ← ALL medicine photos go here
    │   ├── amox_LOT2024_fluorescent_authentic_001.jpg
    │   ├── amox_LOT2024_fluorescent_authentic_002.jpg
    │   └── ...
    ├── holdout/          ← 20% of photos kept aside for validate_db.py
    │   └── ...
    └── provenance/       ← pharmacy receipts + GMP certificates
        ├── amox_pharmacy_receipt.jpg
        └── amox_gmp_certificate.jpg
```

**holdout/** — before running `build_db.py`, move roughly 20% of your photos (pick randomly) into `datasets/verum/holdout/`. These are never used in training — only in `validate_db.py` to measure accuracy.

---

*HELIX VERUM Photography Protocol v1.0 | FAR AWAY by Zuup | May 2026*