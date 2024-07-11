from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from pillow_heif import register_heif_opener
from PIL import Image
import os
import io
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/app.log',
                                   maxBytes=10240,
                                   backupCount=10)
file_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('HEIC to JPG Converter startup')

# Register HEIF opener
register_heif_opener()

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'heic', 'heif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(413)
def too_large(e):
    app.logger.warning('File too large uploaded')
    return jsonify(error="File is too large. Maximum size is 16MB."), 413


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            app.logger.info('No file part in the request')
            return jsonify(error='No file part')
        file = request.files['file']
        if file.filename == '':
            app.logger.info('No selected file')
            return jsonify(error='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            app.logger.info(f'File saved: {filepath}')

            try:
                # Convert HEIC/HEIF to JPG
                with Image.open(filepath) as img:
                    output = io.BytesIO()
                    img.convert('RGB').save(output, format='JPEG')
                    output.seek(0)

                # Clean up the uploaded file
                os.remove(filepath)
                app.logger.info(
                    f'File converted and original removed: {filepath}')

                return send_file(
                    output,
                    mimetype='image/jpeg',
                    as_attachment=True,
                    download_name=f"{os.path.splitext(filename)[0]}.jpg")
            except Exception as e:
                app.logger.error(f'Error during file conversion: {str(e)}')
                return jsonify(
                    error='An error occurred during file conversion')
        else:
            app.logger.info('Invalid file type uploaded')
            return jsonify(
                error='Invalid file type. Please upload a HEIC or HEIF file.')
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
