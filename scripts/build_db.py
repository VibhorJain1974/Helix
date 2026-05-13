"""
build_db.py
HELIX — VERUM Database Lead (M3)
FAR AWAY by Zuup | May 2026

PURPOSE:
    MAIN SCRIPT. Reads all photos from datasets/verum/samples/,
    extracts 3 fingerprint vectors from each using process_verum.py,
    and writes the final database to apps/verum/public/db/

OUTPUT:
    apps/verum/public/db/manifest.json   — medicine list, schema, version info
    apps/verum/public/db/vectors.bin     — binary feature vectors (<40MB target)

USAGE:
    python scripts/build_db.py
    python scripts/build_db.py --input datasets/verum/samples/ --output apps/verum/public/db/
    python scripts/build_db.py --medicine amoxicillin  (build one medicine only)
"""

import os
import sys
import json
import struct
import argparse
import numpy as np
from datetime import datetime

# Add scripts/ to path so we can import process_verum
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from process_verum import extract_vectors, batch_extract


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# These are the 5 medicines in scope for VERUM v1
# (from HELIX Technical Architecture doc)
MEDICINES = [
    "amoxicillin",
    "artemether",
    "metformin",
    "paracetamol",
    "ors"
]

# Lighting conditions used during photography
LIGHTING_CONDITIONS = [
    "natural",
    "fluorescent",
    "led_warm",
    "led_cool",
    "low_light"
]

# Sample label keywords — these appear in the filename
AUTHENTIC_KEYWORD   = "authentic"
COUNTERFEIT_KEYWORD = "counterfeit"

# Database version
DB_VERSION = "1.0.0"

# Size warning threshold (bytes)
SIZE_WARNING_BYTES = 40 * 1024 * 1024  # 40MB


# ─────────────────────────────────────────────
# FILE PARSING
# ─────────────────────────────────────────────

def parse_filename(filename: str) -> dict:
    """
    Parses VERUM naming convention into metadata.

    Expected format:
        {medicine}_{lot}_{condition}_{label}_{shot}.jpg
        e.g. amox_LOT2024_fluorescent_authentic_001.jpg
             paracetamol_LOT2024_natural_counterfeit_002.jpg

    Returns dict with keys: medicine, lot, condition, label, shot
    label is 'authentic' or 'counterfeit'
    """
    name = os.path.splitext(filename)[0]  # strip .jpg
    parts = name.lower().split("_")

    medicine  = parts[0] if len(parts) > 0 else "unknown"
    lot       = parts[1] if len(parts) > 1 else "unknown"
    condition = parts[2] if len(parts) > 2 else "unknown"
    label     = parts[3] if len(parts) > 3 else "unknown"
    shot      = parts[4] if len(parts) > 4 else "000"

    # Normalise medicine name to match MEDICINES list
    for m in MEDICINES:
        if m[:4] in medicine:  # amox → amoxicillin
            medicine = m
            break

    return {
        "medicine":  medicine,
        "lot":       lot,
        "condition": condition,
        "label":     label,   # 'authentic' or 'counterfeit'
        "shot":      shot
    }


# ─────────────────────────────────────────────
# DATABASE BUILDER
# ─────────────────────────────────────────────

def build_database(input_dir: str, output_dir: str, calibration_card: str = None,
                   medicine_filter: str = None) -> bool:
    """
    Core function. Reads all photos → extracts vectors → writes database.

    Args:
        input_dir         : folder containing medicine photos
        output_dir        : where to write manifest.json + vectors.bin
        calibration_card  : path to calibration card image (optional)
        medicine_filter   : if set, only process this medicine name

    Returns:
        True if successful, False if failed
    """
    print("\n" + "=" * 60)
    print("  HELIX VERUM — Database Builder")
    print("=" * 60)
    print(f"  Input  : {input_dir}")
    print(f"  Output : {output_dir}")
    print(f"  Filter : {medicine_filter or 'all medicines'}")
    print("=" * 60 + "\n")

    # ── Validate input directory ──
    if not os.path.isdir(input_dir):
        print(f"[ERROR] Input directory not found: {input_dir}")
        print("        Have you added photos to datasets/verum/samples/ ?")
        return False

    # ── Create output directory if needed ──
    os.makedirs(output_dir, exist_ok=True)

    # ── Find all image files ──
    supported = ('.jpg', '.jpeg', '.png')
    all_files = [
        f for f in sorted(os.listdir(input_dir))
        if f.lower().endswith(supported) and not f.startswith('.')
    ]

    if not all_files:
        print(f"[ERROR] No images found in {input_dir}")
        print("        Add your medicine photos first (see photography_protocol.md)")
        return False

    # ── Apply medicine filter if set ──
    if medicine_filter:
        all_files = [f for f in all_files if medicine_filter.lower() in f.lower()]
        if not all_files:
            print(f"[ERROR] No images found for medicine: {medicine_filter}")
            return False

    print(f"[INFO] Found {len(all_files)} images to process\n")

    # ── Process each image ──
    records = []
    errors  = []

    for i, fname in enumerate(all_files):
        fpath  = os.path.join(input_dir, fname)
        meta   = parse_filename(fname)
        result = extract_vectors(fpath, calibration_card)

        status = "✓" if result['success'] else "✗"
        print(f"  [{i+1:>4}/{len(all_files)}] {status} {fname}")

        if result['success']:
            record = {
                "filename":         fname,
                "medicine":         meta['medicine'],
                "lot":              meta['lot'],
                "condition":        meta['condition'],
                "label":            meta['label'],      # authentic / counterfeit
                "shot":             meta['shot'],
                "colour_vector":    result['colour_vector'].tolist(),
                "geometry_vector":  result['geometry_vector'].tolist(),
                "frequency_vector": result['frequency_vector'].tolist()
            }
            records.append(record)
        else:
            errors.append({"filename": fname, "error": result['error']})
            print(f"              ↳ ERROR: {result['error']}")

    print(f"\n[INFO] Processed: {len(records)} success, {len(errors)} errors\n")

    if not records:
        print("[ERROR] No records were successfully processed. Cannot build database.")
        return False

    # ── Compute authentic means per medicine (used for ΔE76 comparison) ──
    authentic_means = _compute_authentic_means(records)

    # ── Write manifest.json ──
    manifest = _build_manifest(records, authentic_means, errors)
    manifest_path = os.path.join(output_dir, "manifest.json")

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest_size = os.path.getsize(manifest_path)
    print(f"[WRITE] manifest.json — {manifest_size / 1024:.1f} KB")

    # ── Write vectors.bin ──
    bin_path = os.path.join(output_dir, "vectors.bin")
    _write_binary(records, bin_path)

    bin_size = os.path.getsize(bin_path)
    print(f"[WRITE] vectors.bin   — {bin_size / (1024*1024):.2f} MB")

    # ── Size check ──
    total_size = manifest_size + bin_size
    print(f"\n[INFO] Total database size: {total_size / (1024*1024):.2f} MB")

    if total_size > SIZE_WARNING_BYTES:
        print(f"[WARN] ⚠️  Database exceeds 40MB target!")
        print(f"       Consider reducing sample count or compressing images.")
    else:
        print(f"[OK]   ✅ Within 40MB Service Worker cache budget")

    # ── Summary ──
    _print_summary(records, authentic_means)

    return True


# ─────────────────────────────────────────────
# AUTHENTIC MEANS COMPUTATION
# ─────────────────────────────────────────────

def _compute_authentic_means(records: list) -> dict:
    """
    Computes mean colour/geometry/frequency vectors for authentic samples
    per medicine. These become the reference that new scans are compared against.
    """
    means = {}

    for medicine in MEDICINES:
        auth_records = [
            r for r in records
            if r['medicine'] == medicine and r['label'] == AUTHENTIC_KEYWORD
        ]

        if not auth_records:
            continue

        colour_vecs    = np.array([r['colour_vector']    for r in auth_records])
        geometry_vecs  = np.array([r['geometry_vector']  for r in auth_records])
        frequency_vecs = np.array([r['frequency_vector'] for r in auth_records])

        means[medicine] = {
            "sample_count":       len(auth_records),
            "colour_mean":        np.mean(colour_vecs,    axis=0).tolist(),
            "colour_std":         np.std(colour_vecs,     axis=0).tolist(),
            "geometry_mean":      np.mean(geometry_vecs,  axis=0).tolist(),
            "geometry_std":       np.std(geometry_vecs,   axis=0).tolist(),
            "frequency_mean":     np.mean(frequency_vecs, axis=0).tolist(),
            "frequency_std":      np.std(frequency_vecs,  axis=0).tolist(),
        }

    return means


# ─────────────────────────────────────────────
# MANIFEST BUILDER
# ─────────────────────────────────────────────

def _build_manifest(records: list, authentic_means: dict, errors: list) -> dict:
    """
    Builds the manifest.json structure that the browser reads.
    This is what M2 (browser lead) uses to load the database.
    """
    medicines_present = list(set(r['medicine'] for r in records))

    manifest = {
        "version":          DB_VERSION,
        "built_at":         datetime.utcnow().isoformat() + "Z",
        "total_records":    len(records),
        "medicines":        medicines_present,
        "vector_schema": {
            "colour_vector":    {"dims": 3, "description": "CIE L*a*b* mean [L*, a*, b*]"},
            "geometry_vector":  {"dims": 3, "description": "[diameter_px, edge_sharpness, surface_uniformity]"},
            "frequency_vector": {"dims": 1, "description": "DCT band energy (8-24 cycles/mm, normalised)"}
        },
        "verdict_thresholds": {
            "colour_delta_e_suspect":      2.0,
            "colour_delta_e_counterfeit":  4.0,
            "geometry_sigma_suspect":      2.0,
            "frequency_sigma_suspect":     2.0,
            "two_vectors_flag":            "COUNTERFEIT"
        },
        "authentic_means":  authentic_means,
        "errors":           errors,
        "binary_file":      "vectors.bin"
    }

    return manifest


# ─────────────────────────────────────────────
# BINARY WRITER
# ─────────────────────────────────────────────

def _write_binary(records: list, output_path: str):
    """
    Writes all feature vectors to a compact binary file.

    Binary format per record (7 float32 values = 28 bytes):
        [L*, a*, b*, diam, edge, surf, freq]
        + 1 byte label (0=authentic, 1=counterfeit, 2=unknown)
        + 1 byte medicine index (0-4)
    Total: 30 bytes per record

    This format is what the browser-side ONNX model reads.
    """
    medicine_index = {m: i for i, m in enumerate(MEDICINES)}

    with open(output_path, 'wb') as f:
        # Header: number of records (4 bytes)
        f.write(struct.pack('<I', len(records)))

        for record in records:
            # 7 float32 values
            colour    = record['colour_vector']      # [L*, a*, b*]
            geometry  = record['geometry_vector']    # [diam, edge, surf]
            frequency = record['frequency_vector']   # [freq]

            floats = colour + geometry + frequency
            f.write(struct.pack('<7f', *floats))

            # Label byte
            label_map = {AUTHENTIC_KEYWORD: 0, COUNTERFEIT_KEYWORD: 1}
            label_byte = label_map.get(record['label'], 2)
            f.write(struct.pack('<B', label_byte))

            # Medicine index byte
            med_byte = medicine_index.get(record['medicine'], 255)
            f.write(struct.pack('<B', med_byte))


# ─────────────────────────────────────────────
# SUMMARY PRINTER
# ─────────────────────────────────────────────

def _print_summary(records: list, authentic_means: dict):
    print("\n" + "─" * 60)
    print("  DATABASE SUMMARY")
    print("─" * 60)

    for medicine in MEDICINES:
        auth  = [r for r in records if r['medicine'] == medicine and r['label'] == AUTHENTIC_KEYWORD]
        fake  = [r for r in records if r['medicine'] == medicine and r['label'] == COUNTERFEIT_KEYWORD]
        total = [r for r in records if r['medicine'] == medicine]

        if not total:
            print(f"  {medicine:<20} — no data yet")
            continue

        print(f"  {medicine:<20} authentic={len(auth):>3}  counterfeit={len(fake):>3}")

        if medicine in authentic_means:
            mean = authentic_means[medicine]
            lab  = mean['colour_mean']
            print(f"    └─ colour mean L*={lab[0]:.1f} a*={lab[1]:.1f} b*={lab[2]:.1f}  (n={mean['sample_count']})")

    print("─" * 60)
    print(f"  Total records: {len(records)}")
    print("─" * 60 + "\n")


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HELIX VERUM — Build fingerprint database from medicine photos"
    )
    parser.add_argument(
        "--input",
        default="datasets/verum/samples",
        help="Directory containing medicine photos (default: datasets/verum/samples)"
    )
    parser.add_argument(
        "--output",
        default="apps/verum/public/db",
        help="Output directory for manifest.json + vectors.bin (default: apps/verum/public/db)"
    )
    parser.add_argument(
        "--calibration",
        default=None,
        help="Path to calibration card photo for white balance normalisation"
    )
    parser.add_argument(
        "--medicine",
        default=None,
        help="Build database for one medicine only (e.g. --medicine amoxicillin)"
    )

    args = parser.parse_args()

    success = build_database(
        input_dir         = args.input,
        output_dir        = args.output,
        calibration_card  = args.calibration,
        medicine_filter   = args.medicine
    )

    sys.exit(0 if success else 1)