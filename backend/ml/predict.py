import numpy as np
import tensorflow as tf
from PIL import Image


# --------------------------------------------------
# MODEL SETTINGS
# --------------------------------------------------

MODEL_PATH = "ml/models/plant_disease_efficientnet.keras"
CLASS_NAMES_PATH = "ml/models/class_names.txt"


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("Loading Plant Guard AI model...")

model = tf.keras.models.load_model(MODEL_PATH)


# --------------------------------------------------
# LOAD CLASS NAMES
# --------------------------------------------------

class_names = []

with open(CLASS_NAMES_PATH, "r") as file:

    for line in file:

        line = line.strip()

        if line:
            class_name = line.split(": ", 1)[1]
            class_names.append(class_name)


print(f"Model loaded successfully.")
print(f"Number of classes: {len(class_names)}")


# --------------------------------------------------
# PREDICTION FUNCTION
# --------------------------------------------------

def predict_disease(image_path):

    # Open image
    image = Image.open(image_path).convert("RGB")

    # Resize image
    image = image.resize((224, 224))

    # Convert image to NumPy array
    image_array = np.array(image, dtype=np.float32)

    # Normalize pixel values
    image_array = image_array / 255.0

    # Add batch dimension
    image_array = np.expand_dims(image_array, axis=0)

    # Run model
    predictions = model.predict(image_array, verbose=0)

    # Find highest probability
    predicted_index = int(np.argmax(predictions[0]))

    confidence = float(predictions[0][predicted_index])

    predicted_class = class_names[predicted_index]

    confidence_percentage = round(confidence * 100, 2)


    # --------------------------------------------------
    # CONFIDENCE STATUS
    # --------------------------------------------------

    if confidence_percentage >= 70:

        status = "Confident prediction"

    elif confidence_percentage >= 50:

        status = "Possible prediction"

    else:

        status = "Low confidence"


    # --------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------

    return {

        "disease": predicted_class,

        "confidence": confidence_percentage,

        "status": status

    }
