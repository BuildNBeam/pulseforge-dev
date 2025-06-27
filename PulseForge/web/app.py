from flask import Flask
from flask_socketio import SocketIO
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global SocketIO instance
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')

def create_app():
    """Create and configure Flask app"""
    import os
    
    # Get the absolute path to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # Initialize SocketIO with app
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register routes
    from web.routes import main
    app.register_blueprint(main)
    
    # Register SocketIO events
    from web.socketio_events import register_socketio_events
    register_socketio_events(socketio)
    
    logger.info("Flask app created and configured")
    return app
