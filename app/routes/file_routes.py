import os
import uuid
from flask import request, jsonify, Blueprint, current_app
from .. import db
from ..models import Material
from ..auth import token_required

file = Blueprint('file', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@file.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'file' not in request.files:
        return jsonify({'message': '파일이 요청에 포함되지 않았습니다.'}), 400
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'message': '선택된 파일이 없습니다.'}), 400

    if uploaded_file and allowed_file(uploaded_file.filename):
        original_filename = uploaded_file.filename
        file_ext = os.path.splitext(original_filename)[1].lower().replace('.', '')
        
        unique_filename = str(uuid.uuid4()) + os.path.splitext(original_filename)[1]
        filepath = os.path.join(current_app.config['MATERIAL_FOLDER'], unique_filename)
        
        uploaded_file.save(filepath)

        new_material = Material(
            title=original_filename,
            material_type=file_ext,
            source_file_path=filepath,
            user_id=current_user.id
        )
        
        db.session.add(new_material)
        db.session.commit()
        
        return jsonify({
            'message': '파일 업로드 및 정보 저장이 완료되었습니다.',
            'material_id': new_material.id,
            'title': new_material.title
        }), 201
    else:
        return jsonify({'message': '허용되지 않는 파일 형식입니다.'}), 400


@file.route('/list', methods=['GET'])
@token_required
def get_my_files(current_user):
    materials = Material.query.filter_by(user_id=current_user.id, is_deleted=False).all()

    output = [{
        'id': material.id,
        'title': material.title,
        'material_type': material.material_type,
        'created_at': material.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for material in materials]
    
    return jsonify({'files': output})