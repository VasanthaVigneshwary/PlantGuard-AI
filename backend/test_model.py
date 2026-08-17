from ml.predict import predict_disease


# Test image
image_path = "uploads/leaf-spot-fungus-920x518.webp"


# Get AI prediction
result = predict_disease(image_path)


# Display result
print("\n🌱 PLANT GUARD AI RESULT")
print("------------------------")
print("Prediction :", result["disease"])
print("Confidence :", result["confidence"], "%")
print("Status     :", result["status"])