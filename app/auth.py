from functools import wraps
from flask import request, jsonify
import jwt
from .models import User
from flask import current_app

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': '토큰이 존재하지 않습니다.'}), 401

        try:
            # current_app 프록시를 통해 현재 실행 중인 앱의 SECRET_KEY를 가져옴
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': '유효하지 않은 토큰입니다.'}), 401
        except Exception as e:
            return jsonify({'message': '유효하지 않은 토큰입니다.', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)
    return decorated