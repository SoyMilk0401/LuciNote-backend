import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'flaskandjwtauthlearning'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DOCUMENTS_FOLDER = 'documents'
    THUMBNAILS_FOLDER = 'thumbnails'

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://lucinote_conn:elucidateWorld!@#$1234@localhost/LuciNoteDB?charset=utf8mb4'


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}