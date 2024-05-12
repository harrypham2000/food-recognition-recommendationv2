import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.efficientnet import decode_predictions, preprocess_input
from PIL import Image  # Add missing import statement
TF_ENABLE_ONEDNN_OPTS=0

import db_search
model = load_model('trained_food101.keras', compile=False)
model.summary()
img=preprocess_input(tf.expand_dims(Image.open('images/1.jpg').resize((224,224)), axis=0))
predict = model.predict(img)
label=decode_predictions(predict)[0]
prediction='%s (%.2f%%)' % (label[0][1], label[0][2]*100)

print(prediction)

result= db_search.search('recipes', 'title', label[0][1], 'recipes', 'harry', '1309800ok', 'localhost', '5432')
print(result)