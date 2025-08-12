import datetime
from flask import request, jsonify, Blueprint, current_app, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from .. import db
from ..models import User

auth = Blueprint('auth', __name__)

def create_tokens(user_id):
    access_token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    refresh_token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")
    
    return access_token, refresh_token


@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email, password, username = data.get('email'), data.get('password'), data.get('username')
    
    if not email or not password or not username:
        return jsonify({'message': '필수 필드가 누락되었습니다.'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': '이미 존재하는 이메일입니다.'}), 409
        
    if User.query.filter_by(username=username).first():
        return jsonify({'message': '이미 존재하는 닉네임입니다.'}), 409
        
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(email=email, password_hash=hashed_password, username=username)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '회원가입이 완료되었습니다.'}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    
    if not email or not password:
        return jsonify({'message': '로그인 정보가 올바르지 않습니다.'}), 401
        
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': '로그인 정보가 올바르지 않습니다.'}), 401
    
    access_token, refresh_token = create_tokens(user.id)
    
    response = make_response(jsonify({'access_token': access_token}))
    response.set_cookie(
        'refresh_token', 
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite='Lax'
    )
    
    return response


@auth.route('/refresh', methods=['POST'])
def refresh():
    
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return jsonify({'message': '리프레시 토큰이 존재하지 않습니다.'}), 401

    try:
        data = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        
        new_access_token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'access_token': new_access_token})

    except jwt.ExpiredSignatureError:
        return jsonify({'message': '만료된 리프레시 토큰입니다. 다시 로그인하세요.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': '유효하지 않은 리프레시 토큰입니다.'}), 401


@auth.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': '성공적으로 로그아웃되었습니다.'}))
    response.set_cookie('refresh_token', '', expires=0)
    return response