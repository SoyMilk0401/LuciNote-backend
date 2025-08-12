import os
import time
from flask import request, jsonify, Blueprint, current_app
from .. import db
from ..models import Document, Submission
from ..auth import token_required

summary = Blueprint('summary', __name__)

@summary.route('/summary/<int:document_id>', methods=['POST'])
@token_required
def submit_summary(current_user, document_id):
    document = Document.query.get(document_id)

    if not document:
        return jsonify({'message': '요청한 문서를 찾을 수 없습니다.'}), 404
    
    if document.user_id != current_user.id:
        return jsonify({'message': '이 문서에 접근할 권한이 없습니다.'}), 403

    data = request.get_json()
    request_type = data.get('request_type', 'simple_summary')
    request_prompt = data.get('request_prompt', '기본프롬프트')

    # --- 여기부터 AI 처리 로직 ---
    print(f"AI 모델 호출: Document ID {document.id}에 대한 '{request_type}' 요약 요청")
    summary_text = f"이것은 '{document.original_filename}' 파일의 '{request_type}' 요약 결과입니다."
    references_data = [{'page': 1, 'snippet': '문서의 첫 번째 단락 내용...'}, {'page': 3, 'snippet': '세 번째 페이지의 중요한 문장...'}]
    related_questions = ["이 문서의 핵심 주장은 무엇인가요?", "작성자는 누구인가요?"]
    # --- 여기까지가 AI 처리 로직 ---

    new_submission = Submission(
        request_type=request_type,
        request_prompt=request_prompt,
        summary_content=summary_text,
        references=references_data,
        related_questions=related_questions,
        owner=current_user,
        document=document
    )

    db.session.add(new_submission)
    db.session.commit()

    return jsonify({
        'message': '요약 요청이 성공적으로 처리되었습니다.',
        'submission_id': new_submission.id,
        'summary': new_submission.summary_content
    }), 201

