"""Export the experiment best checkpoint only; never targets production artifacts."""
import argparse, json
from pathlib import Path
import torch
from torch import nn
from torchvision import models

EXP=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(); p.add_argument('--checkpoint',type=Path,default=EXP/'training/best.pt'); a=p.parse_args()
    out=EXP/'export'; out.mkdir(parents=True,exist_ok=True)
    model_path=out/'efficientnet_v2_s_realworld.onnx'
    if model_path.exists(): raise FileExistsError(f'Refusing to overwrite {model_path}')
    classes=json.loads((EXP/'classes.json').read_text(encoding='utf-8'))['classes']
    ckpt=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    if len(classes)!=38 or ckpt.get('config',{}).get('classes')!=classes: raise RuntimeError('Checkpoint class order differs from the approved 38-class mapping')
    model=models.efficientnet_v2_s(weights=None); model.classifier[1]=nn.Linear(model.classifier[1].in_features,38)
    model.load_state_dict(ckpt['model_state'],strict=True); model.eval()
    x=torch.zeros(2,3,224,224,dtype=torch.float32)
    torch.onnx.export(model,x,str(model_path),opset_version=17,input_names=['input'],output_names=['logits'],
      dynamic_axes={'input':{0:'batch'},'logits':{0:'batch'}},external_data=True,dynamo=False)
    import onnx
    graph=onnx.load(str(model_path),load_external_data=True); onnx.checker.check_model(graph)
    result={'model':str(model_path),'opset':17,'input_names':[x.name for x in graph.graph.input],
      'output_names':[x.name for x in graph.graph.output],'classes':len(classes),'checkpoint':str(a.checkpoint)}
    (out/'export_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,indent=2))
if __name__=='__main__':main()
