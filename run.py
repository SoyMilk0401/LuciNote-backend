import os
from app import create_app, db

# 환경 변수로부터 설정 이름을 가져오거나, 기본값으로 'development' 사용
config_name = os.getenv('FLASK_CONFIG') or 'development'
app = create_app(config_name)

if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run()
