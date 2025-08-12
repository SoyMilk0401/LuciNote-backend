import os
import openai
import PyPDF2
import tiktoken
from flask import request, jsonify, Blueprint, current_app
from .. import db
from ..models import Material, Summary
from ..auth import token_required

summary = Blueprint('summary', __name__)

def get_text_from_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    text_content = ""

    if file_extension.lower() == '.pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text_content += page.extract_text() or ""
    elif file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text_content = f.read()
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")
    
    if not text_content.strip():
        raise ValueError("파일에서 텍스트를 추출할 수 없습니다.")
        
    return text_content

def summarize_text_in_chunks(text_content, language='ko'):
    max_tokens = 3000
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    tokens = encoding.encode(text_content)
    chunks = [tokens[i:i + max_tokens] for i in range(0, len(tokens), max_tokens)]
    
    summaries = []
    for i, chunk in enumerate(chunks):
        chunk_text = encoding.decode(chunk)
        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        
        prompt = f"다음은 긴 문서의 일부입니다. 이 부분을 {language} 언어로 친절하게 핵심만 요약해주세요:\n\n{chunk_text}"
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes parts of a long document."},
                {"role": "user", "content": prompt}
            ]
        )
        summaries.append(response.choices[0].message.content.strip())

    combined_summary = "\n\n".join(summaries)
    final_prompt = f"다음은 문서의 각 부분을 요약한 내용입니다. 이 요약본들을 바탕으로 전체 내용을 아우르는 최종 요약본을 {language} 언어로 작성해주세요:\n\n{combined_summary}"

    final_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at creating a final, coherent summary from partial summaries."},
            {"role": "user", "content": final_prompt}
        ]
    )
    
    return final_response.choices[0].message.content.strip()


def get_summary_from_openai(file_path, language='ko', custom_prompt=''):
    try:
        text_content = get_text_from_file(file_path)
        openai.api_key = current_app.config['OPENAI_API_KEY']
        
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        total_tokens = len(encoding.encode(text_content))

        if total_tokens > 4000:
            print("Document is too long, summarizing in chunks...")
            summary_text = summarize_text_in_chunks(text_content, language)
        else:
            print("Document is short enough, summarizing directly...")
            prompt = f"다음 문서를 {language} 언어로 {custom_prompt} 친절하게 핵심만 요약해주세요:\n\n{text_content}"
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )
            summary_text = response.choices[0].message.content.strip()

        return summary_text, None

    except (FileNotFoundError, ValueError) as e:
        return None, str(e)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, f"요약 중 오류가 발생했습니다: {str(e)}"


@summary.route('/<int:material_id>', methods=['POST'])
@token_required
def submit_summary(current_user, material_id):
    material = Material.query.filter_by(id=material_id, is_deleted=False).first()

    if not material:
        return jsonify({'message': '요청한 자료를 찾을 수 없습니다.'}), 404
    
    if material.user_id != current_user.id:
        return jsonify({'message': '이 자료에 접근할 권한이 없습니다.'}), 403

    data = request.get_json()
    custom_prompt = data.get('custom_prompt', '')
    summary_title = data.get('summary_title', f"{material.title} 요약")
    language = data.get('language', 'ko')

    file_full_path = os.path.join(current_app.root_path, '..', material.source_file_path)
    summary_text, error = get_summary_from_openai(file_full_path, language, custom_prompt)

    if error:
        return jsonify({'message': error}), 500

    existing_summary = Summary.query.filter_by(
        user_id=current_user.id,
        material_id=material_id
    ).first()

    if existing_summary:
        existing_summary.summary_title = summary_title
        existing_summary.summary_text = summary_text
        existing_summary.language = language
        db.session.commit()
        
        return jsonify({
            'message': '요약이 성공적으로 업데이트되었습니다.',
            'summary_id': existing_summary.id,
            'summary_title': existing_summary.summary_title,
            'summary_text': existing_summary.summary_text
        }), 200
    else:

        new_summary = Summary(
            summary_title=summary_title,
            summary_text=summary_text,
            language=language,
            user_id=current_user.id,
            material_id=material.id
        )
        db.session.add(new_summary)
        db.session.commit()

        return jsonify({
            'message': '요약이 성공적으로 생성되었습니다.',
            'summary_id': new_summary.id,
            'summary_title': new_summary.summary_title,
            'summary_text': new_summary.summary_text
        }), 201


@summary.route('/<int:material_id>', methods=['GET'])
@token_required
def get_summary(current_user, material_id):
    summarys = Summary.query.filter_by(user_id=current_user.id, material_id=material_id, is_deleted=False).all()

    output = [{
        'id': summary.id,
        'material_id': summary.material_id,
        'summary_title': summary.summary_title,
        'summary_text': summary.summary_text,
        'language': summary.language,
        'generated_at': summary.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
        'updated_at': summary.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    } for summary in summarys]
    
    return jsonify({'summarys': output})
