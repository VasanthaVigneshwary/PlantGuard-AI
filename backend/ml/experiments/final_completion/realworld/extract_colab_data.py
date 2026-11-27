"""Extracts only hash-verified manifest members to local Colab storage; no source writes."""
import argparse,csv,hashlib,json,shutil,zipfile
from pathlib import Path
EXP=Path(__file__).resolve().parent
PROJECT_DEFAULT=EXP.parents[4]
def sha_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def csv_rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def safe_target(root,rel):
 p=(root/rel).resolve()
 if root.resolve() not in p.parents: raise ValueError(f'Unsafe archive path: {rel}')
 return p
def extract_member(z,member,target,expected):
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():
  if sha_file(target)==expected:return
  raise FileExistsError(f'Existing extracted file hash differs; refusing overwrite: {target}')
 temp=target.with_suffix(target.suffix+'.partial'); h=hashlib.sha256()
 with z.open(member) as src,temp.open('wb') as dst:
  for b in iter(lambda:src.read(1024*1024),b''): h.update(b);dst.write(b)
 if h.hexdigest()!=expected: temp.unlink(missing_ok=True);raise RuntimeError(f'Archive image hash mismatch: {member}')
 temp.replace(target)
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--project-root',type=Path,required=True);ap.add_argument('--output-root',type=Path,default=Path('/content/plantguard-data'))
 ap.add_argument('--plantvillage-zip',type=Path);ap.add_argument('--plantdoc-zip',type=Path);ap.add_argument('--include-evaluation',action='store_true')
 a=ap.parse_args(); project=a.project_root.resolve(); out=a.output_root.resolve()
 pvzip=(a.plantvillage_zip or project/'datasets/plantvillage-source.zip').resolve(); pdzip=(a.plantdoc_zip or project/'datasets/plantdoc-source.zip').resolve()
 if out.exists() and any(out.iterdir()) and not a.include_evaluation: raise FileExistsError(f'Output root is non-empty; reuse it only with --include-evaluation for the final evaluation extraction: {out}')
 out.mkdir(parents=True,exist_ok=True)
 pv_rows=csv_rows(EXP/'plantvillage_train_filtered.csv'); field=csv_rows(EXP/'field_train.csv')+csv_rows(EXP/'field_val.csv')
 if a.include_evaluation:
  pv_rows+=csv_rows(project/'backend/ml/experiments/stage3_preflight/plantvillage_test.csv')
  pred=csv_rows(project/'backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv')
  field += [{'image_path':r['image_path'],'sha256':r['sha256'],'source':'PlantDoc'} for r in pred if r['metric_eligible'].lower()=='true']
 source_rows=[json.loads(x) for x in (project/'datasets/plantdoc/manifest.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
 pd_by_path={r['image_path']:r['source_archive_path'] for r in source_rows}
 pv_count=pd_count=0
 with zipfile.ZipFile(pvzip) as pvz:
  members=set(pvz.namelist())
  for r in pv_rows:
   member=r.get('archive_member',r.get('member'))
   if not member or member not in members: raise FileNotFoundError(f'PlantVillage ZIP member missing: {member}')
   target=safe_target(out/'plantvillage',member)
   extract_member(pvz,member,target,r['sha256']);pv_count+=1
 with zipfile.ZipFile(pdzip) as pdz:
  members=set(pdz.namelist())
  for r in field:
   member=pd_by_path.get(r['image_path'])
   if not member or member not in members: raise FileNotFoundError(f'PlantDoc archive member missing: {r["image_path"]} => {member}')
   target=safe_target(out/'plantdoc',r['image_path'])
   extract_member(pdz,member,target,r['sha256']);pd_count+=1
 summary={'output_root':str(out),'plantvillage_files_verified':pv_count,'plantdoc_files_verified':pd_count,'evaluation_members_included':bool(a.include_evaluation),
          'plantvillage_zip':str(pvzip),'plantdoc_zip':str(pdzip),'sha256_verified':True}
 (out/'extraction_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
