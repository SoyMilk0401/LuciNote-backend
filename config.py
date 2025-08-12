import os
import dotenv

dotenv.load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MATERIAL_FOLDER = 'materials'
    THUMBNAILS_FOLDER = 'thumbnails'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}