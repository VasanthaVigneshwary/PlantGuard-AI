"""Read-only bake-off readiness, split, and protected-image hash audit."""
import csv,hashlib,importlib.util,json,math,platform,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[5];REAL=BASE.parent
CLASSES=ROOT/'backend/ml/models/classes.json'
def read_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def phash(im):
    a=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=np.float64);x=np.arange(32);u=np.arange(8)[:,None]
    d=np.cos((math.pi/32)*(x+.5)*u);d[0]*=1/math.sqrt(2);d*=math.sqrt(2/32);low=(d@a@d.T)[:8,:8].reshape(-1)[1:];med=np.median(low);h=0
    for bit in low>med:h=(h<<1)|int(bit)
    return h
def manifest_hashes(rows,path_key,root):
    out=[]
    for r in rows:
        p=(root/r[path_key]).resolve()
        if not p.is_file():raise FileNotFoundError(p)
        digest=sha(p)
        if r.get('sha256') and digest!=r['sha256']:raise RuntimeError(f'SHA-256 mismatch: {p}')
        with Image.open(p) as im:im.verify()
        out.append({'image_path':r[path_key],'sha256':digest})
    return out
def write_hashes(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['image_path','sha256']);w.writeheader();w.writerows(rows)
def main():
    classes=json.loads(CLASSES.read_text(encoding='utf-8'))['classes']
    field_train=read_csv(REAL/'field_train.csv');field_val=read_csv(REAL/'field_val.csv')
    pv_train=read_csv(REAL/'plantvillage_train_filtered.csv')
    pv_test=read_csv(ROOT/'backend/ml/experiments/stage3_preflight/plantvillage_test.csv')
    pv_source_train=read_csv(ROOT/'backend/ml/experiments/stage3_preflight/plantvillage_train.csv')
    pd_pred=read_csv(ROOT/'backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv')
    protected=[r for r in pd_pred if r['metric_eligible'].lower()=='true']
    if len(classes)!=38 or len(protected)!=123 or len(field_train)!=1069 or len(field_val)!=268:raise RuntimeError('Approved class order or fixed existing manifests differ from verified artifacts')
    if {r['split'] for r in pv_source_train}!={'train'} or len(pv_source_train)!=37993:raise RuntimeError('PlantVillage source training manifest changed')
    if len(pv_test)!=8154 or {r['split'] for r in pv_test}!={'test'}:raise RuntimeError('Fixed PlantVillage test manifest changed')
    idx={c:i for i,c in enumerate(classes)}
    for r in field_train+field_val+pv_train:
        if r['class_name'] not in idx or int(r['class_index'])!=idx[r['class_name']]:raise RuntimeError(f'Class order mismatch: {r}')
    fsha={r['sha256'] for r in field_train};vsha={r['sha256'] for r in field_val};
    if fsha&vsha or {r['group_id'] for r in field_train}&{r['group_id'] for r in field_val}:raise RuntimeError('Field train/validation leakage detected')
    if {r['sha256'] for r in pv_train}&{r['sha256'] for r in pv_test}:raise RuntimeError('PlantVillage train/test exact SHA overlap')
    root_pd=ROOT/'datasets/plantdoc'
    hashes_before=manifest_hashes(protected,'image_path',root_pd)
    if any(x['mapped_true_class'] not in idx for x in protected):raise RuntimeError('Protected class mapping changed')
    train_rows=pv_train+field_train+field_val
    if any(not r.get('phash') for r in train_rows):raise RuntimeError('A training/validation manifest lacks pHash evidence')
    protected_hashes=[]
    for row in protected:
        with Image.open(root_pd/row['image_path']) as im:protected_hashes.append(phash(ImageOps.exif_transpose(im)))
    train_phashes=[int(r['phash'],16) for r in train_rows]
    sha_overlap={r['sha256'] for r in protected}&{r['sha256'] for r in train_rows}
    near_pairs=[]
    for i,query in enumerate(protected_hashes):
        best=min((query^candidate).bit_count() for candidate in train_phashes)
        if best<=6:near_pairs.append({'protected_image':protected[i]['image_path'],'best_training_validation_hamming_distance':best})
    if sha_overlap or near_pairs:raise RuntimeError(f'Protected evaluation overlap found: exact_sha={len(sha_overlap)}, pHash<=6={len(near_pairs)}')
    providers=[];model_io=None
    try:
        import onnxruntime as ort
        providers=ort.get_available_providers(); model=ROOT/'backend/ml/models/efficientnet_v2_s_best.onnx'
        session=ort.InferenceSession(str(model),providers=['CPUExecutionProvider'])
        model_io={'inputs':[{'name':x.name,'shape':x.shape,'type':x.type} for x in session.get_inputs()],
          'outputs':[{'name':x.name,'shape':x.shape,'type':x.type} for x in session.get_outputs()],'session_providers':session.get_providers()}
    except Exception as e:model_io={'error':f'{type(e).__name__}: {e}'}
    cache=Path.home()/'.cache';dino_cache=cache/'torch/hub/checkpoints';hf_cache=cache/'huggingface/hub/models--imageomics--bioclip'
    weight_paths={'DINOv2_ViT-S/14':dino_cache/'dinov2_vits14_pretrain.pth','DINOv2_ViT-B/14':dino_cache/'dinov2_vitb14_pretrain.pth'}
    cache_status={k:{'path':str(p),'cached':p.is_file()} for k,p in weight_paths.items()}
    cache_status['BioCLIP']={'path':str(hf_cache),'cached':hf_cache.exists() and any(hf_cache.rglob('open_clip_pytorch_model.bin'))}
    required=['numpy','PIL','sklearn','torch','torchvision','onnx','onnxruntime','open_clip']
    deps={name:bool(importlib.util.find_spec(name)) for name in required}
    try:
        import torch
        hardware={'torch_cuda_available':torch.cuda.is_available(),'gpu_name':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'cpu_count':__import__('os').cpu_count()}
    except Exception:hardware={'torch_cuda_available':False,'gpu_name':None,'cpu_count':__import__('os').cpu_count()}
    hashes_after=manifest_hashes(protected,'image_path',root_pd)
    if hashes_before!=hashes_after:raise RuntimeError('Protected PlantDoc image hashes changed during read-only preflight')
    run=BASE/('run_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run.mkdir(parents=True,exist_ok=False)
    write_hashes(run/'protected_hashes_before.csv',hashes_before);write_hashes(run/'protected_hashes_after.csv',hashes_after)
    pv_by_class={c:sum(r['class_name']==c for r in pv_train) for c in classes}
    field_by_class={c:sum(r['class_name']==c for r in field_train) for c in classes}
    pv_epoch=300*len(classes);field_epoch=int(np.ceil(pv_epoch*2/3));sample={'plantvillage_sampled_per_class':300,'plantvillage_total':pv_epoch,'field_total_oversampled':field_epoch,'combined_total':pv_epoch+field_epoch,'field_fraction':field_epoch/(pv_epoch+field_epoch)}
    data={'status':'PREPARATION_ONLY','timestamp_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'project_root':str(ROOT),'class_count':len(classes),'field_train_rows':len(field_train),'field_val_rows':len(field_val),'plantvillage_train_source_rows':len(pv_source_train),'plantvillage_test_rows':len(pv_test),'protected_plantdoc_eval_rows':len(protected),'field_train_class_coverage':sum(n>0 for n in field_by_class.values()),'field_train_classes_missing':[c for c,n in field_by_class.items() if n==0],'plantvillage_train_classes_missing':[c for c,n in pv_by_class.items() if n==0],'train_val_sha_overlap':0,'train_val_group_overlap':0,'plantvillage_train_test_exact_sha_overlap':0,'protected_exact_sha_overlap':len(sha_overlap),'protected_phash_le_6_training_or_validation_matches':len(near_pairs),'protected_hash_count_before':len(hashes_before),'protected_hash_count_after':len(hashes_after),'protected_hashes_unchanged':hashes_before==hashes_after,'manifest_sample_scheme':sample,'dependencies':deps,'hardware':hardware,'onnx_available_providers':providers,'production_model_io':model_io,'pretrained_cache_status':cache_status,'backbone_status':{'EfficientNetV2-S production ONNX':'BLOCKED: published graph interface exposes logits [N,38] only; current environment lacks onnx graph tooling to expose/verify penultimate tensor without a derived graph. No substitute weights used.','DINOv2 ViT-S/14':'BLOCKED: checkpoint not cached and torch/torchvision unavailable; download not attempted.','DINOv2 ViT-B/14':'BLOCKED: checkpoint not cached and torch/torchvision unavailable; download not attempted.','BioCLIP':'BLOCKED: checkpoint not cached and open_clip/torch unavailable; download not attempted.'},'feature_extraction':'NOT RUN','classifier_fitting':'NOT RUN','evaluation':'NOT RUN'}
    (run/'preflight.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print(json.dumps({'run_dir':str(run),'status':data['status'],'data_counts':{'field_train':len(field_train),'field_val':len(field_val),'pv_test':len(pv_test),'protected':len(protected)},'model_status':data['backbone_status'],'dependencies':deps,'protected_hashes_unchanged':data['protected_hashes_unchanged']},indent=2))
if __name__=='__main__':main()
