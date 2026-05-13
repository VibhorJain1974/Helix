"""
VERA Model Training — MobileNetV3-Small, 8 disease classes
Target: 82%+ accuracy, INT8 quantised, <12MB TF.js export

Usage:
  conda activate helix
  python scripts/train_vera.py --data datasets/vera --output models/vera
  python scripts/train_vera.py --data datasets/vera --output models/vera --wandb
"""
import argparse
import json
from pathlib import Path
from typing import Tuple

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from tqdm import tqdm

# ── Config ──────────────────────────────────────────────────────
NUM_CLASSES  = 8
IMG_SIZE     = 224
BATCH_SIZE   = 32
LR           = 1e-4
WEIGHT_DECAY = 1e-4
EPOCHS       = 50
PATIENCE     = 10

DISEASE_CLASSES = [
    'Cutaneous_Leishmaniasis', 'Tinea_Corporis',
    'Scabies', 'Impetigo', 'Cellulitis',
    'Melanocytic_Nevi', 'Seborrheic_Keratosis',
    'Basal_Cell_Carcinoma',
]

MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

train_tf = T.Compose([
    T.Resize(256),
    T.RandomCrop(IMG_SIZE),
    T.RandomHorizontalFlip(),
    T.RandomRotation(15),
    T.ColorJitter(0.2, 0.2, 0.2, 0.1),
    T.RandomErasing(p=0.1),
    T.ToTensor(),
    T.Normalize(MEAN, STD),
])

val_tf = T.Compose([
    T.Resize(IMG_SIZE),
    T.CenterCrop(IMG_SIZE),
    T.ToTensor(),
    T.Normalize(MEAN, STD),
])

def build_model(num_classes: int) -> nn.Module:
    model = models.mobilenet_v3_small(weights='IMAGENET1K_V1')
    in_features: int = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model

def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None,
    device: torch.device,
    train: bool,
) -> Tuple[float, float]:
    model.train(train)
    total_loss = correct = total = 0

    with torch.set_grad_enabled(train):
        for imgs, labels in tqdm(loader, desc='Train' if train else 'Val ', leave=False):
            imgs, labels = imgs.to(device), labels.to(device)
            out  = model(imgs)
            loss = criterion(out, labels)
            if train and optimizer:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item()
            correct    += out.argmax(1).eq(labels).sum().item()
            total      += labels.size(0)

    return total_loss / len(loader), 100.0 * correct / total

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--data',   default='datasets/vera')
    ap.add_argument('--output', default='models/vera')
    ap.add_argument('--epochs', type=int, default=EPOCHS)
    ap.add_argument('--wandb',  action='store_true')
    args = ap.parse_args()

    device = torch.device(
        'cuda' if torch.cuda.is_available() else
        'mps'  if torch.backends.mps.is_available() else
        'cpu'
    )
    print(f'Device : {device}')

    data_root = Path(args.data)
    if not (data_root / 'train').exists():
        print(f'ERROR: {data_root}/train not found.')
        print('Download ISIC 2019: https://www.isic-archive.com')
        return

    train_ds = ImageFolder(str(data_root / 'train'), train_tf)
    val_ds   = ImageFolder(str(data_root / 'val'),   val_tf)
    train_dl = DataLoader(train_ds, BATCH_SIZE, shuffle=True,  num_workers=4, pin_memory=True)
    val_dl   = DataLoader(val_ds,   BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

    print(f'Train: {len(train_ds)} | Val: {len(val_ds)}')

    model     = build_model(len(train_ds.classes)).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.wandb:
        import wandb
        wandb.init(project='helix-vera', config=vars(args))

    best_acc = 0.0
    patience = 0
    history: list[dict] = []

    for epoch in range(1, args.epochs + 1):
        tr_loss, tr_acc = run_epoch(model, train_dl, criterion, optimizer, device, True)
        va_loss, va_acc = run_epoch(model, val_dl,   criterion, None,      device, False)
        scheduler.step()

        print(f'Ep {epoch:02d}/{args.epochs}  train {tr_acc:.1f}%  val {va_acc:.1f}%  [best {best_acc:.1f}%]')

        if args.wandb:
            import wandb
            wandb.log({'train_acc': tr_acc, 'val_acc': va_acc, 'epoch': epoch})

        if va_acc > best_acc:
            best_acc = va_acc
            torch.save(model.state_dict(), out_dir / 'best.pt')
            print(f'  ✓ New best saved')
            patience = 0
        else:
            patience += 1
            if patience >= PATIENCE:
                print(f'  Early stop at epoch {epoch}')
                break

        history.append({'epoch': epoch, 'train_acc': tr_acc, 'val_acc': va_acc})

    with open(out_dir / 'training_history.json', 'w') as f:
        json.dump({'best_val_acc': best_acc, 'history': history,
                   'classes': train_ds.classes}, f, indent=2)

    print(f'\nBest val accuracy: {best_acc:.2f}%')
    print('TARGET REACHED (82%+)' if best_acc >= 82.0 else 'Below 82% — need more data')

if __name__ == '__main__':
    main()