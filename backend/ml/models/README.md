# Plant disease model artifacts

## Active ONNX model

`predict.py` loads `efficientnet_v2_s_best.onnx` with ONNX Runtime and requires
the adjacent `efficientnet_v2_s_best.onnx.data` external tensor file. Keep the
two files together. The ONNX graph declares a float input shaped
`[batch, 3, 224, 224]` and a 38-value output named `logits`. It has no embedded
preprocessing nodes; inference converts the image to RGB, resizes it to 224 by
224, scales pixels to `[0, 1]`, then applies ImageNet channel mean and standard
deviation normalization.

`classes.json` lists the 38 output labels in model-index order. The order agrees
with `class_names.txt`. The filenames and class mapping match the model card at
[`BiernyVR/crop-disease-classifier`](https://huggingface.co/BiernyVR/crop-disease-classifier),
which identifies the model as an EfficientNetV2-S trained on PlantVillage and
the repository license as MIT. The model card reports 99.89% validation
accuracy, but that result has not been independently reproduced here and does
not establish performance on field photographs. Do not present the ONNX model's
softmax score as calibrated confidence or report the card's accuracy as a local
evaluation result.

The included `test_images/sample_leaf.jpg` is also listed by that model card as
an Apple scab sample. It is useful for a loading/inference smoke check only; it
is not an independent validation image. The other checked-in webp fixture has
no known ground-truth label, so neither fixture is used to calculate accuracy.

## Legacy Keras artifact

`plant_disease_efficientnet.keras` and the accompanying model description are
retained from an earlier project version. The description attributes that
artifact to PlantVillage and reports 41.68% on 511 images. Those figures apply
only to that stated Keras evaluation; they have not been verified for the active
ONNX model.
