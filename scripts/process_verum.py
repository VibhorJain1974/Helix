"""
process_verum.py
HELIX — VERUM Database Lead (M3)
FAR AWAY by Zuup | May 2026

PURPOSE:
    Extracts 3 independent fingerprint vectors from a medicine blister pack photo.
    These 3 vectors are what VERUM uses to decide AUTHENTIC / SUSPECT / COUNTERFEIT.

THE 3 VECTORS:
    Vector 1 — Colour     : CIE L*a*b* colour deviation (ΔE76) from authentic mean
    Vector 2 — Geometry   : Pill diameter, scoring line depth, edge curvature
    Vector 3 — Print Freq : DCT frequency analysis (8-24 cycles/mm band)

USAGE:
    from process_verum import extract_vectors
    vectors = extract_vectors("amox_LOT2024_fluorescent_001.jpg", calibration_card_path="card.jpg")
"""

import numpy as np
from skimage import io, color, filters, measure, transform
from skimage.util import img_as_float
from scipy.fft import dct
import warnings
import os

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

# DCT frequency band of interest (cycles per mm)
# Counterfeits show artefacts here — invisible to eye, detectable by camera
DCT_BAND_LOW  = 8    # cycles/mm
DCT_BAND_HIGH = 24   # cycles/mm

# Camera resolution assumption for frequency scaling
# Adjust if using a different device
MM_PER_PIXEL = 0.05  # ~20 pixels per mm for a typical phone macro shot

# How many pixels to crop from edges (removes calibration card border noise)
CROP_MARGIN = 20

# Target size for geometry analysis
GEOMETRY_RESIZE = (512, 512)


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

def extract_vectors(image_path: str, calibration_card_path: str = None) -> dict:
    """
    Main entry point. Takes one photo, returns all 3 fingerprint vectors.

    Args:
        image_path         : Path to the blister pack photo (.jpg)
        calibration_card_path : Path to calibration card photo for white balance.
                               If None, skips white balance normalisation.

    Returns:
        dict with keys:
            'colour_vector'    : np.array shape (3,)  — L*, a*, b* mean values
            'geometry_vector'  : np.array shape (3,)  — [diameter_mm, line_depth, edge_radius]
            'frequency_vector' : np.array shape (1,)  — DCT band energy
            'image_path'       : original file path (for tracing)
            'success'          : bool — False if image could not be processed
            'error'            : str or None
    """
    result = {
        'colour_vector':    None,
        'geometry_vector':  None,
        'frequency_vector': None,
        'image_path':       image_path,
        'success':          False,
        'error':            None
    }

    try:
        # ── Load image ──
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        img_rgb = img_as_float(io.imread(image_path))

        # Handle RGBA (some phones save PNG with alpha)
        if img_rgb.ndim == 3 and img_rgb.shape[2] == 4:
            img_rgb = img_rgb[:, :, :3]

        # ── White balance from calibration card ──
        if calibration_card_path and os.path.exists(calibration_card_path):
            img_rgb = _white_balance(img_rgb, calibration_card_path)

        # ── Crop edges ──
        img_rgb = img_rgb[CROP_MARGIN:-CROP_MARGIN, CROP_MARGIN:-CROP_MARGIN]

        # ── Extract 3 vectors ──
        result['colour_vector']    = _extract_colour_vector(img_rgb)
        result['geometry_vector']  = _extract_geometry_vector(img_rgb)
        result['frequency_vector'] = _extract_frequency_vector(img_rgb)
        result['success']          = True

    except Exception as e:
        result['error'] = str(e)

    return result


# ─────────────────────────────────────────────
# VECTOR 1 — COLOUR (CIE L*a*b*)
# ─────────────────────────────────────────────

def _extract_colour_vector(img_rgb: np.ndarray) -> np.ndarray:
    """
    Converts image to CIE L*a*b* colour space.
    Returns mean [L*, a*, b*] across the centre region of the image.

    Why L*a*b*?
        L*a*b* is perceptually uniform — a ΔE76 of 1.0 means one just-noticeable
        colour difference. Counterfeits typically show ΔE76 > 3.0 from authentic mean.
    """
    # Convert sRGB → CIE L*a*b*
    img_lab = color.rgb2lab(img_rgb)

    # Use centre 60% of image — avoids calibration card edges
    h, w = img_lab.shape[:2]
    cy, cx = h // 2, w // 2
    margin_y, margin_x = h // 5, w // 5

    centre_region = img_lab[
        cy - margin_y : cy + margin_y,
        cx - margin_x : cx + margin_x
    ]

    # Mean L*, a*, b* across the centre region
    colour_vector = np.mean(centre_region.reshape(-1, 3), axis=0)

    return colour_vector.astype(np.float32)


def compute_delta_e76(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Computes ΔE76 (Euclidean distance in L*a*b* space) between two colour vectors.
    ΔE76 > 2.0  → noticeable difference
    ΔE76 > 4.0  → likely counterfeit colour deviation
    """
    return float(np.linalg.norm(vec_a - vec_b))


# ─────────────────────────────────────────────
# VECTOR 2 — GEOMETRY
# ─────────────────────────────────────────────

def _extract_geometry_vector(img_rgb: np.ndarray) -> np.ndarray:
    """
    Extracts geometric features from pill/blister pack:
        [0] estimated_diameter_px  : pill or blister pocket diameter in pixels
        [1] edge_sharpness         : mean gradient magnitude at detected edges
        [2] surface_uniformity     : std deviation of greyscale within pill region

    Note: Full geometry (0° vs 30° tilt comparison) requires TWO images.
          This function handles the single-image pass.
          Use compare_geometry_tilt() for the two-image comparison.
    """
    # Resize for consistent geometry measurements
    img_resized = transform.resize(img_rgb, GEOMETRY_RESIZE, anti_aliasing=True)

    # Convert to greyscale
    img_grey = color.rgb2gray(img_resized)

    # Edge detection
    edges = filters.sobel(img_grey)

    # Threshold to find pill/blister regions
    threshold = filters.threshold_otsu(img_grey)
    binary_mask = img_grey > threshold

    # Measure labelled regions
    labelled = measure.label(binary_mask)
    regions = measure.regionprops(labelled)

    if not regions:
        # Fallback: return zeros if no regions found
        return np.zeros(3, dtype=np.float32)

    # Largest region = pill pocket
    largest = max(regions, key=lambda r: r.area)

    estimated_diameter_px = float(largest.equivalent_diameter)
    edge_sharpness        = float(np.mean(edges[binary_mask]))
    surface_uniformity    = float(np.std(img_grey[binary_mask]))

    geometry_vector = np.array([
        estimated_diameter_px,
        edge_sharpness,
        surface_uniformity
    ], dtype=np.float32)

    return geometry_vector


def compare_geometry_tilt(img_0deg_path: str, img_30deg_path: str) -> np.ndarray:
    """
    Compares two images taken at 0° and 30° tilt.
    Shadow differential reveals scoring line depth and edge curvature.

    This is the full Vector 2 as described in the architecture doc.

    Args:
        img_0deg_path  : path to flat (0°) photo
        img_30deg_path : path to tilted (30°) photo

    Returns:
        np.array shape (3,) — [shadow_differential, diameter_consistency, tilt_edge_delta]
    """
    img_0   = img_as_float(io.imread(img_0deg_path))
    img_30  = img_as_float(io.imread(img_30deg_path))

    if img_0.shape[2] == 4:
        img_0 = img_0[:, :, :3]
    if img_30.shape[2] == 4:
        img_30 = img_30[:, :, :3]

    grey_0  = color.rgb2gray(img_0)
    grey_30 = color.rgb2gray(img_30)

    # Resize to same dimensions
    grey_30_resized = transform.resize(grey_30, grey_0.shape, anti_aliasing=True)

    # Shadow differential — deeper scoring lines = larger shadow at 30°
    shadow_diff = float(np.mean(np.abs(grey_0 - grey_30_resized)))

    # Edge maps for both
    edges_0  = filters.sobel(grey_0)
    edges_30 = filters.sobel(grey_30_resized)

    diameter_consistency = float(np.mean(np.abs(edges_0 - edges_30)))
    tilt_edge_delta      = float(np.std(edges_30 - edges_0))

    return np.array([shadow_diff, diameter_consistency, tilt_edge_delta], dtype=np.float32)


# ─────────────────────────────────────────────
# VECTOR 3 — PRINT FREQUENCY (DCT)
# ─────────────────────────────────────────────

def _extract_frequency_vector(img_rgb: np.ndarray) -> np.ndarray:
    """
    Analyses the blister pack surface print using Discrete Cosine Transform (DCT).

    Why DCT?
        Legitimate blister packs are printed by high-precision pharmaceutical printers.
        Counterfeits are often photocopied or digitally reprinted — this introduces
        lossy-reprint artefacts in the 8-24 cycles/mm band. Invisible to the eye.
        Very visible in the frequency domain.

    Returns:
        np.array shape (1,) — energy in the 8-24 cycles/mm band (normalised)
    """
    # Convert to greyscale and crop centre patch for surface analysis
    img_grey = color.rgb2gray(img_rgb)

    h, w = img_grey.shape
    patch_size = min(h, w) // 2
    cy, cx = h // 2, w // 2

    patch = img_grey[
        cy - patch_size//2 : cy + patch_size//2,
        cx - patch_size//2 : cx + patch_size//2
    ]

    # 2D DCT
    dct_2d = dct(dct(patch, axis=0, norm='ortho'), axis=1, norm='ortho')
    dct_power = np.abs(dct_2d) ** 2

    # Convert frequency indices to cycles/mm
    # freq_cycles_per_mm = index / (patch_size * MM_PER_PIXEL)
    freq_resolution = 1.0 / (patch_size * MM_PER_PIXEL)  # cycles/mm per index

    low_idx  = int(DCT_BAND_LOW  / freq_resolution)
    high_idx = int(DCT_BAND_HIGH / freq_resolution)

    # Clamp to valid range
    low_idx  = max(1, min(low_idx,  patch_size - 1))
    high_idx = max(2, min(high_idx, patch_size - 1))

    # Energy in the band of interest
    band_energy = np.sum(dct_power[low_idx:high_idx, low_idx:high_idx])

    # Normalise by total energy
    total_energy = np.sum(dct_power) + 1e-8
    normalised_band_energy = float(band_energy / total_energy)

    return np.array([normalised_band_energy], dtype=np.float32)


# ─────────────────────────────────────────────
# WHITE BALANCE UTILITY
# ─────────────────────────────────────────────

def _white_balance(img_rgb: np.ndarray, card_path: str) -> np.ndarray:
    """
    Normalises image white balance using the calibration card's white patch.

    The calibration card has an 18% grey patch and a white patch.
    We find the brightest region (white patch) and normalise channels to it.
    This removes colour casts from different lighting conditions.
    """
    card_img = img_as_float(io.imread(card_path))

    if card_img.ndim == 3 and card_img.shape[2] == 4:
        card_img = card_img[:, :, :3]

    # Find white patch: top 1% brightest pixels per channel
    white_refs = []
    for ch in range(3):
        channel = card_img[:, :, ch].flatten()
        white_refs.append(np.percentile(channel, 99))

    white_refs = np.array(white_refs)

    # Normalise: scale each channel so white patch = 1.0
    if np.all(white_refs > 0.01):
        img_normalised = img_rgb / white_refs
        img_normalised = np.clip(img_normalised, 0.0, 1.0)
        return img_normalised

    # If card is too dark to use, return original
    return img_rgb


# ─────────────────────────────────────────────
# BATCH PROCESSING HELPER
# ─────────────────────────────────────────────

def batch_extract(image_dir: str, calibration_card_path: str = None) -> list:
    """
    Processes all .jpg / .jpeg / .png files in a directory.

    Args:
        image_dir             : folder containing medicine photos
        calibration_card_path : calibration card image path (optional)

    Returns:
        list of result dicts (one per image)
    """
    supported = ('.jpg', '.jpeg', '.png')
    results = []

    files = [
        f for f in sorted(os.listdir(image_dir))
        if f.lower().endswith(supported)
    ]

    if not files:
        print(f"[WARN] No images found in {image_dir}")
        return results

    print(f"[INFO] Processing {len(files)} images from {image_dir}")

    for i, fname in enumerate(files):
        fpath = os.path.join(image_dir, fname)
        result = extract_vectors(fpath, calibration_card_path)

        status = "✓" if result['success'] else "✗"
        print(f"  [{i+1}/{len(files)}] {status} {fname}")

        if not result['success']:
            print(f"       ERROR: {result['error']}")

        results.append(result)

    success_count = sum(1 for r in results if r['success'])
    print(f"\n[DONE] {success_count}/{len(files)} images processed successfully.")

    return results


# ─────────────────────────────────────────────
# QUICK TEST — run this file directly to verify
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=" * 55)
    print("  process_verum.py — HELIX VERUM Vector Extractor")
    print("=" * 55)

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python process_verum.py <image_path> [calibration_card_path]")
        print("\nExample:")
        print("  python process_verum.py datasets/verum/samples/amox_LOT2024_fluorescent_001.jpg")
        sys.exit(0)

    img_path  = sys.argv[1]
    card_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\nImage     : {img_path}")
    print(f"Calib card: {card_path or 'None (skipping white balance)'}")
    print()

    result = extract_vectors(img_path, card_path)

    if result['success']:
        print("✅ Extraction successful\n")
        print(f"  Vector 1 — Colour (L*, a*, b*) : {result['colour_vector']}")
        print(f"  Vector 2 — Geometry            : {result['geometry_vector']}")
        print(f"  Vector 3 — Print Frequency     : {result['frequency_vector']}")
    else:
        print(f"❌ Extraction failed: {result['error']}")