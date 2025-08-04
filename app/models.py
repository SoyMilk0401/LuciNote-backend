import datetime
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)    # 소셜 로그인의 경우 null
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    social_accounts = db.relationship('SocialAccount', backref='user', lazy=True, cascade="all, delete-orphan")
    documents = db.relationship('Document', backref='owner', lazy=True, cascade="all, delete-orphan")
    submissions = db.relationship('Submission', backref='owner', lazy=True, cascade="all, delete-orphan")

class SocialAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)     # Google, Naver
    provider_user_id = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.now)
    thumbnail_path = db.Column(db.String(512), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submissions = db.relationship('Submission', backref='document', lazy=True, cascade="all, delete-orphan")

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    
    # 사용자의 요청 정보
    request_type = db.Column(db.String(50), nullable=False, default='simple_summary')   # 'simple_summary', 'deep_research'
    request_prompt = db.Column(db.Text, nullable=True)  # 사용자가 입력한 구체적인 프롬프트
    
    # AI의 결과물
    summary_content = db.Column(db.Text, nullable=False)    # 요약 결과
    references = db.Column(db.JSON, nullable=True)  # 요약에 대한 근거 목록
    related_questions = db.Column(db.JSON, nullable=True)   # 추천 질문 목록
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)