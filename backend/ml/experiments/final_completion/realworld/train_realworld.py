"""Approved manual-run entry point. Never downloads weights or starts unless explicitly invoked."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, random, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms
from torchvision.transforms import InterpolationMode
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

EXP=Path(__file__).resolve().parent
SEED=20261127
TIME_LIMIT_SECONDS=75*60
BATCH_SIZE=32
WORKERS=2
IMAGENET_MEAN=(0.485,0.456,0.406); IMAGENET_STD=(0.229,0.224,0.225)

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def load_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False
    torch.use_deterministic_algorithms(True,warn_only=True)
def worker_seed(worker_id):
    seed=torch.initial_seed()%2**32; random.seed(seed); np.random.seed(seed)

def cached_imagenet_state():
    weights=models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
    cache=Path(torch.hub.get_dir())/'checkpoints'/Path(weights.url).name
    if not cache.is_file():
        raise RuntimeError(f'PRETRAINED_WEIGHT_MISSING: expected cached ImageNet weights at {cache}; no download attempted. Obtain explicit permission before downloading.')
    state=torch.load(cache,map_location='cpu',weights_only=True)
    if not isinstance(state,dict) or 'classifier.1.weight' not in state:
        raise RuntimeError('Cached ImageNet state dictionary is not a verified EfficientNetV2-S checkpoint')
    return state,cache

def build_model(classes, cached_state=None):
    model=models.efficientnet_v2_s(weights=None)
    if cached_state is not None: model.load_state_dict(cached_state,strict=True)
    model.classifier[1]=nn.Linear(model.classifier[1].in_features,len(classes))
    return model

class ManifestImages(Dataset):
    def __init__(self,rows,pv_root,field_root,training=False):
        self.rows=rows; self.pv_root=Path(pv_root); self.field_root=Path(field_root); self.training=training
        if training:
            self.tf=transforms.Compose([
              transforms.RandomResizedCrop(224,scale=(0.35,1.0),interpolation=InterpolationMode.BILINEAR),
              transforms.RandomHorizontalFlip(),transforms.RandomVerticalFlip(),transforms.RandomRotation(20,interpolation=InterpolationMode.BILINEAR),
              transforms.ColorJitter(brightness=.2,contrast=.2,saturation=.2,hue=.05),
              transforms.RandomApply([transforms.GaussianBlur(3)],p=.2),transforms.ToTensor(),transforms.Normalize(IMAGENET_MEAN,IMAGENET_STD),
              transforms.RandomErasing(p=.25)
            ])
        else:
            self.tf=transforms.Compose([transforms.Resize((224,224),interpolation=InterpolationMode.BILINEAR),transforms.ToTensor(),transforms.Normalize(IMAGENET_MEAN,IMAGENET_STD)])
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        row=self.rows[i]; root=self.pv_root if row['source']=='PlantVillage' else self.field_root
        rel=row['archive_member'] if row['source']=='PlantVillage' else row['image_path']
        path=(root/rel).resolve()
        if root.resolve() not in path.parents: raise RuntimeError(f'Image path escapes extracted data root: {rel}')
        with Image.open(path) as im: image=ImageOps.exif_transpose(im).convert('RGB')
        return self.tf(image),int(row['class_index'])

def verify_manifest(rows,root,source):
    for i,row in enumerate(rows,1):
        path=(root/(row['archive_member'] if source=='PlantVillage' else row['image_path'])).resolve()
        if root.resolve() not in path.parents or not path.is_file(): raise FileNotFoundError(path)
        if sha256(path)!=row['sha256']: raise RuntimeError(f'Manifest SHA-256 mismatch: {path}')
        if i%5000==0: print(f'Verified {source}: {i}/{len(rows)}',flush=True)

def sample_epoch(pv_rows,field_rows,epoch_seed):
    rng=np.random.default_rng(epoch_seed); by_class=defaultdict(list)
    for row in pv_rows: by_class[int(row['class_index'])].append(row)
    pv_sample=[]
    for ci in range(38):
        pool=by_class.get(ci,[])
        if not pool: raise RuntimeError(f'PlantVillage training class {ci} is empty after eval leakage filtering')
        indices=rng.choice(len(pool),size=300,replace=len(pool)<300)
        pv_sample.extend(pool[int(i)] for i in indices)
    field_count=math.ceil(len(pv_sample)*2/3) # 40% of combined sample.
    field_by=defaultdict(list)
    for row in field_rows: field_by[int(row['class_index'])].append(row)
    present=sorted(field_by)
    if not present: raise RuntimeError('No eligible mapped field training images remain')
    field_sample=[]
    for _ in range(field_count):
        ci=present[int(rng.integers(len(present)))]; pool=field_by[ci]
        field_sample.append(pool[int(rng.integers(len(pool)))])
    combined=pv_sample+field_sample; rng.shuffle(combined)
    return combined,len(pv_sample),len(field_sample)

def atomic_torch_save(payload,path):
    temp=path.with_suffix(path.suffix+'.tmp'); torch.save(payload,temp); temp.replace(path)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root',required=True,type=Path); ap.add_argument('--plantvillage-root',required=True,type=Path); ap.add_argument('--plantdoc-root',required=True,type=Path)
    args=ap.parse_args(); project=args.project_root.resolve(); pv_root=args.plantvillage_root.resolve(); field_root=args.plantdoc_root.resolve()
    if not torch.cuda.is_available(): raise RuntimeError('CUDA/T4 is not available; training stopped.')
    if torch.cuda.get_device_capability(0)[0]<7: raise RuntimeError('Unexpected CUDA device capability; verify Colab T4.')
    classes=json.loads((EXP/'classes.json').read_text(encoding='utf-8'))['classes']
    if len(classes)!=38 or len(set(classes))!=38: raise RuntimeError('Experiment class mapping must contain the unchanged 38 labels.')
    out=EXP/'training'
    if out.exists() and any(out.iterdir()): raise FileExistsError(f'Training output already exists; refusing overwrite/resume: {out}')
    out.mkdir(parents=True,exist_ok=True)
    pv=load_rows(EXP/'plantvillage_train_filtered.csv'); field=load_rows(EXP/'field_train.csv'); val=load_rows(EXP/'field_val.csv')
    if any(int(r['class_index'])>=38 or classes[int(r['class_index'])]!=r['class_name'] for r in pv+field+val): raise RuntimeError('Manifest class-index mismatch')
    if {r['source'] for r in pv}!={'PlantVillage'} or {r['source'] for r in field+val}!={'PlantDoc'}: raise RuntimeError('Unexpected source in training manifests')
    if set(r['sha256'] for r in field)&set(r['sha256'] for r in val): raise RuntimeError('Field train/val exact overlap')
    verify_manifest(pv,pv_root,'PlantVillage'); verify_manifest(field,field_root,'PlantDoc'); verify_manifest(val,field_root,'PlantDoc')
    state,weights_path=cached_imagenet_state()
    seeds={'python':SEED,'numpy':SEED,'torch':SEED,'cuda':SEED,'dataloader_worker_base':SEED}
    seed_all(SEED)
    model=build_model(classes,state).cuda()
    config={'architecture':'torchvision.models.efficientnet_v2_s','classes':classes,'class_count':38,'input_size':[224,224],
      'pretrained_weights':'ImageNet IMAGENET1K_V1 cached-only','pretrained_cache_path':str(weights_path),'pretrained_cache_sha256':sha256(weights_path),
      'seed':seeds,'batch_size':BATCH_SIZE,'workers':WORKERS,'time_limit_seconds':TIME_LIMIT_SECONDS,'field_minimum_fraction':0.40,
      'plantvillage_max_samples_per_class_per_epoch':300,'phase_a_epochs':2,'phase_b_epochs':8,'optimizer':'AdamW','phase_b_lr':1e-4,
      'phase_b_schedule':'CosineAnnealingLR, T_max=8','label_smoothing':0.1,'best_checkpoint_metric':'field_val_macro_f1',
      'preprocessing':'EXIF transpose, RGB, train-only augmentation; evaluation resize 224x224 BILINEAR, /255, ImageNet mean/std, CHW float32',
      'field_train_manifest_sha256':sha256(EXP/'field_train.csv'),'field_val_manifest_sha256':sha256(EXP/'field_val.csv'),
      'plantvillage_train_manifest_sha256':sha256(EXP/'plantvillage_train_filtered.csv')}
    (out/'configuration.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    (out/'classes.json').write_text((EXP/'classes.json').read_text(encoding='utf-8'),encoding='utf-8')
    train_transform_ds=ManifestImages([],pv_root,field_root,training=True); eval_ds=ManifestImages(val,pv_root,field_root,training=False)
    val_loader=DataLoader(eval_ds,batch_size=BATCH_SIZE,shuffle=False,num_workers=WORKERS,pin_memory=True,worker_init_fn=worker_seed)
    criterion_head=nn.CrossEntropyLoss()
    for p in model.parameters(): p.requires_grad=False
    for p in model.classifier.parameters(): p.requires_grad=True
    optimizer=torch.optim.AdamW(model.classifier.parameters(),lr=1e-4)
    scheduler=None; scaler=torch.amp.GradScaler('cuda'); best=-1.0; start=time.monotonic(); metric_file=out/'epoch_metrics.csv'
    metric_fields=['epoch','phase','train_loss','train_accuracy','train_macro_precision','train_macro_recall','train_macro_f1','field_val_loss','field_val_accuracy','field_val_macro_precision','field_val_macro_recall','field_val_macro_f1','field_samples','plantvillage_samples','elapsed_seconds','learning_rate']
    with metric_file.open('w',newline='',encoding='utf-8') as f: csv.DictWriter(f,fieldnames=metric_fields).writeheader()
    total_epoch=0; status='completed'
    for phase,epochs in [('A',2),('B',8)]:
        if phase=='B':
            for p in model.parameters(): p.requires_grad=True
            optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4)
            scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=8)
        for phase_epoch in range(epochs):
            if time.monotonic()-start>=TIME_LIMIT_SECONDS: status='incomplete_time_limit'; break
            total_epoch+=1; model.train()
            if phase=='A':
                # Keep frozen backbone batch-normalization statistics fixed as well as its gradients.
                model.features.eval(); model.classifier.train()
            samples,pv_n,field_n=sample_epoch(pv,field,SEED+total_epoch)
            ds=ManifestImages(samples,pv_root,field_root,training=True)
            gen=torch.Generator(); gen.manual_seed(SEED+total_epoch)
            loader=DataLoader(ds,batch_size=BATCH_SIZE,shuffle=True,num_workers=WORKERS,pin_memory=True,worker_init_fn=worker_seed,generator=gen)
            losses=[]; true=[]; pred=[]
            for xb,yb in loader:
                xb=xb.cuda(non_blocking=True); yb=yb.cuda(non_blocking=True); optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type='cuda',dtype=torch.float16): logits=model(xb); loss=nn.functional.cross_entropy(logits,yb,label_smoothing=.1 if phase=='B' else 0.0)
                scaler.scale(loss).backward(); scaler.step(optimizer); scaler.update()
                losses.append(float(loss.detach().item())); pred.extend(logits.detach().argmax(1).cpu().tolist()); true.extend(yb.cpu().tolist())
            if scheduler is not None: scheduler.step()
            train_pr,train_rc,train_f1,_=precision_recall_fscore_support(true,pred,labels=list(range(38)),average='macro',zero_division=0)
            model.eval(); vtrue=[]; vpred=[]; vloss=[]
            with torch.inference_mode():
                for xb,yb in val_loader:
                    xb=xb.cuda(non_blocking=True); yb=yb.cuda(non_blocking=True)
                    with torch.autocast(device_type='cuda',dtype=torch.float16): logits=model(xb); loss=nn.functional.cross_entropy(logits,yb)
                    vloss.append(float(loss.item())); vpred.extend(logits.argmax(1).cpu().tolist()); vtrue.extend(yb.cpu().tolist())
            vpr,vrc,vf1,_=precision_recall_fscore_support(vtrue,vpred,labels=list(range(38)),average='macro',zero_division=0)
            val_loss=float(np.mean(vloss)); val_acc=float(accuracy_score(vtrue,vpred)); elapsed=time.monotonic()-start
            row={'epoch':total_epoch,'phase':phase,'train_loss':float(np.mean(losses)),'train_accuracy':float(accuracy_score(true,pred)),
              'train_macro_precision':float(train_pr),'train_macro_recall':float(train_rc),'train_macro_f1':float(train_f1),
              'field_val_loss':val_loss,'field_val_accuracy':val_acc,'field_val_macro_precision':float(vpr),'field_val_macro_recall':float(vrc),'field_val_macro_f1':float(vf1),
              'field_samples':field_n,'plantvillage_samples':pv_n,'elapsed_seconds':elapsed,'learning_rate':optimizer.param_groups[0]['lr']}
            with metric_file.open('a',newline='',encoding='utf-8') as f: csv.DictWriter(f,fieldnames=metric_fields).writerow(row)
            checkpoint={'model_state':model.state_dict(),'optimizer_state':optimizer.state_dict(),'scheduler_state':scheduler.state_dict() if scheduler else None,
              'scaler_state':scaler.state_dict(),'epoch':total_epoch,'phase':phase,'field_val_macro_f1':float(vf1),'config':config,'rng_python':random.getstate(),
              'rng_numpy':np.random.get_state(),'rng_torch':torch.get_rng_state(),'rng_cuda':torch.cuda.get_rng_state_all()}
            atomic_torch_save(checkpoint,out/'last.pt')
            if float(vf1)>best:
                best=float(vf1); atomic_torch_save(checkpoint,out/'best.pt')
            print(json.dumps(row),flush=True)
        if status!='completed': break
    summary={'status':status,'completed_epochs':total_epoch,'best_field_val_macro_f1':best if best>=0 else None,'elapsed_seconds':time.monotonic()-start,
      'time_limit_seconds':TIME_LIMIT_SECONDS,'training_executed':True,'classes':38,'checkpoint_best':'best.pt' if (out/'best.pt').exists() else None,'checkpoint_last':'last.pt' if (out/'last.pt').exists() else None}
    (out/'training_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
