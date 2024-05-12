import os
from flask import Flask, render_template, jsonify, redirect, url_for, send_from_directory,request
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow.keras.models import load_model
from werkzeug.utils import secure_filename
from geopy.geocoders import Nominatim
import geocoder
import db_search
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.applications.efficientnet_v2 import preprocess_input
import psycopg2
from tensorflow.keras.preprocessing import image as image_utils
import numpy as np
# from io import BytesIO
from geopy.geocoders import Nominatim
import requests
from requests import get

# Search for current location based on IP client
def current_location():
    location=get('http://ipapi.co/json').json()
    lat,long=location['latitude'],location['longitude']
    return f"{lat}, {long}"
    
    
#DEFINE MAPBOX
HO_CHI_MINH_CITY_COORDINATES = (10.762622, 106.660172)
MAPBOX_API_KEY="pk.eyJ1IjoiaHVuZ3BnIiwiYSI6ImNsdnczaWN1MDI1ZnYya214enlmbDBwcTUifQ.XyiCBLGL150eoW5cysk7tQ"
MAPBOX_GEOCODER_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json?&access_token={}&proximity={}".format("{}","MAPBOX_API_KEY","ip")
# MAPBOX_GEOCODER_URL = "https://api.mapbox.com/search/geocode/v6/forward?q={}&access_token={}&country=vn".format("{}","MAPBOX_API_KEY")
def search_location(query):
    url = MAPBOX_GEOCODER_URL.format(requests.utils.quote(query))
    # params = {
    #     "access_token": MAPBOX_API_KEY,
    #     "autocomplete": True,
    #     "country": "vn",
    #     "limit": 1,
    # }
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data["features"]:
            location = data["features"][0]
            return (location["center"][1], location["center"][0])
    return None

#DEFINE FOR EDAMAM
EDAMAM_APP_ID = "61b2055f"
EDAMAM_APP_KEY="29f8098c06f4ba46364be7445e808785"
EDAMAM_ENDPOINT="https://api.edamam.com/api/food-database/v2/parser?app_id={}&app_key={}&ingr={}".format(EDAMAM_APP_ID,EDAMAM_APP_KEY,{})

def get_nutrients(food):
    url = EDAMAM_ENDPOINT.format(requests.utils.quote(food))
    response = requests.get(url)
    data = response.json()
    nutrients = []
    if "hints" in data:
        for item in data["hints"]:
            food_info = {
                "label": item["food"]["label"],
                "nutrients": item["food"]["nutrients"],
                # "img": item["food"]["image"]
            }
            nutrients.append(food_info)
        return nutrients
    else:
        return "No data found"
#DEFINE CLASSES AND LABELS
class_names = ['apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare', 'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito', 'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake', 'ceviche', 'cheese_plate', 'cheesecake', 'chicken_curry', 'chicken_quesadilla', 'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder', 'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes', 'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots', 'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries', 'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt', 'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon', 'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog', 'huevos_rancheros', 'hummus', 'ice_cream', 'lasagna', 'lobster_bisque', 'lobster_roll_sandwich', 'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels', 'nachos', 'omelette', 'onion_rings', 'oysters', 'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck', 'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich', 'ramen', 'ravioli', 'red_velvet_cake', 'risotto', 'samosa', 'sashimi', 'scallops', 'seaweed_salad', 'shrimp_and_grits', 'spaghetti_bolognese', 'spaghetti_carbonara', 'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki', 'tiramisu', 'tuna_tartare', 'waffles']
label_names = ['Apple pie', 'Baby back ribs', 'Baklava', 'Beef carpaccio', 'Beef tartare', 'Beet salad', 'Beignets', 'Bibimbap', 'Bread pudding', 'Breakfast burrito', 'Bruschetta', 'Caesar salad', 'Cannoli', 'Caprese salad', 'Carrot cake', 'Ceviche', 'Cheesecake', 'Cheese plate', 'Chicken curry', 'Chicken quesadilla', 'Chicken wings', 'Chocolate cake', 'Chocolate mousse', 'Churros', 'Clam chowder', 'Club sandwich', 'Crab cakes', 'Creme brulee', 'Croque madame', 'Cup cakes', 'Deviled eggs', 'Donuts', 'Dumplings', 'Edamame', 'Eggs benedict', 'Escargots', 'Falafel', 'Filet mignon', 'Fish and chips', 'Foie gras', 'French fries', 'French onion soup', 'French toast', 'Fried calamari', 'Fried rice', 'Frozen yogurt', 'Garlic bread', 'Gnocchi', 'Greek salad', 'Grilled cheese sandwich', 'Grilled salmon', 'Guacamole', 'Gyoza', 'Hamburger', 'Hot and sour soup', 'Hot dog', 'Huevos rancheros', 'Hummus', 'Ice cream', 'Lasagna', 'Lobster bisque', 'Lobster roll sandwich', 'Macaroni and cheese', 'Macarons', 'Miso soup', 'Mussels', 'Nachos', 'Omelette', 'Onion rings', 'Oysters', 'Pad thai', 'Paella', 'Pancakes', 'Panna cotta', 'Peking duck', 'Pho', 'Pizza', 'Pork chop', 'Poutine', 'Prime rib', 'Pulled pork sandwich', 'Ramen', 'Ravioli', 'Red velvet cake', 'Risotto', 'Samosa', 'Sashimi', 'Scallops', 'Seaweed salad', 'Shrimp and grits', 'Spaghetti bolognese', 'Spaghetti carbonara', 'Spring rolls', 'Steak', 'Strawberry shortcake', 'Sushi', 'Tacos', 'Takoyaki', 'Tiramisu', 'Tuna tartare', 'Waffles']
class_to_label = dict(zip(class_names, label_names))

#DEFINE DB CONNECTION
table_name = 'recipes'
column_name = 'title'
database = 'recipes'
username = 'harry'
password = '1309800ok'
host = 'localhost'
port = '5432'

conn=psycopg2.connect(database=database, user=username, password=password, host=host, port=port)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    # Try to load the image using 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS           
app=Flask(__name__,template_folder='templates')
# app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')
model=load_model('trained_food101_old.h5')
@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        image = request.files['image']
        # if not allowed_file(image):
        #     return "Invalid image file. Please upload a valid image file."
        if image.filename == '':
            return "Please select an image file."
        if not allowed_file(image.filename):
            return "Invalid image file. Please upload a valid image file."
        filename = secure_filename(image.filename)
    
        img_path = os.path.join('uploads/', filename)
       
        image.save(img_path)
        # print(img_path)
        img_url=url_for('static', filename=filename)
        # image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', filename)
        image = image_utils.load_img(img_path, target_size=(224, 224))
        image = preprocess_input(image)
        image = np.expand_dims(image, axis=0)
        preds = model.predict(image)
        best_class_index = np.argmax(preds[0])
        best_class_label = class_to_label[class_names[best_class_index]]
    
        if best_class_label:
            location=search_location(best_class_label)
        else:
            # Get user location based on IP address
            # g=geocoder.ip('me')
            # location=(g.latlng[0],g.latlng[1])
            location=HO_CHI_MINH_CITY_COORDINATES
        recipe = db_search.search(conn, table_name, 'title', best_class_label)
        recipes='\n'.join(recipe)
        nutrient=get_nutrients(best_class_label)
        #print(recipes)
        # os.remove(img_path)
        return render_template('index.html', predicted_food=best_class_label, filename=filename,recipe=recipes,img_url=img_url,location=location,nutrients_all=nutrient)
    # else:
    #     cur_location=current_location()
    return render_template('index.html', prediction=None, recipe=None, filename=None, img_url=None,location=HO_CHI_MINH_CITY_COORDINATES)
@app.route('/uploads/<filename>')
def get_image(filename):
    return send_from_directory('uploads/',filename)


if __name__ == '__main__':
    app.run(debug=True)
# @app.route('/upload', methods=['POST'])
# def upload():
#     if request.method == 'POST':
#         image = request.files['image']
#         filename = secure_filename(image.filename)
#         img_path=os.path.join('static','uploads', filename)
#         image.save(img_path)
#         img_url=url_for('static', filename='uploads/'+filename)
#         return render_template('index.html',filename=filename, img_url=img_url)
# @app.route('/uploads/<filename>')
# def get_image(filename):
#     return send_from_directory(os.path.join(app.root_path, 'static', 'uploads'), filename)

    
    
# @app.route('/', methods=['GET'])
# def index():
#     return render_template('home.html')

# @app.route('/predict/<string:filename>')
# def predict(filename):
#     """
#     Predicts the food in the given image and returns the recipe for the recognized food.

#     Args:
#         filename (str): The name of the image file.

#     Returns:
#         dict: A dictionary containing the recipe for the recognized food.
#     """
#     # Get directory where the app is located
#     app_dir = os.path.dirname(os.path.abspath(__file__))
#     # Load the image and perform food recognition
#     image_path = os.path.join(app_dir,'uploads', filename)
#     image=image_utils.load_img(image_path, target_size=(224, 224))
#     image=preprocess_input(image)
#     image=np.expand_dims(image, axis=0)
#     # Predict the food in the image
#     preds=model.predict(image)
#     best_class_index = np.argmax(preds[0])
#     best_class_label = class_to_label[class_names[best_class_index]]
#     # best_class=class_names[best_class_index]
    
#     # Get the recipe for the recognized food
#     recipe = db_search.search(conn,table_name,'title',best_class_label)
    
#     # Delete the uploaded image after prediction
#     os.remove(image_path)
    
#     return jsonify({'result':best_class_label,'recipe': recipe})

# @app.route('/preview/<string:filename>')
# def preview(filename):
#     # Load the image 
#     return render_template('preview.html', filename=filename)

# @app.route('/', methods=['POST'])
# def predict():
#     imgfile = request.files['imgfile']
#     img_path = "./images/" + imgfile.filename
#     imgfile.save(img_path)
#     img=preprocess_input(tf.expand_dims(Image.open(img_path).resize((224,224)), axis=0))
#     predict = model.predict(img)
#     label=decode_predictions(predict)[0]
#     prediction='%s (%.2f%%)' % (label[0][1], label[0][2]*100)
    
#     return render_template('index.html', result=prediction)

