from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import shutil
import tempfile

app = Flask(__name__)

# Use environment variables or default to 'uploads' and 'downloads' in the current directory
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER', os.path.join(os.getcwd(), 'downloads'))
ALLOWED_EXTENSIONS = {'txt', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Ensure the upload and download folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

MAX_IMAGE_SIZE = 1000  # Maximum image size (width or height)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def split_text_into_chunks(text, chunk_size):
    for start in range(0, len(text), chunk_size):
        yield text[start:start + chunk_size]

def encode_text_to_image(text):
    binary_text = ''.join(format(ord(char), '08b') for char in text)
    binary_array = np.array([int(bit) for bit in binary_text], dtype=np.uint8)
    side_length = int(np.ceil(np.sqrt(len(binary_array) / 8)))
    padded_binary_array = np.pad(binary_array, (0, side_length * side_length * 8 - len(binary_array)), 'constant')
    byte_array = padded_binary_array.reshape((side_length, side_length, 8))
    encoded_image = np.packbits(byte_array, axis=-1)
    return encoded_image

def decode_image_to_text(image):
    byte_array = np.unpackbits(image, axis=-1)
    binary_array = byte_array.flatten()
    binary_text = ''.join(map(str, binary_array))
    characters = [chr(int(binary_text[i:i + 8], 2)) for i in range(0, len(binary_text), 8)]
    text = ''.join(characters)
    return text.rstrip('\x00')

def encode_text_file_to_images(input_text, input_file_path):
    if not input_text and not input_file_path:
        return None, "No input provided. Please enter text or upload a file."

    if input_text:
        text = input_text
        # Create a temporary file in the uploads folder
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=app.config['UPLOAD_FOLDER']) as temp_file:
            temp_file.write(text)
            input_file_path = temp_file.name
    
    if input_file_path:
        with open(input_file_path, 'r') as file:
            text = file.read()
        
        chunk_size = MAX_IMAGE_SIZE ** 2
        text_chunks = list(split_text_into_chunks(text, chunk_size))
        
        output_image_paths = []
        for idx, chunk in enumerate(text_chunks):
            encoded_image = encode_text_to_image(chunk)
            output_image_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f"{os.path.splitext(os.path.basename(input_file_path))[0]}_encoded_{idx + 1}.png")
            cv2.imwrite(output_image_path, encoded_image)
            output_image_paths.append(output_image_path)
        
        return output_image_paths, None
    else:
        return None, "Failed to process the input."

def decode_image_file_to_text(input_image_paths):
    if not input_image_paths:
        return None, "No input provided. Please upload an image file."

    decoded_texts = []
    for input_image_path in input_image_paths:
        # Read encoded image
        encoded_image = cv2.imread(input_image_path, cv2.IMREAD_GRAYSCALE)
        
        # Decode image back to text
        decoded_text = decode_image_to_text(encoded_image)
        decoded_texts.append(decoded_text)
    
    # Write decoded text to temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=app.config['DOWNLOAD_FOLDER']) as temp_file:
        for text in decoded_texts:
            temp_file.write(text)
        temp_file_path = temp_file.name

    return temp_file_path, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    print("Encode route called")
    text_input = request.form.get('text_input')
    file = request.files.get('file')

    print(f"Received text_input: {text_input}")
    print(f"Received file: {file}")

    file_path = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")

    # Call encode function
    encoded_image_paths, error = encode_text_file_to_images(text_input, file_path)

    if error:
        print(f"Error occurred: {error}")
        return jsonify({"error": error}), 400

    # Generate download links
    download_links = []
    for path in encoded_image_paths:
        filename = os.path.basename(path)
        download_link = url_for('download_file', filename=filename, _external=True)
        download_links.append(download_link)

    # Return JSON response
    response = {
        "result": f'Encoded image(s) saved successfully.',
        "download_links": download_links
    }
    print(f"Sending response: {response}")
    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/decode', methods=['POST'])
def decode():
    files = request.files.getlist('file')

    if not files or all(file.filename == '' for file in files):
        return jsonify({"error": "No files uploaded. Please select at least one image file."}), 400

    file_paths = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_paths.append(file_path)

    # Call decode function
    output_text_file_path, error = decode_image_file_to_text(file_paths)

    if error:
        return jsonify({"error": error}), 400

    # Generate a download link for the decoded text file
    decoded_filename = os.path.basename(output_text_file_path)
    download_link = url_for('download_file', filename=decoded_filename, _external=True)

    # Return JSON response
    return jsonify({
        "result": 'Decoded text saved successfully.',
        "text_file_path": output_text_file_path,
        "download_link": download_link
    })

if __name__ == '__main__':
    app.run(debug=True)
