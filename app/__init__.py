from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_by_name

db = SQLAlchemy()

def create_app(config_name):

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])
    
    db.init_app(app)
    
    from .routes.auth_routes import auth
    from .routes.file_routes import file
    from .routes.summary_routes import summary
    
    app.register_blueprint(auth, url_prefix='/api/auth')
    app.register_blueprint(file, url_prefix='/api/files')
    app.register_blueprint(summary, url_prefix='/api')

    return app
