from flask import Flask
from flask_socketio import SocketIO
from config import Config
from api.auth import auth_bp
from api.chats import chats_bp
from api.contacts import contacts_bp
from api.messages import messages_bp
from services.socket_service import init_socket_handlers

app = Flask(__name__)
app.config.from_object(Config)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(chats_bp, url_prefix='/api/chats')
app.register_blueprint(contacts_bp, url_prefix='/api/contacts')
app.register_blueprint(messages_bp, url_prefix='/api/messages')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=Config.SOCKET_CORS_ORIGINS)
init_socket_handlers(socketio)

if __name__ == '__main__':
    socketio.run(app, debug=Config.DEBUG)