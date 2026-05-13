# scripts/prep_vera_data.py
"""
Prepares ISIC 2019 for training.
Run: python scripts/prep_vera_data.py
Input:  datasets/vera/raw/ISIC_2019_Training_Input/  (unzipped images)
        datasets/vera/raw/ISIC_2019_Training_GroundTruth.csv
Output: datasets/vera/train/<class>/*.jpg
        datasets/vera/val/<class>/*.jpg
"""
import csv, shutil, random
from pathlib import Path

# ISIC 2019 classes → our display names
CLASS_MAP = {
    'MEL':  'Melanoma',
    'NV':   'Melanocytic_Nevi',
    'BCC':  'Basal_Cell_Carcinoma',
    'AK':   'Actinic_Keratosis',
    'BKL':  'Seborrheic_Keratosis',
    'DF':   'Dermatofibroma',
    'VASC': 'Vascular_Lesion',
    'SCC':  'Squamous_Cell_Carcinoma',
}

RAW_IMGS  = Path('datasets/vera/raw/ISIC_2019_Training_Input')
LABELS    = Path('datasets/vera/raw/ISIC_2019_Training_GroundTruth.csv')
TRAIN_OUT = Path('datasets/vera/train')
VAL_OUT   = Path('datasets/vera/val')
VAL_SPLIT = 0.15
random.seed(42)

# Read labels
rows: dict[str, str] = {}
with open(LABELS) as f:
    reader = csv.DictReader(f)
    headers = [h for h in CLASS_MAP if h in (reader.fieldnames or [])]
    for row in reader:
        label = next((CLASS_MAP[h] for h in headers if row.get(h) == '1.0'), None)
        if label:
            rows[row['image']] = label

print(f'Loaded {len(rows)} labelled images')

# Split and copy
by_class: dict[str, list[str]] = {}
for img_id, label in rows.items():
    by_class.setdefault(label, []).append(img_id)

total = 0
for label, ids in by_class.items():
    random.shuffle(ids)
    split = int(len(ids) * (1 - VAL_SPLIT))
    for split_ids, out_dir in [(ids[:split], TRAIN_OUT), (ids[split:], VAL_OUT)]:
        (out_dir / label).mkdir(parents=True, exist_ok=True)
        for img_id in split_ids:
            src = RAW_IMGS / f'{img_id}.jpg'
            if src.exists():
                shutil.copy(src, out_dir / label / f'{img_id}.jpg')
                total += 1

print(f'Done. {total} images organised.')
for label in CLASS_MAP.values():
    tr = len(list((TRAIN_OUT / label).glob('*.jpg'))) if (TRAIN_OUT / label).exists() else 0
    va = len(list((VAL_OUT   / label).glob('*.jpg'))) if (VAL_OUT   / label).exists() else 0
    print(f'  {label:35s} train={tr:4d}  val={va:4d}')