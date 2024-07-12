# app.py
from flask import Flask, request, send_file, jsonify, render_template
from pillow_heif import register_heif_opener
from PIL import Image
import io

app = Flask(__name__)

# Register HEIF opener
register_heif_opener()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(error='No file part')

        file = request.files['file']

        if file.filename == '':
            return jsonify(error='No selected file')

        if file and file.filename.lower().endswith(('.heic', '.heif')):
            try:
                # Read the file into memory
                in_memory_file = io.BytesIO(file.read())

                # Open the image using Pillow
                with Image.open(in_memory_file) as img:
                    # Convert to RGB (this is necessary for HEIC images)
                    img = img.convert('RGB')

                    # Save as JPEG to a new BytesIO object
                    out_memory_file = io.BytesIO()
                    img.save(out_memory_file, format='JPEG')
                    out_memory_file.seek(0)

                return send_file(
                    out_memory_file,
                    mimetype='image/jpeg',
                    as_attachment=True,
                    download_name=f"{file.filename.rsplit('.', 1)[0]}.jpg"
                )
            except Exception as e:
                app.logger.error(f'Error during file conversion: {str(e)}')
                return jsonify(error='An error occurred during file conversion')
        else:
            return jsonify(error='Invalid file type. Please upload a HEIC or HEIF file.')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)