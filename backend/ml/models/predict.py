import numpy as np
import tensorflow as tf
from PIL import Image

MODEL_PATH = "ml/models/plant_disease_efficientnet.keras"
CLASS_NAMES_PATH = "ml/models/class_names.txt"

model = tf.keras.models.load_model(MODEL_PATH)

class_names = []

with open(CLASS_NAMES_PATH, "r") as file:
    for line in file:
        line = line.strip()

        if line:
            class_name = line.split(": ", 1)[1]
            class_names.append(class_name)


def predict_disease(image_path):

    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))

    image_array = np.array(image, dtype=np.float32)
    image_array = image_array / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array, verbose=0)

    predicted_index = int(np.argmax(predictions[0]))
    confidence = float(predictions[0][predicted_index])

    predicted_class = class_names[predicted_index]

    confidence_percentage = round(confidence * 100, 2)

if confidence_percentage >= 70:
    status = "Confident prediction"
elif confidence_percentage >= 50:
    status = "Possible prediction"
else:
    status = "Low confidence"

return {
    "disease": predicted_class,
    "confidence": confidence_percentage,
    "status": status
}