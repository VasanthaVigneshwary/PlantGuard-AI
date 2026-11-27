"""Evaluate production and experiment ONNX identically; manual post-training only."""
import argparse,csv,hashlib,json,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from sklearn.metrics import accuracy_score,confusion_matrix,precision_recall_fscore_support,top_k_accuracy_score
EXP=Path(__file__).resolve().parent
MEAN=np.array([.485,.456,.406],np.float32); STD=np.array([.229,.224,.225],np.float32)
def rows_csv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def load_tensor(path):
    with Image.open(path) as im: a=np.asarray(ImageOps.exif_transpose(im).convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32)/255.0
    return np.transpose((a-MEAN)/STD,(2,0,1)).astype(np.float32)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True,type=Path); ap.add_argument('--data-root',type=Path,default=Path('/content/plantguard-data')); ap.add_argument('--onnx',type=Path,default=EXP/'export/efficientnet_v2_s_realworld.onnx'); ap.add_argument('--providers',nargs='+',default=['CUDAExecutionProvider','CPUExecutionProvider']); a=ap.parse_args()
    import onnxruntime as ort
    classes=json.loads((EXP/'classes.json').read_text(encoding='utf-8'))['classes']; n=len(classes)
    if n!=38: raise RuntimeError('Expected unchanged 38-class map')
    old=a.project_root/'backend/ml/models/efficientnet_v2_s_best.onnx'; new=a.onnx
    production_classes=json.loads((a.project_root/'backend/ml/models/classes.json').read_text(encoding='utf-8'))['classes']
    if production_classes!=classes: raise RuntimeError('Production and experiment class order differs')
    if not old.is_file() or not Path(str(old)+'.data').is_file(): raise FileNotFoundError('Production ONNX graph or external tensor file missing')
    if not new.is_file(): raise FileNotFoundError(new)
    run=EXP/'evaluation'/datetime.now(timezone.utc).strftime('run_%Y%m%dT%H%M%SZ'); run.mkdir(parents=True,exist_ok=False)
    # Pick the uncertainty threshold using field_val only: highest coverage with >=95% selective accuracy.
    fv=rows_csv(EXP/'field_val.csv'); val_paths=[a.data_root/'plantdoc'/r['image_path'] for r in fv]
    val_y=np.array([int(r['class_index']) for r in fv]); val_x=np.stack([load_tensor(p) for p in val_paths])
    sessions={}
    for name,path in [('old',old),('new',new)]:
        opts=ort.SessionOptions(); opts.enable_profiling=True; opts.profile_file_prefix=str(run/f'{name}_profile')
        sessions[name]=ort.InferenceSession(str(path),sess_options=opts,providers=a.providers)
    def infer(sess,x):
        if [z.name for z in sess.get_inputs()]!=['input'] or [z.name for z in sess.get_outputs()]!=['logits']: raise RuntimeError('ONNX input/output names differ from contract')
        out=[]
        for i in range(0,len(x),64):out.extend(sess.run(['logits'],{'input':x[i:i+64]})[0])
        out=np.asarray(out,dtype=np.float32)
        if out.shape!=(len(x),38):raise RuntimeError(f'Expected [N,38], got {out.shape}')
        return out
    def scores(logits):
        z=logits-logits.max(1,keepdims=True); p=np.exp(z); return p/p.sum(1,keepdims=True)
    val_prob={m:scores(infer(s,val_x)) for m,s in sessions.items()}
    thresholds={}; curve=[]
    for m,p in val_prob.items():
        conf=p.max(1); pred=p.argmax(1); cand=sorted(set(conf.tolist()))+[1.000001]
        for t in cand:
            covered=conf>=t; ncovered=int(covered.sum())
            curve.append({'model':m,'threshold_model_score_not_calibrated_probability':float(t),'covered':ncovered,'coverage':float(covered.mean()),'selective_accuracy':float((pred[covered]==val_y[covered]).mean()) if ncovered else None})
        valid=[(float((conf>=t).mean()),float((pred[conf>=t]==val_y[conf>=t]).mean()),float(t)) for t in cand if np.any(conf>=t) and float((pred[conf>=t]==val_y[conf>=t]).mean())>=.95]
        thresholds[m]=max(valid,key=lambda x:(x[0],x[2]))[2] if valid else 1.000001
    with (run/'field_val_accuracy_coverage.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(curve[0]));w.writeheader();w.writerows(curve)
    pv=rows_csv(a.project_root/'backend/ml/experiments/stage3_preflight/plantvillage_test.csv')
    predrows=rows_csv(a.project_root/'backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv')
    pd=[r for r in predrows if r['metric_eligible'].lower()=='true']
    if len(pd)!=123:raise RuntimeError(f'Expected exactly 123 protected PlantDoc eval images, found {len(pd)}')
    datasets={'field_val':[(r,a.data_root/'plantdoc'/r['image_path'],int(r['class_index']),r['class_name']) for r in fv],
      'plantvillage_test':[(r,a.data_root/'plantvillage'/r['member'],classes.index(r['class_name']),r['class_name']) for r in pv],
      'plantdoc_external':[(r,a.data_root/'plantdoc'/r['image_path'],classes.index(r['mapped_true_class']),r['mapped_true_class']) for r in pd]}
    summary={'classes':classes,'thresholds_selected_on_field_val_only':thresholds,'threshold_rule':'maximize coverage subject to >=95% accuracy among covered validation samples; scores are raw softmax model scores, not calibrated probabilities','sessions':{m:{'requested_providers':a.providers,'active_providers':s.get_providers()} for m,s in sessions.items()},'datasets':{}}
    comparisons=[]
    for dsname,items in datasets.items():
        yy=np.array([x[2] for x in items]); names=[x[3] for x in items]
        if len(yy)==0:raise RuntimeError(f'Empty dataset {dsname}')
        valid_items=[]; tensors=[]; failures=[]
        for item in items:
            r,path,y,cls=item
            try:
                if not path.is_file(): raise FileNotFoundError(path)
                actual=sha(path); expected=r.get('sha256','')
                if expected and actual!=expected: raise RuntimeError(f'SHA-256 mismatch: expected {expected}, got {actual}')
                tensors.append(load_tensor(path)); valid_items.append((r,path,y,cls,actual))
            except Exception as e: failures.append({'image_path':r.get('image_path',r.get('member','')),'error':f'{type(e).__name__}: {e}'})
        if not valid_items: raise RuntimeError(f'No valid images for {dsname}; see generated failure report')
        yy=np.array([x[2] for x in valid_items]); xx=np.stack(tensors)
        summary['datasets'][dsname]={'requested_support':len(items),'support':len(yy),'class_support':{classes[i]:int(np.sum(yy==i)) for i in range(n)},'image_hashes_verified':len(valid_items),'inference_or_load_failures':len(failures)}
        (run/f'{dsname}_inference_failures.json').write_text(json.dumps(failures,indent=2)+'\n')
        (run/f'{dsname}_image_hash_verification.json').write_text(json.dumps({'requested':len(items),'verified':len(valid_items),'failures':len(failures),'status':'PASS' if len(valid_items)==len(items) else 'PARTIAL'},indent=2)+'\n')
        for m,sess in sessions.items():
            try: logits=infer(sess,xx)
            except Exception as e:
                failed=[{'image_path':x[0].get('image_path',x[0].get('member','')),'error':f'{type(e).__name__}: batch inference failed: {e}'} for x in valid_items]
                (run/f'{dsname}_{m}_inference_failures.json').write_text(json.dumps(failed,indent=2)+'\n'); summary['datasets'][dsname][m]={'status':'FAILED','error':str(e)}; continue
            probs=scores(logits); pred=probs.argmax(1); conf=probs.max(1); cm=confusion_matrix(yy,pred,labels=range(n))
            pr,rc,f1,sup=precision_recall_fscore_support(yy,pred,labels=range(n),zero_division=0)
            eligible=conf>=thresholds[m]; metrics={'support':len(yy),'accuracy_top1':float(accuracy_score(yy,pred)),'accuracy_top3':float(top_k_accuracy_score(yy,probs,k=3,labels=range(n))),
              'macro_precision':float(pr.mean()),'macro_recall':float(rc.mean()),'macro_f1':float(f1.mean()),'weighted_f1':float(np.average(f1,weights=sup)),'uncertain_rate':float((~eligible).mean()),'accuracy_at_coverage':float((pred[eligible]==yy[eligible]).mean()) if eligible.any() else None,'coverage':float(eligible.mean()),'threshold':thresholds[m],
              'per_class':{classes[i]:{'support':int(sup[i]),'precision':float(pr[i]),'recall':float(rc[i]),'f1':float(f1[i])} for i in range(n)}}
            pair_counts=Counter((classes[int(yy[i])],classes[int(pred[i])]) for i in range(len(yy)) if yy[i]!=pred[i])
            metrics['top_confused_pairs']=[{'true_class':k[0],'predicted_class':k[1],'count':v} for k,v in pair_counts.most_common(20)]
            tag=f'{dsname}_{m}'; (run/f'{tag}_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');
            with (run/f'{tag}_confusion_matrix.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.writer(f);w.writerow(['true_class']+classes);w.writerows([[classes[i],*cm[i].tolist()] for i in range(n)])
            with (run/f'{tag}_predictions.csv').open('w',newline='',encoding='utf-8') as f:
                fields=['image_path','true_class','predicted_class','model_score_not_calibrated_probability','uncertain','sha256','top3'] ; w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
                for i,(r,path,y,cls,digest) in enumerate(valid_items):w.writerow({'image_path':r.get('image_path',r.get('member','')),'true_class':classes[y],'predicted_class':classes[pred[i]],'model_score_not_calibrated_probability':float(conf[i]),'uncertain':bool(not eligible[i]),'sha256':digest,'top3':'|'.join(classes[j] for j in np.argsort(probs[i])[-3:][::-1])})
            summary['datasets'][dsname][m]=metrics; comparisons.append({'dataset':dsname,'model':m,'top1':metrics['accuracy_top1'],'top3':metrics['accuracy_top3'],'macro_f1':metrics['macro_f1'],'weighted_f1':metrics['weighted_f1'],'coverage':metrics['coverage']})
    for model_name,sess in sessions.items():
        profile=Path(sess.end_profiling()); events=json.loads(profile.read_text(encoding='utf-8'))
        node_events=[e for e in events if e.get('cat')=='Node']
        cuda_nodes=sum(e.get('args',{}).get('provider')=='CUDAExecutionProvider' for e in node_events)
        target=run/f'{model_name}_onnxruntime_profile.json'
        if profile!=target: profile.replace(target)
        summary['sessions'][model_name].update({'profile_file':target.name,'profile_node_events':len(node_events),'cuda_node_events':cuda_nodes,'cuda_execution_verified':cuda_nodes>0})
    (run/'evaluation.json').write_text(json.dumps(summary,indent=2)+'\n');
    with (run/'old_vs_new_comparison.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
    print(json.dumps({'run_dir':str(run),'datasets':{k:v['support'] for k,v in summary['datasets'].items()},'thresholds':thresholds,'providers':summary['sessions']},indent=2))
if __name__=='__main__':main()
