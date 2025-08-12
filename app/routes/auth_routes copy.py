import datetime
from flask import request, jsonify, Blueprint, current_app, make_response, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from .. import db
from ..models import User, UserProvider
from app import oauth

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


@auth.route('/login/<provider>')
def social_login(provider):
    """소셜 로그인 페이지로 리디렉션합니다."""
    redirect_uri = url_for('auth.authorize', provider=provider, _external=True)
    return oauth.create_client(provider).authorize_redirect(redirect_uri)

@auth.route('/authorize/<provider>')
def authorize(provider):
    """소셜 로그인 후 콜백을 처리하고, 유저 정보 확인 및 생성을 담당합니다."""
    client = oauth.create_client(provider)
    token = client.authorize_access_token()
    
    user_info = None
    if provider == 'google':
        user_info = client.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    elif provider == 'naver':
        user_info_resp = client.get('v1/nid/me')
        user_info_resp.raise_for_status()
        user_info = user_info_resp.json().get('response')

    if not user_info:
        return jsonify(message="사용자 정보를 가져올 수 없습니다."), 400

    provider_user_id = user_info.get('id') or user_info.get('sub')
    email = user_info.get('email')
    
    # 1. 소셜 계정 정보로 기존 유저 찾기
    user_provider = UserProvider.query.filter_by(
        provider=provider, 
        provider_user_id=str(provider_user_id)
    ).first()

    if user_provider:
        # 소셜 계정으로 로그인 성공, 토큰 발급
        user = user_provider.user
        access_token, refresh_token = create_tokens(user.id)
        response = make_response(jsonify({'access_token': access_token, 'message': f'{user.username}님 환영합니다.'}))
        response.set_cookie('refresh_token', value=refresh_token, httponly=True, secure=True, samesite='Lax')
        # TODO: 로그인 성공 후 프론트엔드로 리디렉션하는 로직 추가
        return response

    # 2. 이메일로 기존 유저 찾기 (소셜 계정 연결)
    user = User.query.filter_by(email=email).first()
    if user:
        # 기존 계정에 소셜 정보 추가
        new_provider = UserProvider(
            provider=provider,
            provider_user_id=str(provider_user_id),
            email=email,
            display_name=user_info.get('name'),
            user_id=user.id
        )
        db.session.add(new_provider)
        db.session.commit()
    else:
        # 3. 신규 유저 생성
        new_user = User(
            email=email,
            username=user_info.get('name') or f"{provider}_{provider_user_id}"
            # 소셜 로그인은 비밀번호가 없음
        )
        db.session.add(new_user)
        db.session.flush() # new_user의 id를 가져오기 위해 flush

        new_provider = UserProvider(
            provider=provider,
            provider_user_id=str(provider_user_id),
            email=email,
            display_name=user_info.get('name'),
            user_id=new_user.id
        )
        db.session.add(new_provider)
        db.session.commit()
        user = new_user

    # 새로 생성/연결된 계정으로 토큰 발급
    access_token, refresh_token = create_tokens(user.id)
    response = make_response(jsonify({'access_token': access_token, 'message': '로그인에 성공했습니다.'}))
    response.set_cookie('refresh_token', value=refresh_token, httponly=True, secure=True, samesite='Lax')
    # TODO: 로그인 성공 후 프론트엔드로 리디렉션하는 로직 추가
    return response
