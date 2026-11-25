"""Held-out evaluation for the active 38-class ONNX model on ZIP manifests."""
import csv, json, sys, time, zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import onnxruntime as ort

ROOT=Path(__file__).resolve().parents[1]
ML=ROOT/'backend/ml'; OUT=ML/'experiments/stage3_preflight'
sys.path.insert(0,str(ML)); import predict
classes=predict.get_class_names(); index={c:i for i,c in enumerate(classes)}
manifest=OUT/'plantvillage_test.csv'
with manifest.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
if len(classes)!=38 or len(index)!=38: raise RuntimeError('Expected exactly 38 unique classes')
if any(r['class_name'] not in index for r in rows): raise RuntimeError('Manifest contains unknown labels')
session=predict.get_inference_session(); inp=session.get_inputs()[0].name
cm=np.zeros((38,38),dtype=np.int64); start=time.perf_counter(); n=0
byzip={}
try:
 batch_x=[]; batch_y=[]
 for row in rows:
  zp=ROOT/row['archive']
  if zp not in byzip: byzip[zp]=zipfile.ZipFile(zp)
  z=byzip[zp]
  with Image.open(BytesIO(z.read(row['member']))) as im:
   batch_x.append(predict.preprocess_image(ImageOps.exif_transpose(im))[0])
  batch_y.append(index[row['class_name']])
  if len(batch_x)==32:
   logits=session.run(None,{inp:np.stack(batch_x)})[0]
   for actual,pred in zip(batch_y,np.argmax(logits,axis=1)): cm[actual,int(pred)]+=1
   n+=len(batch_x); batch_x.clear(); batch_y.clear()
 if batch_x:
  logits=session.run(None,{inp:np.stack(batch_x)})[0]
  for actual,pred in zip(batch_y,np.argmax(logits,axis=1)): cm[actual,int(pred)]+=1
  n+=len(batch_x)
finally:
 for z in byzip.values(): z.close()
total=int(cm.sum()); accuracy=float(cm.trace()/total)
per=[]
for i,c in enumerate(classes):
 tp=int(cm[i,i]); support=int(cm[i].sum()); predicted=int(cm[:,i].sum())
 precision=tp/predicted if predicted else 0.; recall=tp/support if support else 0.
 f1=2*precision*recall/(precision+recall) if precision+recall else 0.
 per.append({'class_name':c,'support':support,'precision':precision,'recall':recall,'f1':f1})
report={'model':'backend/ml/models/efficientnet_v2_s_best.onnx','provider':session.get_providers(),
 'dataset':'PlantVillage held-out test manifest','images':total,'classes':38,'accuracy':accuracy,
 'macro_precision':float(np.mean([x['precision'] for x in per])),
 'macro_recall':float(np.mean([x['recall'] for x in per])),
 'macro_f1':float(np.mean([x['f1'] for x in per])),
 'weighted_f1':float(sum(x['f1']*x['support'] for x in per)/total),
 'duration_seconds':round(time.perf_counter()-start,3),'per_class':per}
target=OUT/'onnx_plantvillage_heldout_evaluation.json'
if target.exists(): raise FileExistsError(target)
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
with (OUT/'onnx_plantvillage_confusion_matrix.csv').open('x',newline='',encoding='utf-8') as f:
 w=csv.writer(f); w.writerow(['actual\\predicted',*classes]);
 for c,row in zip(classes,cm): w.writerow([c,*map(int,row)])
print(json.dumps({k:report[k] for k in ('images','accuracy','macro_precision','macro_recall','macro_f1','weighted_f1','duration_seconds')}))
