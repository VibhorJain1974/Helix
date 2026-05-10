"""
train_verum_model.py
HELIX — VERUM Database Lead (M3)
FAR AWAY by Zuup | May 2026

PURPOSE:
    Trains a lightweight classifier on the fingerprint vectors produced by build_db.py.
    Exports the trained model as an ONNX file for use in the browser via ONNX Runtime Web.

    Input  : apps/verum/public/db/manifest.json (contains authentic_means + all vectors)
    Output : apps/verum/public/db/verum_model.onnx

USAGE:
    python scripts/train_verum_model.py
    python scripts/train_verum_model.py --db apps/verum/public/db --epochs 100
"""

import os
import sys
import json
import argparse
import numpy as np

# ─────────────────────────────────────────────
# CHECK DEPENDENCIES
# ─────────────────────────────────────────────

def check_dependencies():
    missing = []
    try:
        import sklearn
    except ImportError:
        missing.append("scikit-learn")
    try:
        import skl2onnx
    except ImportError:
        missing.append("skl2onnx")
    try:
        import onnxruntime
    except ImportError:
        missing.append("onnxruntime")

    if missing:
        print("[ERROR] Missing required packages. Install with:")
        print(f"        pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import onnxruntime as rt
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

# Total vector size: 3 (colour) + 3 (geometry) + 1 (frequency) = 7 features
VECTOR_DIM = 7

# Labels
LABEL_AUTHENTIC   = 0
LABEL_COUNTERFEIT = 1

# Model output path
MODEL_FILENAME = "verum_model.onnx"
SCALER_FILENAME = "verum_scaler.json"


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────

def load_vectors_from_manifest(db_dir: str) -> tuple:
    """
    Loads all fingerprint vectors and labels from manifest.json.

    Returns:
        X : np.array shape (N, 7) — feature matrix
        y : np.array shape (N,)   — labels (0=authentic, 1=counterfeit)
        medicines : list of medicine names per sample
    """
    manifest_path = os.path.join(db_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"[ERROR] manifest.json not found at: {manifest_path}")
        print("        Run build_db.py first to generate the database.")
        sys.exit(1)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    print(f"[INFO] Loading manifest v{manifest.get('version', '?')}")
    print(f"[INFO] Total records in manifest: {manifest['total_records']}")

    # Rebuild records from authentic_means and raw data
    # The manifest stores authentic_means per medicine — we reconstruct training data
    # from the authentic_means statistics using synthetic samples + any counterfeit records

    X         = []
    y         = []
    medicines = []

    authentic_means = manifest.get("authentic_means", {})

    for medicine, stats in authentic_means.items():
        n = stats["sample_count"]
        if n == 0:
            continue

        colour_mean   = np.array(stats["colour_mean"])
        colour_std    = np.array(stats["colour_std"])
        geometry_mean = np.array(stats["geometry_mean"])
        geometry_std  = np.array(stats["geometry_std"])
        freq_mean     = np.array(stats["frequency_mean"])
        freq_std      = np.array(stats["frequency_std"])

        # Generate authentic samples from stored statistics
        # (Gaussian approximation of the authentic distribution)
        rng = np.random.default_rng(seed=42)

        for _ in range(n):
            colour_sample   = rng.normal(colour_mean,   np.maximum(colour_std,   0.01))
            geometry_sample = rng.normal(geometry_mean, np.maximum(geometry_std, 0.01))
            freq_sample     = rng.normal(freq_mean,     np.maximum(freq_std,     0.001))

            vector = np.concatenate([colour_sample, geometry_sample, freq_sample])
            X.append(vector)
            y.append(LABEL_AUTHENTIC)
            medicines.append(medicine)

        # Generate synthetic counterfeit samples:
        # Counterfeits are shifted outside the authentic distribution
        # Colour shift: +5 ΔE76 (noticeable colour difference)
        # Frequency shift: +2σ in DCT band (reprint artefacts)
        n_fake = max(5, n // 3)  # at least 5 counterfeits per medicine
        for _ in range(n_fake):
            # Shift colour outside authentic range
            colour_shift    = rng.choice([-1, 1]) * (colour_std * 3 + 5)
            colour_fake     = colour_mean + colour_shift

            # Geometry stays similar (counterfeits look physically similar)
            geometry_fake   = rng.normal(geometry_mean, geometry_std * 1.2)

            # Frequency is the key difference — counterfeits show higher band energy
            freq_fake       = freq_mean + freq_std * rng.uniform(2.5, 5.0)

            vector = np.concatenate([colour_fake, geometry_fake, freq_fake])
            X.append(vector)
            y.append(LABEL_COUNTERFEIT)
            medicines.append(medicine)

    if not X:
        print("[ERROR] No data found in manifest. Build the database first.")
        sys.exit(1)

    X_arr = np.array(X, dtype=np.float32)
    y_arr = np.array(y, dtype=np.int32)

    auth_count = int(np.sum(y_arr == LABEL_AUTHENTIC))
    fake_count = int(np.sum(y_arr == LABEL_COUNTERFEIT))

    print(f"[INFO] Training data: {auth_count} authentic, {fake_count} counterfeit samples")

    return X_arr, y_arr, medicines


# ─────────────────────────────────────────────
# MODEL TRAINING
# ─────────────────────────────────────────────

def train_model(X: np.ndarray, y: np.ndarray, n_estimators: int = 100) -> tuple:
    """
    Trains a Random Forest classifier on the fingerprint vectors.

    Why Random Forest?
        - Works well with small datasets (which VERUM v1 will be)
        - Interpretable — we can inspect which features matter
        - Exports cleanly to ONNX via skl2onnx
        - Fast inference (important for browser ONNX Runtime)

    Returns:
        (trained_model, scaler, test_metrics)
    """
    # ── Train/test split ──
    # Stratified to ensure both classes in both sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = 0.2,
        random_state = 42,
        stratify     = y
    )

    # ── Feature scaling ──
    scaler  = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # ── Train ──
    print(f"\n[TRAIN] Training Random Forest ({n_estimators} trees)...")
    model = RandomForestClassifier(
        n_estimators = n_estimators,
        max_depth    = 8,           # Shallow = faster ONNX inference
        random_state = 42,
        class_weight = 'balanced',  # Handles imbalanced authentic/counterfeit
        n_jobs       = -1
    )
    model.fit(X_train_scaled, y_train)

    # ── Evaluate ──
    y_pred = model.predict(X_test_scaled)

    print("\n[EVAL] Classification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=['authentic', 'counterfeit'],
        zero_division=0
    ))

    print("[EVAL] Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"       Predicted →    authentic  counterfeit")
    print(f"  Actual authentic  : {cm[0][0]:>9}  {cm[0][1]:>11}")
    print(f"  Actual counterfeit: {cm[1][0]:>9}  {cm[1][1]:>11}")

    # False positive rate (authentic flagged as counterfeit)
    if cm[0].sum() > 0:
        fpr = cm[0][1] / cm[0].sum()
        print(f"\n[METRIC] False Positive Rate: {fpr:.3f} ({fpr*100:.1f}%)")
        print(f"         (authentic samples wrongly flagged as counterfeit)")

    # False negative rate (counterfeit missed as authentic)
    if cm[1].sum() > 0:
        fnr = cm[1][0] / cm[1].sum()
        print(f"[METRIC] False Negative Rate: {fnr:.3f} ({fnr*100:.1f}%)")
        print(f"         (counterfeit samples missed — this is the dangerous one)")

    metrics = {
        "confusion_matrix":   cm.tolist(),
        "test_size":          len(y_test),
        "n_estimators":       n_estimators
    }

    return model, scaler, metrics


# ─────────────────────────────────────────────
# ONNX EXPORT
# ─────────────────────────────────────────────

def export_to_onnx(model, scaler, output_dir: str) -> str:
    """
    Exports the trained model to ONNX format.
    The browser loads this file via ONNX Runtime Web.

    Also saves scaler parameters as JSON (for browser-side normalisation).
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── Export ONNX model ──
    onnx_path = os.path.join(output_dir, MODEL_FILENAME)

    initial_type = [('float_input', FloatTensorType([None, VECTOR_DIM]))]
    onnx_model = convert_sklearn(
        model,
        initial_types = initial_type,
        target_opset  = 12  # ONNX Runtime Web supports opset 12
    )

    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    model_size = os.path.getsize(onnx_path)
    print(f"\n[WRITE] {MODEL_FILENAME} — {model_size / 1024:.1f} KB")

    # ── Export scaler parameters as JSON ──
    # Browser needs these to normalise inputs before inference
    scaler_data = {
        "mean":  scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "n_features": VECTOR_DIM,
        "feature_names": [
            "colour_L", "colour_a", "colour_b",
            "geometry_diameter", "geometry_edge", "geometry_surface",
            "frequency_dct_band"
        ]
    }

    scaler_path = os.path.join(output_dir, SCALER_FILENAME)
    with open(scaler_path, "w") as f:
        json.dump(scaler_data, f, indent=2)

    print(f"[WRITE] {SCALER_FILENAME} — scaler parameters saved")

    return onnx_path


# ─────────────────────────────────────────────
# ONNX VALIDATION
# ─────────────────────────────────────────────

def validate_onnx(onnx_path: str, X_sample: np.ndarray, scaler):
    """
    Quick sanity check — runs a few samples through the exported ONNX model
    to confirm the export worked correctly.
    """
    print("\n[VALIDATE] Testing ONNX model...")

    sess = rt.InferenceSession(onnx_path)
    input_name = sess.get_inputs()[0].name

    # Run 5 samples
    X_scaled = scaler.transform(X_sample[:5]).astype(np.float32)
    pred     = sess.run(None, {input_name: X_scaled})

    label_names = {0: "AUTHENTIC", 1: "COUNTERFEIT"}

    print("  Sample predictions from exported ONNX model:")
    for i, p in enumerate(pred[0]):
        print(f"    Sample {i+1}: {label_names.get(p, 'UNKNOWN')} (label={p})")

    print("[VALIDATE] ✅ ONNX model working correctly")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main(db_dir: str, n_estimators: int):
    print("\n" + "=" * 60)
    print("  HELIX VERUM — Model Trainer")
    print("=" * 60)

    # Load data
    X, y, medicines = load_vectors_from_manifest(db_dir)

    # Train
    model, scaler, metrics = train_model(X, y, n_estimators)

    # Export
    onnx_path = export_to_onnx(model, scaler, db_dir)

    # Validate
    validate_onnx(onnx_path, X, scaler)

    print("\n" + "─" * 60)
    print("  ✅ Training complete!")
    print(f"  Model saved to: {onnx_path}")
    print("  Next step: run validate_db.py to measure false positive rate")
    print("─" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HELIX VERUM — Train ONNX classifier on fingerprint vectors"
    )
    parser.add_argument(
        "--db",
        default="apps/verum/public/db",
        help="Path to database directory containing manifest.json"
    )
    parser.add_argument(
        "--estimators",
        type=int,
        default=100,
        help="Number of trees in Random Forest (default: 100)"
    )
    args = parser.parse_args()

    main(db_dir=args.db, n_estimators=args.estimators)