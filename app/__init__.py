import os
from flask import Flask
from .db import init_db
def create_app():
    app=Flask(__name__,instance_relative_config=True)
    app.config["SECRET_KEY"]=os.environ.get("SECRET_KEY","dev-change-this-secret")
    app.config["MAX_CONTENT_LENGTH"]=20*1024*1024
    os.makedirs(app.instance_path,exist_ok=True)
    init_db(app)
    from .auth import auth_bp
    from .main import main_bp
    app.register_blueprint(auth_bp);app.register_blueprint(main_bp)
    return app
