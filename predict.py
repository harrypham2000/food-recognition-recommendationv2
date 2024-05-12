import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.efficientnet_v2 import decode_predictions
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input


def preprocess_image(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))  # Resize image to match EfficientNetV2 input size
    image = preprocess_input(tf.expand_dims(image, axis=0))  # Preprocess image using EfficientNetV2's preprocess_input function
    return image


def predict(image_path):
    img = preprocess_image(image_path)
    predictions = model.predict(img)
    predicted_labels = decode_predictions(predictions)[0]
    best_class = predicted_labels[0][1]
    return best_class
