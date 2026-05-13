"""
VERA Export: PyTorch best.pt → ONNX → TF.js GraphModel
Run AFTER training: python scripts/export_vera.py --checkpoint models/vera/best.pt
Output: models/vera/tfjs/ → copy to apps/vera/public/models/vera/
"""
import argparse
import json
import subprocess
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.models as models


def build_model(num_classes: int = 8) -> nn.Module:
    model = models.mobilenet_v3_small(weights=None)
    model.classifier[-1] = nn.Linear(1024, num_classes)
    return model


def export(checkpoint: str, output_dir: str, num_classes: int = 8) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print('Step 1/4: Loading checkpoint...')
    model = build_model(num_classes)
    state = torch.load(checkpoint, map_location='cpu')
    model.load_state_dict(state)
    model.eval()
    print(f'  Parameters: {sum(p.numel() for p in model.parameters()):,}')

    print('Step 2/4: Exporting to ONNX...')
    dummy = torch.randn(1, 3, 224, 224)
    onnx_path = out / 'vera.onnx'
    torch.onnx.export(
        model, dummy, str(onnx_path),
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}},
        opset_version=17,
    )
    print(f'  ONNX: {onnx_path.stat().st_size / 1e6:.1f}MB')

    print('Step 3/4: Converting to TF.js...')
    tfjs_dir = out / 'tfjs'
    tfjs_dir.mkdir(exist_ok=True)
    result = subprocess.run([
        'tensorflowjs_converter',
        '--input_format=onnx',
        '--output_format=tfjs_graph_model',
        '--quantize_uint8',
        str(onnx_path),
        str(tfjs_dir),
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print('ERROR: TF.js conversion failed')
        print(result.stderr)
        return

    print('Step 4/4: Validating...')
    total_mb = sum(f.stat().st_size for f in tfjs_dir.rglob('*') if f.is_file()) / 1e6
    print(f'  TF.js size: {total_mb:.1f}MB (target <12MB) {"OK" if total_mb < 12.0 else "TOO LARGE"}')

    meta = {
        'model': 'MobileNetV3-Small',
        'input_size': [1, 3, 224, 224],
        'normalisation': {'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]},
        'classes': [
            'Cutaneous_Leishmaniasis', 'Tinea_Corporis',
            'Scabies', 'Impetigo', 'Cellulitis',
            'Melanocytic_Nevi', 'Seborrheic_Keratosis',
            'Basal_Cell_Carcinoma',
        ],
        'disclaimer': 'Screening tool only. Confirm with qualified health worker.',
    }
    with open(tfjs_dir / 'metadata.json', 'w') as f:
        json.dump(meta, f, indent=2)

    print('\nExport complete.')
    print(f'Copy to app: xcopy /E /I models\\vera\\tfjs apps\\vera\\public\\models\\vera')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', default='models/vera/best.pt')
    ap.add_argument('--output',     default='models/vera')
    ap.add_argument('--classes',    type=int, default=8)
    args = ap.parse_args()
    export(args.checkpoint, args.output, args.classes)