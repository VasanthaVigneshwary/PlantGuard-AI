"""Hash inventory and duplicate screen for unlabeled/excluded local image folders."""
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
EXP=Path(__file__).resolve().parent
POPCOUNT=np.array([i.bit_count() for i in range(256)],dtype=np.uint8)
def phash(im):
    a=np.asarray(im.convert('L').resize((32,32),Image.Resampling.LANCZOS),dtype=np.float64); x=np.arange(32);u=np.arange(8)[:,None]
    d=np.cos((math.pi/32)*(x+.5)*u);d[0]*=1/math.sqrt(2);d*=math.sqrt(2/32);low=(d@a@d.T)[:8,:8].reshape(-1)[1:]; med=np.median(low); h=0
    for b in low>med:h=(h<<1)|int(b)
    return h
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--project-root',required=True,type=Path);a=ap.parse_args();root=a.project_root.resolve()
    outputs=[EXP/'local_unusable_source_hashes.csv',EXP/'local_unusable_source_overlap_audit.csv',EXP/'local_unusable_source_audit.json']
    if any(p.exists() for p in outputs):raise FileExistsError('Refusing to overwrite an existing local-source audit')
    sources=[]
    for name,folder in [('backend_uploads',root/'backend/uploads'),('test_images_fixture',root/'test_images')]:
        if folder.exists():
            sources.extend((name,p) for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'})
    if not sources:raise RuntimeError('No excluded local source images found')
    inventory=[]
    for source,p in sources:
        error=''
        try:
            with Image.open(p) as im:h=phash(ImageOps.exif_transpose(im))
            ph=f'{h:016X}'
        except Exception as e:ph='';error=f'{type(e).__name__}: {e}'
        inventory.append({'source':source,'image_path':p.relative_to(root).as_posix(),'sha256':digest(p),'phash':ph,'decode_error':error})
    protected=list(csv.DictReader((EXP/'protected_plantdoc_evaluation.csv').open(encoding='utf-8-sig')))
    field=list(csv.DictReader((EXP/'field_train.csv').open(encoding='utf-8-sig')))+list(csv.DictReader((EXP/'field_val.csv').open(encoding='utf-8-sig')))
    pv=list(csv.DictReader((EXP/'plantvillage_train_filtered.csv').open(encoding='utf-8-sig')))
    partial=[p for p in (root/'datasets/plantdoc-partial-extract').rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'}]
    refs=[]
    for label,records,pathkey in [('PlantDoc protected evaluation',protected,'image_path'),('PlantDoc mapped candidates',field,'image_path'),('PlantVillage train',pv,'archive_member')]:
        refs.extend({'source':label,'path':r[pathkey],'sha256':r['sha256'],'phash':int(r['phash'],16)} for r in records)
    for p in partial:
        with Image.open(p) as im:h=phash(ImageOps.exif_transpose(im))
        refs.append({'source':'PlantDoc partial extract','path':p.relative_to(root).as_posix(),'sha256':digest(p),'phash':h})
    refs.extend({'source':r['source'],'path':r['image_path'],'sha256':r['sha256'],'phash':int(r['phash'],16) if r['phash'] else None} for r in inventory)
    audit=[]
    for r in inventory:
        for q in refs:
            if q['path']==r['image_path']:continue
            dist=(int(r['phash'],16)^int(q['phash'])).bit_count() if r['phash'] and q['phash'] is not None else None
            if r['sha256']==q['sha256'] or (dist is not None and dist<=6):
                audit.append({'image_path':r['image_path'],'source':r['source'],'sha256':r['sha256'],'phash':r['phash'],'matched_image':q['path'],'matched_source':q['source'],'matched_sha256':q['sha256'],'matched_phash':f"{q['phash']:016X}" if q['phash'] is not None else '', 'hamming_distance':dist,'reason':'exact SHA-256' if r['sha256']==q['sha256'] else 'pHash Hamming distance <=6','decision':'excluded_unlabeled_source'})
    def write(p,rows):
        fields=list(rows[0]) if rows else []
        with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write(outputs[0],inventory);write(outputs[1],audit)
    summary={'source_images':len(inventory),'source_counts':{s:sum(r['source']==s for r in inventory) for s,_ in sources},'decode_failures':sum(bool(r['decode_error']) for r in inventory),'reference_counts':{'PlantDoc protected evaluation':len(protected),'PlantDoc mapped train_and_validation':len(field),'PlantVillage train':len(pv),'PlantDoc partial extract':len(partial)},'overlap_records':len(audit),'distinct_source_images_with_match':len({r['image_path'] for r in audit}),'threshold_hamming':6,'all_inventory_sha256_computed':True,'pHash_computed_for_decodable_files':sum(bool(r['phash']) for r in inventory),'unlabeled_sources_used_for_training':0}
    outputs[2].write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
