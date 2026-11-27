"""Cached-only linear-probe bake-off. Never downloads, trains a backbone, or writes production files."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,random,sys,time,zipfile
from datetime import datetime,timezone
import platform
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
BASE=Path(__file__).resolve().parent;REAL=BASE.parent;ROOT=BASE.parents[5]
SEED=20261127;C_GRID=(0.001,0.01,0.1,1.0,10.0,100.0);BATCH=32;BOOTSTRAPS=2000
MEAN=(0.485,0.456,0.406);STD=(0.229,0.224,0.225)
def csvread(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def manifest_hashes(rows,path_key,root):
    """Hash every referenced image and reject stale manifest digests."""
    out=[]
    for row in rows:
        path=(root/row[path_key]).resolve()
        if not path.is_file():raise FileNotFoundError(path)
        digest=sha_file(path)
        if row.get('sha256') and digest!=row['sha256']:raise RuntimeError(f'SHA-256 mismatch: {path}')
        out.append({'image_path':row[path_key],'sha256':digest})
    return out
def image_bytes(row,source,pvzip,pdroot):
    if source=='pv':
        member=row.get('archive_member',row.get('member'))
        raw=pvzip.read(member)
    else:raw=(pdroot/row['image_path']).read_bytes()
    if row.get('sha256') and sha_bytes(raw)!=row['sha256']:raise RuntimeError(f'Image hash mismatch: {row}')
    with Image.open(__import__('io').BytesIO(raw)) as im:return ImageOps.exif_transpose(im).convert('RGB').copy()
def dino_transform(image):
    from torchvision import transforms
    from torchvision.transforms import InterpolationMode
    tf=transforms.Compose([transforms.Resize(256,interpolation=InterpolationMode.BICUBIC),transforms.CenterCrop(224),transforms.ToTensor(),transforms.Normalize(MEAN,STD)])
    return tf(image)
def class_metrics(y,pred,probs,classes,covered_ids):
    from sklearn.metrics import accuracy_score,f1_score,precision_recall_fscore_support,top_k_accuracy_score
    top3=np.argsort(probs,axis=1)[:,-3:][:,::-1];covered=np.array([int(c) in covered_ids for c in y]);uncovered=~covered
    precision,recall,f1,support=precision_recall_fscore_support(y,pred,labels=range(len(classes)),zero_division=0)
    return {'n':len(y),'top1_accuracy':float(accuracy_score(y,pred)),'top3_accuracy':float(np.mean([yi in top for yi,top in zip(y,top3)])),'macro_f1_all_38':float(f1_score(y,pred,labels=range(len(classes)),average='macro',zero_division=0)),'crop_accuracy':None,'covered_classes':{'class_count':len(covered_ids),'sample_count':int(covered.sum()),'top1_accuracy':float(accuracy_score(y[covered],pred[covered])) if covered.any() else None,'macro_f1':float(f1_score(y[covered],pred[covered],labels=sorted(covered_ids),average='macro',zero_division=0)) if covered.any() else None},'uncovered_classes':{'class_count':len(classes)-len(covered_ids),'sample_count':int(uncovered.sum()),'top1_accuracy':float(accuracy_score(y[uncovered],pred[uncovered])) if uncovered.any() else None,'macro_f1':float(f1_score(y[uncovered],pred[uncovered],labels=sorted(set(range(len(classes)))-covered_ids),average='macro',zero_division=0)) if uncovered.any() else None},'per_class':{classes[i]:{'support':int(support[i]),'precision':float(precision[i]) if support[i] else None,'recall':float(recall[i]) if support[i] else None,'f1':float(f1[i]) if support[i] else None} for i in range(len(classes))}}
def crop_of(class_name):return class_name.split('___',1)[0]
def prediction_probability(model,x,n_classes):
    raw=model.decision_function(x)
    if raw.ndim==1:
        q=1/(1+np.exp(-raw));return np.column_stack([1-q,q])
    z=raw-raw.max(axis=1,keepdims=True);q=np.exp(z);return q/q.sum(axis=1,keepdims=True)
def make_lr(C,max_iter=2000):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=C,solver='lbfgs',max_iter=max_iter,random_state=SEED)
def fit_direct(train_x,train_y,C):
    m=make_lr(C);m.fit(train_x,train_y);return m
def direct_probs(m,x,n_classes):
    p=m.predict_proba(x);out=np.zeros((len(x),n_classes),np.float64)
    for j,c in enumerate(m.classes_):out[:,int(c)]=p[:,j]
    return out
def fit_crop_first(x,y,crop_names,C,classes):
    crop_labels=np.array([crop_names[int(i)] for i in y]);cm=make_lr(C);cm.fit(x,crop_labels)
    local={}
    for crop in sorted(set(crop_labels)):
        ix=np.flatnonzero(crop_labels==crop);sub=make_lr(C)
        diseases=np.unique(y[ix])
        if len(diseases)==1:local[crop]=int(diseases[0])
        else:sub.fit(x[ix],y[ix]);local[crop]=sub
    return cm,local
def crop_first_probs(bundle,x,n_classes):
    cm,local=bundle; crop_p=cm.predict_proba(x);crop_labels=cm.classes_[crop_p.argmax(1)];out=np.zeros((len(x),n_classes),np.float64)
    for crop in cm.classes_:
        ix=np.flatnonzero(crop_labels==crop);model=local[crop]
        if not len(ix):continue
        if isinstance(model,(int,np.integer)):out[ix,int(model)]=1.0
        else:
            p=model.predict_proba(x[ix])
            for j,c in enumerate(model.classes_):out[ix,int(c)]=p[:,j]
    return out,crop_labels
def bootstrap_ci(y,p,classes,crop_names,seed=SEED):
    from sklearn.metrics import f1_score
    rng=np.random.default_rng(seed);n=len(y);stats=[]
    for _ in range(BOOTSTRAPS):
        ix=rng.integers(0,n,n);yy=y[ix];pp=p[ix].argmax(1);top=np.argsort(p[ix],axis=1)[:,-3:]
        stats.append([np.mean(pp==yy),np.mean([a in b for a,b in zip(yy,top)]),f1_score(yy,pp,labels=range(len(classes)),average='macro',zero_division=0),np.mean([crop_names[int(a)]==crop_names[int(b)] for a,b in zip(yy,pp)])])
    a=np.asarray(stats);return {k:[float(v) for v in np.percentile(a[:,i],[2.5,97.5])] for i,k in enumerate(('top1_accuracy','top3_accuracy','macro_f1_all_38','crop_accuracy'))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,default=ROOT);ap.add_argument('--run-dir',type=Path);ap.add_argument('--batch-size',type=int,default=BATCH);a=ap.parse_args()
    # Imports below are offline-only. Never call torch.hub remote source or a package installer.
    core_error=None
    try:
        import torch
        from torchvision import transforms
        from torchvision.transforms import InterpolationMode
        from sklearn.metrics import f1_score
    except Exception as e:core_error=f'{type(e).__name__}: {e}'
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    project=a.project_root.resolve();classes=json.loads((REAL/'classes.json').read_text(encoding='utf-8'))['classes'];idx={c:i for i,c in enumerate(classes)}
    if len(classes)!=38:raise RuntimeError('Expected approved 38-class mapping')
    run=a.run_dir or BASE/('run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run=run.resolve();run.mkdir(parents=True,exist_ok=False);feature_dir=run/'features';feature_dir.mkdir()
    pv_all=csvread(REAL/'plantvillage_train_filtered.csv');ft=csvread(REAL/'field_train.csv');fv=csvread(REAL/'field_val.csv')
    rng=random.Random(SEED);pv=[];pv_sample_counts={}
    for ci,label in enumerate(classes):
        pool=[r for r in pv_all if r['class_name']==label]
        if not pool:raise RuntimeError(f'PlantVillage class {label} has no training images')
        pv_sample_counts[label]=min(300,len(pool));pv.extend(rng.sample(pool,pv_sample_counts[label]))
    pv=[{**r,'class_index':idx[r['class_name']],'source':'PlantVillage'} for r in pv]
    ft=[{**r,'source':'PlantDoc'} for r in ft];fv=[{**r,'source':'PlantDoc'} for r in fv]
    pvtest=csvread(project/'backend/ml/experiments/stage3_preflight/plantvillage_test.csv')
    pdrows=[r for r in csvread(project/'backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv') if r['metric_eligible'].lower()=='true']
    if len(pvtest)!=8154 or len(pdrows)!=123:raise RuntimeError('Fixed held-out manifests differ from expected evidence')
    pd_eval=[{'image_path':r['image_path'],'sha256':r['sha256'],'class_name':r['mapped_true_class'],'class_index':idx[r['mapped_true_class']],'source':'PlantDoc'} for r in pdrows]
    pdroot=project/'datasets/plantdoc';pvzip_path=project/'datasets/plantvillage-source.zip'
    pv_y=np.array([int(r['class_index']) for r in pv]);ft_y=np.array([int(r['class_index']) for r in ft]);fv_y=np.array([int(r['class_index']) for r in fv]);
    field_n=int(math.ceil(len(pv)*2/3));field_ix=np.random.default_rng(SEED).choice(len(ft),field_n,replace=field_n>len(ft));train_y=np.r_[pv_y,ft_y[field_ix]]
    covered_ids=set(ft_y.tolist())|set(fv_y.tolist());crop_names=[crop_of(c) for c in classes]
    bundle={'PlantVillage train':pv,'field_train_unique':ft,'field_val':fv}
    evaluation_bundle={'field_val':fv,'PlantVillage test':[{**r,'class_index':idx[r['class_name']],'source':'PlantVillage'} for r in pvtest],'PlantDoc external':pd_eval}
    protected_before=manifest_hashes(pd_eval,'image_path',pdroot)
    model_status={};results={};timings={};prediction_rows=[];env={'python':sys.version,'platform':platform.platform(),'seed':SEED,'batch_size':a.batch_size,'training_unique_pv':len(pv),'plantvillage_sample_counts_by_class':pv_sample_counts,'plantvillage_per_class_max':300,'field_train_oversampled':field_n,'field_train_fraction':field_n/(len(pv)+field_n),'c_grid':list(C_GRID),'bootstrap_replicates':BOOTSTRAPS,'bootstrap_seed':SEED,'bootstrap_method':'paired image bootstrap with replacement; percentile 2.5th/97.5th quantiles'}
    if core_error:
        protected_after=manifest_hashes(pd_eval,'image_path',pdroot)
        if protected_before!=protected_after:raise RuntimeError('Protected PlantDoc hashes changed during preflight')
        for label,records in (('before',protected_before),('after',protected_after)):
            with (run/f'protected_hashes_{label}.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=['image_path','sha256']);w.writeheader();w.writerows(records)
        model_status={n:{'status':'BLOCKED','reason':f'Core embedding/LR dependency unavailable: {core_error}'} for n in ('Production EfficientNetV2-S','DINOv2 ViT-S/14','DINOv2 ViT-B/14','BioCLIP')}
        output={'environment':env,'model_status':model_status,'feature_timings':{},'metrics':{},'protected_hashes_unchanged':True,'seed':SEED,'evaluation':'NOT RUN: required local dependencies unavailable','feature_cache_dir':str(feature_dir)}
        (run/'bakeoff_results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'run_dir':str(run),'model_status':model_status,'metric_rows':0},indent=2));return
    def load_model(name):
        hub=Path(torch.hub.get_dir());ck=hub/'checkpoints';
        if name.startswith('DINOv2'):
            arch='dinov2_vits14' if 'S/14' in name else 'dinov2_vitb14';weight=ck/('dinov2_vits14_pretrain.pth' if 'S/14' in name else 'dinov2_vitb14_pretrain.pth')
            repo_candidates=[hub/f'facebookresearch_dinov2_main',hub/'github/facebookresearch_dinov2_main']
            repo=next((p for p in repo_candidates if p.is_dir()),None)
            if not weight.is_file() or repo is None:raise RuntimeError(f'BLOCKED: cached DINOv2 code/weight missing: {weight}; download not attempted')
            model=torch.hub.load(str(repo),arch,source='local',pretrained=False)
            state=torch.load(weight,map_location='cpu',weights_only=True)
            if isinstance(state,dict) and 'teacher' in state:state=state['teacher']
            model.load_state_dict(state,strict=True);model.eval()
            return model,dino_transform,lambda m,x:m.forward_features(x)['x_norm_clstoken'],str(weight)
        if name=='BioCLIP':
            cache=Path.home()/'.cache/huggingface/hub/models--imageomics--bioclip'
            if not cache.exists() or not any(cache.rglob('open_clip_pytorch_model.bin')):raise RuntimeError('BLOCKED: BioCLIP checkpoint not cached; download not attempted')
            import open_clip
            model,_,preprocess=open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip')
            model.eval();return model,preprocess,lambda m,x:m.encode_image(x,normalize=False),str(cache)
        raise RuntimeError('Production EfficientNet ONNX embeddings BLOCKED: graph exposes logits only; no different weights allowed')
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu');env.update({'device':str(device),'gpu_name':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'cpu_count':os.cpu_count()})
    for name in ('Production EfficientNetV2-S','DINOv2 ViT-S/14','DINOv2 ViT-B/14','BioCLIP'):
        try:model,preprocess,forward,weight_source=load_model(name)
        except Exception as e:model_status[name]={'status':'BLOCKED','reason':f'{type(e).__name__}: {e}'};continue
        model_status[name]={'status':'AVAILABLE','weight_source':weight_source}
        # Benchmark CPU embedding separately on a small training-only batch.
        cpu_rows=pv[:min(16,len(pv))]
        with zipfile.ZipFile(pvzip_path) as zf:
            cpu_batch=torch.stack([preprocess(image_bytes(r,'pv',zf,pdroot)) for r in cpu_rows])
        model=model.cpu().eval();start=time.perf_counter()
        with torch.inference_mode():cpu_features=forward(model,cpu_batch)
        cpu_seconds=time.perf_counter()-start
        cpu_features=None
        model=model.to(device).eval()
        model_status[name]['cpu_embedding_benchmark']={'images':len(cpu_rows),'seconds':cpu_seconds,'seconds_per_image':cpu_seconds/len(cpu_rows),'batch_size':len(cpu_rows),'split':'PlantVillage train only'}
        with zipfile.ZipFile(pvzip_path) as zf:warmup=preprocess(image_bytes(pv[0],'pv',zf,pdroot)).unsqueeze(0).to(device)
        start=time.perf_counter()
        with torch.inference_mode():forward(model,warmup)
        if device.type=='cuda':torch.cuda.synchronize()
        warmup_seconds=time.perf_counter()-start
        model_status[name]['warmup_seconds']=warmup_seconds
        cache={}
        for split,rows in bundle.items():
            tag=name.replace('/','_').replace(' ','_').replace('-','_');file=feature_dir/f'{tag}_{split.replace(" ","_")}.npy';meta=file.with_suffix('.json')
            manifest_digest=hashlib.sha256(''.join(r['sha256'] for r in rows).encode()).hexdigest()
            if file.exists() and meta.exists():
                m=json.loads(meta.read_text());
                if m.get('manifest_sha256')!=manifest_digest:raise RuntimeError(f'Feature cache manifest mismatch: {file}')
                z=np.load(file,mmap_mode='r')
            else:
                chunks=[];start=time.perf_counter()
                with zipfile.ZipFile(pvzip_path) as zf:
                    for lo in range(0,len(rows),a.batch_size):
                        batch=rows[lo:lo+a.batch_size];t=torch.stack([preprocess(image_bytes(r,r['source']=='PlantVillage' and 'pv' or 'pd',zf,pdroot)) for r in batch]).to(device)
                        with torch.inference_mode():out=forward(model,t)
                        chunks.append(out.detach().float().cpu().numpy())
                elapsed=time.perf_counter()-start;z=np.concatenate(chunks)
                np.save(file,z);meta.write_text(json.dumps({'manifest_sha256':manifest_digest,'shape':list(z.shape),'dtype':str(z.dtype),'seconds':elapsed,'seconds_per_image':elapsed/len(rows),'hardware':str(device),'weights':weight_source},indent=2)+'\n')
                timings[f'{name}:{split}']={'seconds':elapsed,'seconds_per_image':elapsed/len(rows),'n':len(rows)}
            cache[split]=np.asarray(z)
        xpv=cache['PlantVillage_train'];xft=cache['field_train_unique'][field_ix];xtrain=np.concatenate([xpv,xft]);xval=cache['field_val']
        chosen={};direct_models={};crop_models={}
        for C in C_GRID:
            m=fit_direct(xtrain,train_y,C);p=direct_probs(m,xval,38);score=f1_score(fv_y,p.argmax(1),labels=sorted(covered_ids),average='macro',zero_division=0)
            if C not in chosen or score>chosen[C][0]:chosen[C]=(float(score),m)
        bestC=max(C_GRID,key=lambda C:(chosen[C][0],-C));direct_models[name]=chosen[bestC][1]
        c_scores=[]
        for C in C_GRID:
            b=fit_crop_first(xtrain,train_y,crop_names,C,classes);p,cp=crop_first_probs(b,xval,38);score=f1_score(fv_y,p.argmax(1),labels=sorted(covered_ids),average='macro',zero_division=0);c_scores.append((float(score),-C,C,b))
        _,_,cropC,crop_bundle=max(c_scores,key=lambda x:(x[0],x[1]));crop_models[name]=crop_bundle
        evaluation_bundle['field_val']=fv
        for split in ('field_val','PlantVillage test','PlantDoc external'):
            xx=cache.get(split)
            if xx is None:
                rows=evaluation_bundle[split];chunks=[]
                with zipfile.ZipFile(pvzip_path) as zf:
                    for lo in range(0,len(rows),a.batch_size):
                        batch=rows[lo:lo+a.batch_size];t=torch.stack([preprocess(image_bytes(r,'pv' if r['source']=='PlantVillage' else 'pd',zf,pdroot)) for r in batch]).to(device)
                        with torch.inference_mode():out=forward(model,t)
                        chunks.append(out.detach().float().cpu().numpy())
                xx=np.concatenate(chunks);manifest_digest=hashlib.sha256(''.join(r['sha256'] for r in rows).encode()).hexdigest();tag=name.replace('/','_').replace(' ','_').replace('-','_');file=feature_dir/f'{tag}_{split.replace(" ","_")}.npy';np.save(file,xx);file.with_suffix('.json').write_text(json.dumps({'manifest_sha256':manifest_digest,'shape':list(xx.shape),'dtype':str(xx.dtype),'seconds_per_image':None,'hardware':str(device),'weights':weight_source},indent=2)+'\n');cache[split]=xx
            rows=evaluation_bundle[split];yy=np.array([int(r['class_index']) for r in rows]);allpred={}
            for method in ('direct','crop_first'):
                probs=direct_probs(direct_models[name],xx,38) if method=='direct' else crop_first_probs(crop_models[name],xx,38)[0]
                metric=class_metrics(yy,probs.argmax(1),probs,classes,covered_ids);metric['crop_accuracy']=float(np.mean([crop_names[int(y)]==crop_names[int(p)] for y,p in zip(yy,probs.argmax(1))]));metric['tuning_set']='field_val' if split=='field_val' else None
                if split=='PlantDoc external':metric['bootstrap_95_percentile_ci']=bootstrap_ci(yy,probs,classes,crop_names)
                results[f'{name}:{method}:{split}']=metric;allpred[method]=probs
                for i,row in enumerate(rows):
                    order=np.argsort(probs[i])[::-1][:5]
                    prediction_rows.append({'backbone':name,'method':method,'split':split,'image_path':row['image_path'],'sha256':row['sha256'],'true_class':classes[int(yy[i])],'predicted_class':classes[int(order[0])],'top3_classes':'|'.join(classes[int(c)] for c in order[:3]),'model_score_not_calibrated':float(probs[i,order[0]]),'crop_correct':crop_names[int(yy[i])]==crop_names[int(order[0])]})
            if split=='field_val':results[f'{name}:selected_C']={'direct_C':float(bestC),'direct_field_val_covered_macro_f1':chosen[bestC][0],'crop_first_C':float(cropC),'crop_first_field_val_covered_macro_f1':float(max(c_scores)[0])}
        del model
    protected_after=manifest_hashes(pd_eval,'image_path',pdroot)
    if protected_before!=protected_after:raise RuntimeError('Protected PlantDoc hashes changed during bake-off')
    for label,records in (('before',protected_before),('after',protected_after)):
        with (run/f'protected_hashes_{label}.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['image_path','sha256']);w.writeheader();w.writerows(records)
    if prediction_rows:
        with (run/'predictions.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(prediction_rows[0]));w.writeheader();w.writerows(prediction_rows)
    output={'environment':env,'model_status':model_status,'feature_timings':timings,'metrics':results,'protected_hashes_unchanged':protected_before==protected_after,'seed':SEED,'C_candidates':list(C_GRID),'evaluation_design':'field_val-only C selection; protected PlantDoc and PlantVillage test used only for final metrics after fitting','feature_cache_dir':str(feature_dir)}
    (run/'bakeoff_results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'run_dir':str(run),'model_status':model_status,'metric_rows':len(results)},indent=2))
if __name__=='__main__':main()
