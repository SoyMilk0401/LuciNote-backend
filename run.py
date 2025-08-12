import os
from app import create_app, db

config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name)

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run()
