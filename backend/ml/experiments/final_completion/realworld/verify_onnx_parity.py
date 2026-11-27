"""Compare checkpoint and experiment ONNX on 20 field validation images."""
import argparse,csv,json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
import torch
from torch import nn
from torchvision import models
EXP=Path(__file__).resolve().parent
MEAN=np.array([.485,.456,.406],np.float32); STD=np.array([.229,.224,.225],np.float32)
def tensor(path):
    with Image.open(path) as im: a=np.asarray(ImageOps.exif_transpose(im).convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32)/255
    a=(a-MEAN)/STD; return np.transpose(a,(2,0,1)).astype(np.float32)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root',required=True,type=Path); p.add_argument('--plantdoc-root',required=True,type=Path); p.add_argument('--checkpoint',type=Path,default=EXP/'training/best.pt'); p.add_argument('--onnx',type=Path,default=EXP/'export/efficientnet_v2_s_realworld.onnx'); a=p.parse_args()
    import onnxruntime as ort
    rows=list(csv.DictReader((EXP/'field_val.csv').open(encoding='utf-8-sig')))
    if len(rows)<20: raise RuntimeError('Need 20 field_val samples for parity check')
    rows=rows[:20]; classes=json.loads((EXP/'classes.json').read_text())['classes']; ckpt=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    model=models.efficientnet_v2_s(weights=None); model.classifier[1]=nn.Linear(model.classifier[1].in_features,38); model.load_state_dict(ckpt['model_state'],strict=True); model.eval()
    paths=[(a.plantdoc_root/r['image_path']).resolve() for r in rows]
    for path,row in zip(paths,rows):
        if not path.is_file() or sha(path)!=row['sha256']: raise RuntimeError(f'field_val image SHA mismatch: {path}')
    x=np.stack([tensor(p) for p in paths]);
    with torch.inference_mode(): pt=model(torch.from_numpy(x)).numpy()
    sess=ort.InferenceSession(str(a.onnx),providers=['CPUExecutionProvider']); ortout=sess.run(['logits'],{'input':x})[0]
    if pt.shape!=(20,38) or ortout.shape!=(20,38): raise RuntimeError(f'Unexpected outputs: {pt.shape}, {ortout.shape}')
    d=np.abs(pt-ortout); report={'sample_count':20,'source':'field_val only','maximum_absolute_difference':float(d.max()),'mean_absolute_difference':float(d.mean()),'top1_agreement':float((pt.argmax(1)==ortout.argmax(1)).mean()),'pytorch_shape':list(pt.shape),'onnx_shape':list(ortout.shape),'onnx_input_names':[i.name for i in sess.get_inputs()],'onnx_output_names':[o.name for o in sess.get_outputs()],'providers':sess.get_providers(),'preprocessing':'EXIF transpose, RGB, direct 224x224 BILINEAR resize, /255, ImageNet mean/std, NCHW float32'}
    out=EXP/'export/parity_report.json'
    if out.exists(): raise FileExistsError(out)
    out.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__':main()
