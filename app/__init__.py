from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_by_name
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
oauth = OAuth()

def create_app(config_name):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])
    
    db.init_app(app)
    oauth.init_app(app)
    
    # Naver OAuth 설정
    oauth.register(
        name='naver',
        client_id=app.config['NAVER_CLIENT_ID'],
        client_secret=app.config['NAVER_CLIENT_SECRET'],
        access_token_url='https://nid.naver.com/oauth2.0/token',
        access_token_params=None,
        authorize_url='https://nid.naver.com/oauth2.0/authorize',
        authorize_params=None,
        api_base_url='https://openapi.naver.com/',
        client_kwargs={'scope': 'name email'},
        userinfo_endpoint='v1/nid/me'
    )

    # Google OAuth 설정
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    from .routes.auth_routes import auth
    from .routes.file_routes import file
    from .routes.summary_routes import summary
    
    app.register_blueprint(auth, url_prefix='/api/auth')
    app.register_blueprint(file, url_prefix='/api/files')
    app.register_blueprint(summary, url_prefix='/api/summary')

    return app