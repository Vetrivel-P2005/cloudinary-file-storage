from flask import Flask, request, jsonify
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from flask import send_file
load_dotenv()

app = Flask(__name__)
CORS(app)

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

users = {
    'student1': 'password123',
    'teacher1': 'password123'
}

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt', 'docx', 'doc', 'pptx', 'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username] == password:
        token = str(uuid.uuid4())
        return jsonify({'success': True, 'token': token, 'username': username})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/upload', methods=['POST'])
def upload_file():
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({'success': False, 'message': 'No token'}), 401

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'File type not allowed'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'message': 'File too large (max 10MB)'}), 400

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())[:8]
    ext = filename.rsplit('.', 1)[-1].lower()

    resource_type = "image"
    if ext in ['txt', 'pdf', 'doc', 'docx', 'pptx', 'xlsx']:
        resource_type = "raw"

    upload = cloudinary.uploader.upload(
        file,
        folder="cloud-storage/uploads",
        public_id=f"{unique_id}_{filename}",
        resource_type=resource_type,
        context={
            'original_filename': filename,
            'uploaded_by': auth.split(' ')[-1][:8],
            'upload_date': datetime.now().isoformat()
        }
    )

    return jsonify({
        'success': True,
        'file': {
            'filename': filename,
            'url': upload.get('secure_url'),
            'public_id': upload.get('public_id'),
            'size': upload.get('bytes'),
            'format': upload.get('format'),
            'resource_type': upload.get('resource_type'),
            'created_at': upload.get('created_at')
        }
    })

@app.route('/api/files', methods=['GET'])
def list_files():
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({'success': False, 'message': 'No token'}), 401

    result = cloudinary.api.resources(
        type="upload",
        prefix="cloud-storage/uploads/",
        max_results=500,
        context=True
    )

    files = []
    for r in result.get('resources', []):
        public_id = r.get('public_id')
        filename = public_id.split('/')[-1] if public_id else 'unknown'
        files.append({
            'public_id': public_id,
            'filename': filename,
            'url': r.get('secure_url'),
            'size': r.get('bytes'),
            'format': r.get('format'),
            'resource_type': r.get('resource_type'),
            'created_at': r.get('created_at')
        })

    return jsonify({'success': True, 'files': files, 'count': len(files)})

@app.route('/api/delete/<path:public_id>', methods=['DELETE'])
def delete_file(public_id):
    auth = request.headers.get('Authorization')
    if not auth:
        return jsonify({'success': False, 'message': 'No token'}), 401

    for r_type in ['raw', 'image', 'video']:
        result = cloudinary.uploader.destroy(public_id, resource_type=r_type, invalidate=True)
        if result.get('result') == 'ok':
            return jsonify({'success': True, 'message': 'Deleted'})

    return jsonify({'success': False, 'message': 'File not found'}), 404

@app.route('/')
def serve_index():
    return send_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
