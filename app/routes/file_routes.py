import os
import uuid
from flask import request, jsonify, Blueprint, current_app
from .. import db
from ..models import Document
from ..auth import token_required

file_bp = Blueprint('file', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': '파일이 요청에 포함되지 않았습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': '선택된 파일이 없습니다.'}), 400

    if file and allowed_file(file.filename):
        original_filename = file.filename
        filename = str(uuid.uuid4()) + os.path.splitext(original_filename)[1]
        filepath = os.path.join(current_app.config['DOCUMENTS_FOLDER'], filename)
        thumbnail_path = os.path.join(current_app.config['THUMBNAILS_FOLDER'], filename + "-thumbnail.png")
        
        file.save(filepath)

        new_document = Document(
            original_filename=original_filename,
            filename=filename,
            filepath=filepath,
            thumbnail_path=thumbnail_path,
            owner=current_user
        )
        
        db.session.add(new_document)
        db.session.commit()
        return jsonify({'message': '파일 업로드 및 정보 저장이 완료되었습니다.', 'filename': filename}), 200
    else:
        return jsonify({'message': '허용되지 않는 파일 형식입니다.'}), 400

@file_bp.route('/list', methods=['GET'])
@token_required
def get_my_files(current_user):
    documents = current_user.documents
    output = [{'id': doc.id, 'original_filename': doc.original_filename, 'upload_date': doc.upload_date.strftime("%Y-%m-%d %H:%M:%S")} for doc in documents]
    return jsonify({'files': output})