from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
from fuzzywuzzy import fuzz
from metaphone import doublemetaphone
from indic_transliteration import sanscript

app = Flask(__name__)
CORS(app)  # To allow cross-origin requests

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to normalize names
def normalize_name(name):
    return name.strip().lower()

# Function to perform fuzzy matching
def fuzzy_match(name1, name2):
    return fuzz.ratio(normalize_name(name1), normalize_name(name2))

# Function for phonetic matching
def phonetic_match(name):
    return doublemetaphone(normalize_name(name))

@app.route('/')
def index():
    return render_template('index.html')

# OCR API route to handle image uploads
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['image']
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(image_path)

    # Call OCR API
    with open(image_path, 'rb') as img:
        response = requests.post(
            "https://ocr-extract-text.p.rapidapi.com/ocr",
            headers={
                "x-rapidapi-key": "5c6b4b123bmsh2d4ad7d4a62b9aap14a5aejsn4074919061fb",  # Replace with your API key
                "x-rapidapi-host": "ocr-extract-text.p.rapidapi.com"
            },
            files={"image": img}
        )
    
    result = response.json()
    if response.status_code != 200 or 'text' not in result:
        return jsonify({'error': 'Error extracting text from image'}), 500

    # Extract Hindi text
    hindi_text = result['text']

    # Transliterate Hindi text to English
    english_name = sanscript.transliterate(hindi_text, sanscript.DEVANAGARI, sanscript.IAST)
    normalized_name = english_name.replace('ś', 's').replace('ा', '')
    
    # Simulated database name list, will later be getting these names from database
    name_list = ["Srikrishna", "Sri", "krishna" , "Suresh", "Sursh", "Kumar", "Kumaar", "कुमार", "सुरेश"]
    
    # Perform fuzzy matching
    matches = [name for name in name_list if fuzzy_match(normalized_name, name) > 20]
    
    # Perform phonetic matching
    phonetic_target = phonetic_match(normalized_name)
    phonetic_matches = [name for name in name_list if phonetic_match(name) == phonetic_target]


print("Original Text:", hindi_text)
print("Transliterated Text:", normalized_name)

# Generate phonetic encoding for the normalized name
phonetic_target = phonetic_match(normalized_name)
print("Phonetic Target for Normalized Name:", phonetic_target)

# Check phonetic encodings for each name in the list
for name in name_list:
    phonetic_code = phonetic_match(name)
    print(f"Phonetic Match for '{name}': {phonetic_code}")

# Perform phonetic matching
phonetic_matches = [name for name in name_list if phonetic_match(name) == phonetic_target]

# Print phonetic matches
print("Phonetic Matches Found:", phonetic_matches)
    return jsonify({
        'original_text': hindi_text,
        'transliterated_text': normalized_name,
        'fuzzy_matches': list(set(matches)),
        'phonetic_matches': phonetic_matches
    })

# Start the server
if __name__ == '__main__':
    app.run(port=3000)
