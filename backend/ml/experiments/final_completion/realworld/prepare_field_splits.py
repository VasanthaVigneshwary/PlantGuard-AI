"""Leakage-controlled local inventory/split builder; never writes source datasets/manifests."""
from __future__ import annotations
import csv, hashlib, json, math, random, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
SEED = 20261127
MAX_PHASH_DISTANCE = 6
PV_TRAIN = ROOT / 'backend/ml/experiments/stage3_preflight/plantvillage_train.csv'
FIELD_CANDIDATES = ROOT / 'backend/ml/experiments/stage2_dataset/manifest.csv'
PLANTDOC_MANIFEST = ROOT / 'datasets/plantdoc/manifest.jsonl'
PLANTDOC_PREDICTIONS = ROOT / 'backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv'
PV_ZIP = ROOT / 'datasets/plantvillage-source.zip'
PLANTDOC_ROOT = ROOT / 'datasets/plantdoc'
CLASSES_PATH = ROOT / 'backend/ml/models/classes.json'

# Same 64-bit DCT pHash definition as the existing Stage 4 PlantDoc audit.
def phash(image: Image.Image) -> int:
    a=np.asarray(image.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=np.float64)
    x=np.arange(32,dtype=np.float64); u=np.arange(8,dtype=np.float64)[:,None]
    d=np.cos((math.pi/32.0)*(x+0.5)*u); d[0]*=1.0/math.sqrt(2.0); d*=math.sqrt(2.0/32.0)
    low=(d@a@d.T)[:8,:8].reshape(-1)[1:]; med=float(np.median(low)); result=0
    for bit in low>med: result=(result<<1)|int(bit)
    return result

POPCOUNT=np.array([i.bit_count() for i in range(256)],dtype=np.uint8)
def distances(value:int, refs:np.ndarray)->np.ndarray:
    if len(refs)==0: return np.empty(0,dtype=np.uint8)
    xor=np.bitwise_xor(refs,np.uint64(value))
    return POPCOUNT[xor.view(np.uint8).reshape(-1,8)].sum(axis=1,dtype=np.uint16)
def sha_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def write_csv_new(path:Path, fields:list[str], rows:list[dict])->None:
    if path.exists(): raise FileExistsError(f'Refusing to overwrite existing evidence: {path}')
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def rel(p:Path)->str: return p.relative_to(ROOT).as_posix()

classes_meta=json.loads(CLASSES_PATH.read_text(encoding='utf-8')); classes=classes_meta['classes']
if len(classes)!=38 or len(set(classes))!=38: raise RuntimeError('Expected the unchanged unique 38-class order')
class_index={name:i for i,name in enumerate(classes)}
for output in ['field_train.csv','field_val.csv','plantvillage_train_filtered.csv','leakage_audit.csv','field_class_counts.csv','split_summary.json','source_inventory.json','protected_plantdoc_evaluation.csv','classes.json']:
    if (OUT/output).exists(): raise FileExistsError(f'Refusing to overwrite existing realworld artifact: {OUT/output}')

# Reuse the completed PlantDoc 123-image eligibility decisions and per-image hashes.
pred_rows=list(csv.DictReader(PLANTDOC_PREDICTIONS.open(encoding='utf-8-sig')))
eval_rows=[r for r in pred_rows if r['metric_eligible'].lower()=='true']
if len(eval_rows)!=123: raise RuntimeError(f'Expected the preserved 123-image PlantDoc evaluation set; found {len(eval_rows)}')
protected=[]
for r in eval_rows:
    path=PLANTDOC_ROOT/r['image_path']
    if not path.is_file(): raise FileNotFoundError(path)
    raw=path.read_bytes(); digest=sha_bytes(raw)
    if digest!=r['sha256']: raise RuntimeError(f'PlantDoc evaluation hash mismatch: {r["image_path"]}')
    with Image.open(path) as im: h=phash(ImageOps.exif_transpose(im))
    protected.append({'path':r['image_path'],'sha256':digest,'phash':f'{h:016X}','class_name':r['mapped_true_class']})
eval_hashes={r['sha256'] for r in protected}
eval_phashes=np.asarray([int(r['phash'],16) for r in protected],dtype=np.uint64)

# PlantDoc candidate pool is restricted to original source train rows and exact approved mappings.
source_manifest=[json.loads(line) for line in PLANTDOC_MANIFEST.read_text(encoding='utf-8').splitlines() if line.strip()]
source_by_path={r['image_path']:r for r in source_manifest}
candidate_rows=list(csv.DictReader(FIELD_CANDIDATES.open(encoding='utf-8-sig')))
candidates=[]
for r in candidate_rows:
    if r['source_split']!='train': continue
    if r['target_class'] not in class_index: raise RuntimeError('Stage 2 candidate contains an unapproved class')
    path=ROOT/r['image_path']
    src=source_by_path.get(path.relative_to(PLANTDOC_ROOT).as_posix())
    if not path.is_file() or not src: raise FileNotFoundError(f'PlantDoc candidate absent from source manifest: {path}')
    raw=path.read_bytes(); digest=sha_bytes(raw)
    if digest!=r['sha256'] or digest!=src['sha256']: raise RuntimeError(f'PlantDoc candidate hash mismatch: {path}')
    with Image.open(path) as im: h=phash(ImageOps.exif_transpose(im))
    candidates.append({'image_path':r['image_path'],'source':'PlantDoc','source_label':r['source_label'],'class_name':r['target_class'],'sha256':digest,'phash':h})
if len(candidates)!=1346: raise RuntimeError(f'Expected 1,346 mapped PlantDoc training candidates; found {len(candidates)}')

# Build or resume a verified pHash cache for the fixed PlantVillage training manifest only.
pv_rows=list(csv.DictReader(PV_TRAIN.open(encoding='utf-8-sig')))
if len(pv_rows)!=37993 or {r['split'] for r in pv_rows}!={'train'}: raise RuntimeError('PlantVillage train manifest differs from the verified 37,993-row train split')
pv_manifest_sha=sha_bytes(PV_TRAIN.read_bytes())
cache_path=OUT/'plantvillage_train_phashes.csv'; cache_meta=OUT/'plantvillage_train_phashes.meta.json'
if cache_path.exists() or cache_meta.exists():
    if not (cache_path.exists() and cache_meta.exists()): raise RuntimeError('Incomplete pHash cache pair; preserve and inspect before resuming')
    meta=json.loads(cache_meta.read_text(encoding='utf-8'))
    if meta.get('manifest_sha256')!=pv_manifest_sha: raise RuntimeError('Existing pHash cache belongs to a different train manifest')
    cache={r['member']:{'sha256':r['sha256'],'phash':int(r['phash'],16)} for r in csv.DictReader(cache_path.open(encoding='utf-8-sig'))}
    if not set(cache).issubset({r['member'] for r in pv_rows}): raise RuntimeError('pHash cache has unknown archive members')
else:
    cache={}
    cache_meta.write_text(json.dumps({'manifest_sha256':pv_manifest_sha,'algorithm':'64-bit DCT pHash, grayscale Lanczos 32x32, low 8x8 excluding DC','resume_safe':True},indent=2)+'\n',encoding='utf-8')
    with cache_path.open('w',encoding='utf-8',newline='') as f: csv.writer(f).writerow(['member','sha256','phash'])
missing=[r for r in pv_rows if r['member'] not in cache]
if missing:
    mode='a' if cache_path.stat().st_size>0 else 'w'
    with zipfile.ZipFile(PV_ZIP) as z, cache_path.open(mode,encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        for i,r in enumerate(missing,1):
            raw=z.read(r['member']); digest=sha_bytes(raw)
            if digest!=r['sha256']: raise RuntimeError(f'PlantVillage train image SHA mismatch: {r["member"]}')
            with Image.open(__import__('io').BytesIO(raw)) as im: h=phash(ImageOps.exif_transpose(im))
            writer.writerow([r['member'],digest,f'{h:016X}']); cache[r['member']]={'sha256':digest,'phash':h}
            if i%1000==0: f.flush(); print(f'PlantVillage pHash {i}/{len(missing)}',flush=True)
    if len(cache)!=len(pv_rows): raise RuntimeError('PlantVillage pHash cache is incomplete')

# Protect the PlantDoc evaluation images from every training and validation source.
leak_fields=['image_path','source','class_name','sha256','phash','matched_image','matched_sha256','matched_phash','hamming_distance','exclusion_reason','decision']
audit=[]
def audit_row(path,source,cls,digest,h,matched,reason,decision='excluded'):
    audit.append({'image_path':path,'source':source,'class_name':cls,'sha256':digest,'phash':f'{h:016X}' if isinstance(h,int) else h,
      'matched_image':matched.get('path','') if matched else '', 'matched_sha256':matched.get('sha256','') if matched else '',
      'matched_phash':matched.get('phash','') if matched else '', 'hamming_distance':matched.get('distance','') if matched else '',
      'exclusion_reason':reason,'decision':decision})
# Identify PlantVillage train records matching any of the 123 protected eval images.
pv_eval_excluded=set(); pv_kept=[]
for r in pv_rows:
    item=cache[r['member']]; h=item['phash']; digest=item['sha256']
    ds=distances(h,eval_phashes); hits=np.flatnonzero(ds<=MAX_PHASH_DISTANCE)
    exact_eval=next((e for e in protected if e['sha256']==digest),None)
    if exact_eval is not None or len(hits):
        pv_eval_excluded.add(r['member'])
        matched=exact_eval or {**protected[int(hits[0])],'distance':int(ds[hits[0]])}
        if exact_eval: matched={**exact_eval,'distance':0}
        audit_row(r['member'],'PlantVillage',r['class_name'],digest,h,matched,'exact or pHash<=6 duplicate of protected PlantDoc evaluation image')
    else: pv_kept.append({**r,'phash':h,'sha256':digest})
pv_hashes={r['sha256'] for r in pv_kept}
pv_phashes=np.asarray([r['phash'] for r in pv_kept],dtype=np.uint64)

# Exclude field images that overlap protected PlantDoc evaluation or retained PlantVillage training.
field_keep=[]
for c in candidates:
    exact=next((e for e in protected if e['sha256']==c['sha256']),None)
    ds=distances(c['phash'],eval_phashes); hits=np.flatnonzero(ds<=MAX_PHASH_DISTANCE)
    if exact or len(hits):
        m=exact or {**protected[int(hits[0])],'distance':int(ds[hits[0]])}
        if exact: m={**exact,'distance':0}
        audit_row(c['image_path'],'PlantDoc',c['class_name'],c['sha256'],c['phash'],m,'exact or pHash<=6 duplicate of protected PlantDoc evaluation image')
        continue
    exact_pv=next((r for r in pv_kept if r['sha256']==c['sha256']),None)
    ds_pv=distances(c['phash'],pv_phashes); pv_hits=np.flatnonzero(ds_pv<=MAX_PHASH_DISTANCE)
    if exact_pv or len(pv_hits):
        hit=exact_pv or pv_kept[int(pv_hits[0])]
        m={'path':hit['member'],'sha256':hit['sha256'],'phash':f'{hit["phash"]:016X}','distance':0 if exact_pv else int(ds_pv[pv_hits[0]])}
        audit_row(c['image_path'],'PlantDoc',c['class_name'],c['sha256'],c['phash'],m,'exact or pHash<=6 duplicate of retained PlantVillage training image')
        continue
    field_keep.append(c)

# Group near-duplicate field candidates (Hamming <=6); components cannot cross train/val.
parent=list(range(len(field_keep)))
def find(x):
    while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
    return x
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb: parent[rb]=ra
field_hashes=np.asarray([c['phash'] for c in field_keep],dtype=np.uint64)
for i,c in enumerate(field_keep):
    ds=distances(c['phash'],field_hashes[i+1:])
    for j in np.flatnonzero(ds<=MAX_PHASH_DISTANCE): union(i,i+1+int(j))
groups=defaultdict(list)
for i,c in enumerate(field_keep): groups[find(i)].append(c)
usable=[]; conflict_groups=0
for members in groups.values():
    labels={r['class_name'] for r in members}
    if len(labels)>1:
        conflict_groups+=1
        for c in members:
            other=next(r for r in members if r['class_name']!=c['class_name'])
            d=int(distances(c['phash'],np.asarray([other['phash']],dtype=np.uint64))[0])
            audit_row(c['image_path'],'PlantDoc',c['class_name'],c['sha256'],c['phash'],{'path':other['image_path'],'sha256':other['sha256'],'phash':f'{other["phash"]:016X}','distance':d},'near-duplicate group has conflicting class labels')
        continue
    gid=hashlib.sha256('|'.join(sorted(r['sha256'] for r in members)).encode()).hexdigest()[:16]
    for c in members: c['group_id']=gid
    if len(members)>1:
        first=members[0]
        for c in members[1:]:
            d=int(distances(c['phash'],np.asarray([first['phash']],dtype=np.uint64))[0])
            audit_row(c['image_path'],'PlantDoc',c['class_name'],c['sha256'],c['phash'],{'path':first['image_path'],'sha256':first['sha256'],'phash':f'{first["phash"]:016X}','distance':d},'within-field near-duplicate group kept together','grouped')
    usable.extend(members)

# Seeded, class-stratified group split; singleton groups stay in train and are reported.
rng=random.Random(SEED); by_class=defaultdict(list)
for c in usable: by_class[c['class_name']].append(c)
train_rows=[]; val_rows=[]; singleton_classes=[]
for cls in classes:
    cls_groups=defaultdict(list)
    for c in by_class.get(cls,[]): cls_groups[c['group_id']].append(c)
    keys=sorted(cls_groups); rng.shuffle(keys)
    if len(keys)<2:
        singleton_classes.append(cls)
        for k in keys: train_rows.extend(cls_groups[k])
        continue
    total=sum(len(cls_groups[k]) for k in keys); target=0.2*total
    best_k=min(range(1,len(keys)),key=lambda k:(abs(sum(len(cls_groups[x]) for x in keys[:k])-target),k))
    val_groups=set(keys[:best_k])
    for k in keys:
        (val_rows if k in val_groups else train_rows).extend(cls_groups[k])

def manifest_row(c):
    return {'image_path':c['image_path'],'class_index':class_index[c['class_name']],'class_name':c['class_name'],'source':'PlantDoc','sha256':c['sha256'],'phash':f'{c["phash"]:016X}','group_id':c['group_id'],'source_label':c['source_label']}
field_train=[manifest_row(c) for c in sorted(train_rows,key=lambda r:r['image_path'])]
field_val=[manifest_row(c) for c in sorted(val_rows,key=lambda r:r['image_path'])]

# Filter only the existing PlantVillage train split; validation/test manifests are never read here.
pv_filtered=[]
for r in pv_kept:
    pv_filtered.append({'image_path':r['member'],'archive_member':r['member'],'class_index':class_index[r['class_name']],'class_name':r['class_name'],'source':'PlantVillage','sha256':r['sha256'],'phash':f'{r["phash"]:016X}','variant':'raw/color'})

# Inventory all accessible sources; unlabelled or unprovenanced folders are not training inputs.
partial=list((ROOT/'datasets/plantdoc-partial-extract').rglob('*'))
partial_imgs=[p for p in partial if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}]
uploads=[p for p in (ROOT/'backend/uploads').glob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}]
label_mapping={r['source_label']:r['target_class'] for r in candidate_rows if r['source_split']=='train'}
partial_counts=Counter(p.parent.name for p in partial_imgs)
partial_mapped=Counter({})
for label,n in partial_counts.items():
    if label in label_mapping: partial_mapped[label_mapping[label]]+=n
partial_duplicate_matches=Counter()
candidate_hashes=np.asarray([c['phash'] for c in candidates],dtype=np.uint64)
for p in partial_imgs:
    raw=p.read_bytes(); digest=sha_bytes(raw)
    with Image.open(p) as im: h=phash(ImageOps.exif_transpose(im))
    label=p.parent.name; cls=label_mapping.get(label,'')
    sources=[('PlantDoc evaluation',protected,eval_phashes),
             ('PlantDoc mapped candidate',candidates,candidate_hashes),
             ('PlantVillage retained train',pv_kept,pv_phashes)]
    for name,refs,hashes in sources:
        ds=distances(h,hashes)
        for idx in np.flatnonzero(ds<=MAX_PHASH_DISTANCE):
            ref=refs[int(idx)]
            ref_path=ref.get('image_path',ref.get('member',ref.get('path','')))
            ref_phash=ref['phash'] if isinstance(ref['phash'],str) else f'{ref["phash"]:016X}'
            matched={'path':ref_path,'sha256':ref['sha256'],'phash':ref_phash,'distance':int(ds[idx])}
            audit_row(rel(p),'PlantDoc_partial_extract',cls,digest,h,matched,f'inventory-only partial extract matches {name} at pHash<=6','inventory_only_not_train')
            partial_duplicate_matches[name]+=1
pv_counts=Counter(r['class_name'] for r in pv_rows)
field_counts=Counter(c['class_name'] for c in candidates)
counts=[]
for cls in classes:
    counts.append({'class_index':class_index[cls],'class_name':cls,'plantdoc_mapped_candidates':field_counts[cls],
      'field_train':sum(r['class_name']==cls for r in field_train),'field_val':sum(r['class_name']==cls for r in field_val),
      'plantvillage_train_original':pv_counts[cls],'plantvillage_train_after_eval_exclusion':sum(r['class_name']==cls for r in pv_filtered),
      'field_train_below_10':sum(r['class_name']==cls for r in field_train)<10})

# Persist all new evidence without replacing any pre-existing file.
write_csv_new(OUT/'protected_plantdoc_evaluation.csv',['image_path','class_name','sha256','phash'],[
    {'image_path':r['path'],'class_name':r['class_name'],'sha256':r['sha256'],'phash':r['phash']} for r in protected])
write_csv_new(OUT/'field_train.csv',['image_path','class_index','class_name','source','sha256','phash','group_id','source_label'],field_train)
write_csv_new(OUT/'field_val.csv',['image_path','class_index','class_name','source','sha256','phash','group_id','source_label'],field_val)
write_csv_new(OUT/'plantvillage_train_filtered.csv',['image_path','archive_member','class_index','class_name','source','sha256','phash','variant'],pv_filtered)
write_csv_new(OUT/'leakage_audit.csv',leak_fields,audit)
write_csv_new(OUT/'field_class_counts.csv',list(counts[0]),counts)
shutil_copy=__import__('shutil').copyfile
if (OUT/'classes.json').exists(): raise FileExistsError(OUT/'classes.json')
shutil_copy(CLASSES_PATH,OUT/'classes.json')
# Source inventory / provenance is local-only; no licence is inferred where absent.
source_inventory={
 'PlantDoc':{'source':'CC BY 4.0 per local ATTRIBUTION.txt','revision':'5467f6012d78d1c446145d5f582da6096f852ae8','manifest_images':len(source_manifest),'usable_mapped_train_candidates':len(candidates),'usable_after_leakage_and_group_checks':len(usable),'field_train':len(field_train),'field_val':len(field_val),'mapped_classes':len(field_counts),'missing_manifest_files':0,'unmapped_or_ambiguous_train_images':2342-len(candidates),'evaluation_images_protected':len(protected),'class_counts_all_splits':{cls:sum(1 for r in source_manifest if label_mapping.get(r['ground_truth_label'])==cls) for cls in classes},'note':'Only original source-split=train rows from the approved 17-label mapping enter candidates.'},
 'PlantDoc_partial_extract':{'images':len(partial_imgs),'usable_for_training':0,'mapped_class_counts':{cls:partial_mapped[cls] for cls in classes},'unmapped_images':len(partial_imgs)-sum(partial_mapped.values()),'licence':'Not independently documented for this partial extraction; source relation is uncertain.'},
 'backend_uploads':{'images':len(uploads),'usable_for_training':0,'mapped_class_counts':{cls:0 for cls in classes},'licence_and_labels':'No per-image labels, provenance or licence metadata; excluded.'},
 'test_images_fixture':{'images':sum(1 for p in (ROOT/'test_images').rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}),'usable_for_training':0,'mapped_class_counts':{cls:0 for cls in classes},'licence_and_labels':'Application fixture, not admitted as field data.'},
 'PlantVillage':{'image_count':54305,'train_manifest_rows':len(pv_rows),'train_after_protected_eval_exclusion':len(pv_filtered),'class_count':38,'class_counts_train_after_filter':{cls:sum(1 for r in pv_filtered if r['class_name']==cls) for cls in classes},'source':'Existing local archive/manifests; source licence recorded as CC BY-SA 3.0 in Stage 3 report. This is lab imagery, not field data.'},
 'PlantWild':{'found_locally':False,'usable_for_training':0,'class_counts':{cls:0 for cls in classes}}}
(OUT/'source_inventory.json').write_text(json.dumps(source_inventory,indent=2)+'\n',encoding='utf-8')
summary={'seed':SEED,'phash_hamming_exclusion_threshold':MAX_PHASH_DISTANCE,'class_order_file':'classes.json','class_count':38,'plantdoc_eval_images_sealed':len(protected),'plantdoc_candidate_count':len(candidates),'field_candidates_excluded_or_grouped':len(candidates)-len(usable),'field_candidate_exact_or_near_eval_exclusions':sum('protected PlantDoc evaluation' in a['exclusion_reason'] for a in audit),'plantvillage_original_train':len(pv_rows),'plantvillage_removed_as_eval_duplicate':len(pv_eval_excluded),'plantvillage_train_filtered':len(pv_filtered),'field_train':len(field_train),'field_val':len(field_val),'field_train_fraction':len(field_train)/(len(field_train)+len(field_val)) if field_train or field_val else None,'field_val_fraction':len(field_val)/(len(field_train)+len(field_val)) if field_train or field_val else None,'field_conflicting_duplicate_groups_excluded':conflict_groups,'field_classes_with_single_group_train_only':singleton_classes,'field_classes_below_10_training_images':[r['class_name'] for r in counts if r['field_train_below_10']],'field_train_val_group_overlap':0,'manifest_rows_verified_by_sha256':len(candidates)+len(pv_rows),'evaluation_threshold_source':'The protected PlantDoc 123-image subset is not used for any train/validation operation.'}
(OUT/'split_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
