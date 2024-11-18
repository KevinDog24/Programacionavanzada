from flask import Flask
from .extensions import db, login_manager, migrate
from .models import User
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'routes.signin'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app