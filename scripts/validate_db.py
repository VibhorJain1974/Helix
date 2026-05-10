"""
validate_db.py
HELIX — VERUM Database Lead (M3)
FAR AWAY by Zuup | May 2026

PURPOSE:
    Measures the false positive and false negative rates of the VERUM model
    on a holdout set of medicine photos NOT used in training.

    This is the Week 3 deliverable:
    "False positive rate measured on holdout set" — HELIX Build Plan

    A false positive = authentic medicine wrongly flagged as SUSPECT/COUNTERFEIT
    A false negative = counterfeit medicine missed (marked AUTHENTIC) ← dangerous

USAGE:
    python scripts/validate_db.py
    python scripts/validate_db.py --holdout datasets/verum/holdout/ --db apps/verum/public/db
"""

import os
import sys
import json
import argparse
import numpy as np

# Add scripts/ to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from process_verum import extract_vectors


# ─────────────────────────────────────────────
# CHECK DEPENDENCIES
# ─────────────────────────────────────────────

def check_dependencies():
    missing = []
    try:
        import onnxruntime
    except ImportError:
        missing.append("onnxruntime")
    if missing:
        print("[ERROR] Missing packages. Install with:")
        print(f"        pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()
import onnxruntime as rt


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

MODEL_FILENAME  = "verum_model.onnx"
SCALER_FILENAME = "verum_scaler.json"

LABEL_AUTHENTIC   = 0
LABEL_COUNTERFEIT = 1

AUTHENTIC_KEYWORD   = "authentic"
COUNTERFEIT_KEYWORD = "counterfeit"


# ─────────────────────────────────────────────
# LOAD ONNX MODEL + SCALER
# ─────────────────────────────────────────────

def load_model_and_scaler(db_dir: str):
    model_path  = os.path.join(db_dir, MODEL_FILENAME)
    scaler_path = os.path.join(db_dir, SCALER_FILENAME)

    if not os.path.exists(model_path):
        print(f"[ERROR] Model not found: {model_path}")
        print("        Run train_verum_model.py first.")
        sys.exit(1)

    if not os.path.exists(scaler_path):
        print(f"[ERROR] Scaler not found: {scaler_path}")
        print("        Run train_verum_model.py first.")
        sys.exit(1)

    sess = rt.InferenceSession(model_path)

    with open(scaler_path, "r") as f:
        scaler_data = json.load(f)

    scaler_mean  = np.array(scaler_data["mean"],  dtype=np.float32)
    scaler_scale = np.array(scaler_data["scale"], dtype=np.float32)

    print(f"[INFO] Model loaded: {model_path}")

    return sess, scaler_mean, scaler_scale


# ─────────────────────────────────────────────
# INFERENCE ON ONE IMAGE
# ─────────────────────────────────────────────

def predict_image(image_path: str, sess, scaler_mean, scaler_scale,
                  calibration_card: str = None) -> dict:
    """
    Runs one image through the full pipeline:
        photo → extract_vectors → normalise → ONNX inference → verdict

    Returns dict with prediction, confidence, and raw vectors.
    """
    result = extract_vectors(image_path, calibration_card)

    if not result['success']:
        return {
            "image_path":  image_path,
            "success":     False,
            "error":       result['error'],
            "prediction":  None,
            "confidence":  None
        }

    # Concatenate all vectors into one feature array
    feature_vec = np.concatenate([
        result['colour_vector'],
        result['geometry_vector'],
        result['frequency_vector']
    ]).astype(np.float32)

    # Apply scaler normalisation (same as training)
    feature_scaled = (feature_vec - scaler_mean) / (scaler_scale + 1e-8)
    feature_input  = feature_scaled.reshape(1, -1)

    # ONNX inference
    input_name = sess.get_inputs()[0].name
    outputs    = sess.run(None, {input_name: feature_input})

    prediction   = int(outputs[0][0])
    # Probability output (index 1) gives confidence
    if len(outputs) > 1 and outputs[1] is not None:
        proba      = outputs[1][0]
        confidence = float(max(proba))
    else:
        confidence = 1.0

    label_names = {LABEL_AUTHENTIC: "AUTHENTIC", LABEL_COUNTERFEIT: "COUNTERFEIT"}

    return {
        "image_path":       image_path,
        "success":          True,
        "prediction":       prediction,
        "prediction_label": label_names.get(prediction, "UNKNOWN"),
        "confidence":       confidence,
        "colour_vector":    result['colour_vector'].tolist(),
        "geometry_vector":  result['geometry_vector'].tolist(),
        "frequency_vector": result['frequency_vector'].tolist(),
        "error":            None
    }


# ─────────────────────────────────────────────
# BATCH VALIDATION
# ─────────────────────────────────────────────

def validate_holdout(holdout_dir: str, db_dir: str, calibration_card: str = None):
    """
    Runs all images in holdout_dir through the model.
    Computes false positive rate, false negative rate, and overall accuracy.

    Filenames must contain 'authentic' or 'counterfeit' to determine true label.
    """
    print("\n" + "=" * 60)
    print("  HELIX VERUM — Holdout Validation")
    print("=" * 60)

    # ── Load model ──
    sess, scaler_mean, scaler_scale = load_model_and_scaler(db_dir)

    # ── Find holdout images ──
    if not os.path.isdir(holdout_dir):
        print(f"[ERROR] Holdout directory not found: {holdout_dir}")
        print("        Create datasets/verum/holdout/ and add test photos.")
        print("\n[TIP]   If you don't have a holdout set yet, this is normal for Week 1-2.")
        print("        You need at least 10 authentic + 5 counterfeit samples per medicine.")
        sys.exit(1)

    supported = ('.jpg', '.jpeg', '.png')
    files = [
        f for f in sorted(os.listdir(holdout_dir))
        if f.lower().endswith(supported)
    ]

    if not files:
        print(f"[ERROR] No images in holdout directory: {holdout_dir}")
        sys.exit(1)

    print(f"[INFO] Validating {len(files)} holdout images\n")

    # ── Run predictions ──
    results       = []
    true_positives  = 0  # counterfeit correctly identified
    true_negatives  = 0  # authentic correctly identified
    false_positives = 0  # authentic wrongly flagged as counterfeit
    false_negatives = 0  # counterfeit wrongly passed as authentic
    errors          = 0

    for i, fname in enumerate(files):
        fpath = os.path.join(holdout_dir, fname)

        # Determine true label from filename
        fname_lower = fname.lower()
        if AUTHENTIC_KEYWORD in fname_lower:
            true_label = LABEL_AUTHENTIC
        elif COUNTERFEIT_KEYWORD in fname_lower:
            true_label = LABEL_COUNTERFEIT
        else:
            print(f"  [SKIP] {fname} — cannot determine true label from filename")
            print(f"         (filename must contain 'authentic' or 'counterfeit')")
            continue

        # Run prediction
        pred = predict_image(fpath, sess, scaler_mean, scaler_scale, calibration_card)

        if not pred['success']:
            print(f"  [ERR ] {fname} — {pred['error']}")
            errors += 1
            continue

        # Compare prediction to true label
        correct    = pred['prediction'] == true_label
        true_name  = "authentic"   if true_label == LABEL_AUTHENTIC   else "counterfeit"
        pred_name  = pred['prediction_label'].lower()
        status     = "✓" if correct else "✗"
        conf_str   = f"{pred['confidence']*100:.0f}%"

        print(f"  [{i+1:>4}] {status} {fname:<45} true={true_name:<12} pred={pred_name:<12} conf={conf_str}")

        # Tally
        if true_label == LABEL_AUTHENTIC and pred['prediction'] == LABEL_AUTHENTIC:
            true_negatives  += 1
        elif true_label == LABEL_COUNTERFEIT and pred['prediction'] == LABEL_COUNTERFEIT:
            true_positives  += 1
        elif true_label == LABEL_AUTHENTIC and pred['prediction'] == LABEL_COUNTERFEIT:
            false_positives += 1  # ← bad: authentic flagged as counterfeit
        elif true_label == LABEL_COUNTERFEIT and pred['prediction'] == LABEL_AUTHENTIC:
            false_negatives += 1  # ← dangerous: counterfeit missed

        results.append({
            "filename":     fname,
            "true_label":   true_name,
            "prediction":   pred_name,
            "correct":      correct,
            "confidence":   pred['confidence']
        })

    # ── Compute metrics ──
    _print_metrics(true_positives, true_negatives, false_positives, false_negatives, errors, len(files))

    # ── Save results ──
    results_path = os.path.join(db_dir, "validation_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "true_positives":  true_positives,
            "true_negatives":  true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "errors":          errors,
            "results":         results
        }, f, indent=2)

    print(f"\n[WRITE] Validation results saved to: {results_path}")


# ─────────────────────────────────────────────
# METRICS PRINTER
# ─────────────────────────────────────────────

def _print_metrics(tp, tn, fp, fn, errors, total):
    print("\n" + "─" * 60)
    print("  VALIDATION RESULTS")
    print("─" * 60)

    total_valid = tp + tn + fp + fn
    if total_valid == 0:
        print("  [WARN] No valid predictions made.")
        return

    accuracy = (tp + tn) / total_valid
    fpr      = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # false positive rate
    fnr      = fn / (fn + tp) if (fn + tp) > 0 else 0.0  # false negative rate (dangerous)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    print(f"  Total images      : {total}")
    print(f"  Valid predictions : {total_valid}")
    print(f"  Errors            : {errors}")
    print()
    print(f"  True positives    : {tp:>4}  (counterfeit correctly caught)")
    print(f"  True negatives    : {tn:>4}  (authentic correctly cleared)")
    print(f"  False positives   : {fp:>4}  (authentic wrongly flagged)  ← affects trust")
    print(f"  False negatives   : {fn:>4}  (counterfeit missed)         ← DANGEROUS")
    print()
    print(f"  Accuracy          : {accuracy*100:.1f}%")
    print(f"  False Positive Rate: {fpr*100:.1f}%")
    print(f"  False Negative Rate: {fnr*100:.1f}%  ← target: as close to 0% as possible")
    print(f"  Precision         : {precision*100:.1f}%")
    print(f"  Recall            : {recall*100:.1f}%")

    print()
    if fpr <= 0.05:
        print("  ✅ False positive rate within acceptable range (≤5%)")
    else:
        print("  ⚠️  False positive rate too high — consider more authentic samples")

    if fnr == 0.0:
        print("  ✅ No counterfeits missed on this holdout set")
    elif fnr <= 0.02:
        print("  ⚠️  Low false negative rate — continue monitoring with more data")
    else:
        print("  ❌ False negative rate too high — counterfeits being missed!")
        print("     Add more counterfeit samples and retrain.")

    print("─" * 60 + "\n")


# ─────────────────────────────────────────────
# SINGLE IMAGE TEST (quick spot-check)
# ─────────────────────────────────────────────

def test_single_image(image_path: str, db_dir: str, calibration_card: str = None):
    """
    Quick test: run one image and print the verdict.
    Useful for testing a specific blister pack during development.
    """
    sess, scaler_mean, scaler_scale = load_model_and_scaler(db_dir)
    result = predict_image(image_path, sess, scaler_mean, scaler_scale, calibration_card)

    print(f"\n{'='*55}")
    print(f"  VERUM Single Image Test")
    print(f"{'='*55}")
    print(f"  Image: {image_path}")
    print()

    if not result['success']:
        print(f"  ❌ Failed: {result['error']}")
        return

    verdict = result['prediction_label']
    conf    = result['confidence']

    if verdict == "AUTHENTIC":
        print(f"  ✅ VERDICT: AUTHENTIC")
    elif verdict == "COUNTERFEIT":
        print(f"  🚨 VERDICT: COUNTERFEIT")
    else:
        print(f"  ⚠️  VERDICT: {verdict}")

    print(f"  Confidence: {conf*100:.1f}%")
    print(f"\n  Raw vectors:")
    print(f"    Colour (L*,a*,b*) : {result['colour_vector']}")
    print(f"    Geometry          : {result['geometry_vector']}")
    print(f"    Frequency (DCT)   : {result['frequency_vector']}")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HELIX VERUM — Validate model on holdout images"
    )
    parser.add_argument(
        "--holdout",
        default="datasets/verum/holdout",
        help="Holdout image directory (filenames must contain 'authentic' or 'counterfeit')"
    )
    parser.add_argument(
        "--db",
        default="apps/verum/public/db",
        help="Database directory containing model and manifest"
    )
    parser.add_argument(
        "--calibration",
        default=None,
        help="Calibration card photo path"
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Test a single image instead of full holdout validation"
    )

    args = parser.parse_args()

    if args.image:
        test_single_image(args.image, args.db, args.calibration)
    else:
        validate_holdout(args.holdout, args.db, args.calibration)