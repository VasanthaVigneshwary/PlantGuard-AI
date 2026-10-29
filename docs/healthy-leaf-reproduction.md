# Reproduce the healthy-leaf prediction

The project copy of `GREEN LEAF HEALTHY.webp` was not found during the Phase 2
file search. Do not substitute another image or treat an unlabeled image as
ground truth. When the original file is available, run this from the project
root in PowerShell and replace the path with its actual location:

```powershell
$ImagePath = 'C:\path\to\GREEN LEAF HEALTHY.webp'
@'
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps
sys.path.insert(0, str(Path.cwd() / 'backend'))
from ml.predict import ONNX_MODEL_PATH, predict_disease

image_path = Path(sys.argv[1])
with Image.open(image_path) as image:
    original_dimensions = image.size
    oriented_dimensions = ImageOps.exif_transpose(image).size

first = predict_disease(image_path, top_k=5)
second = predict_disease(image_path, top_k=5)
external_weights = ONNX_MODEL_PATH.with_suffix(ONNX_MODEL_PATH.suffix + '.data')
report = {
    'image': str(image_path.resolve()),
    'original_dimensions': original_dimensions,
    'exif_oriented_dimensions': oriented_dimensions,
    'preprocessing': (
        'EXIF transpose; RGB; bilinear resize to 224x224; float32 scaling to [0,1]; '
        'ImageNet mean/std normalization; NCHW layout'
    ),
    'model_sha256': hashlib.sha256(ONNX_MODEL_PATH.read_bytes()).hexdigest(),
    'external_weights_sha256': hashlib.sha256(external_weights.read_bytes()).hexdigest(),
    'first_result': first,
    'second_result': second,
    'identical_repeat': first == second,
}
print(json.dumps(report, indent=2))
'@ | & '.\.venv\Scripts\python.exe' - $ImagePath
```

The result includes the top five class scores in `top_predictions`. They are raw
softmax scores, not calibrated probabilities. Preserve the exact image and
printed report together; only an independently verified label can establish
whether the prediction was correct.
