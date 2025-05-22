import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory database (replace with real DB in production)
users = {}
chats = {}
contacts = {}
messages = {}

class User:
    def __init__(self, phone_number, name, profile_pic=None):
        self.id = str(uuid.uuid4())
        self.phone_number = phone_number
        self.name = name
        self.profile_pic = profile_pic
        self.status = "Hey there! I'm using WhatsApp Clone"
        self.last_seen = datetime.now()
        self.contacts = []

class Chat:
    def __init__(self, chat_type, participants):
        self.id = str(uuid.uuid4())
        self.type = chat_type  # 'private' or 'group'
        self.participants = participants
        self.messages = []
        self.created_at = datetime.now()

class Message:
    def __init__(self, sender_id, content, message_type="text"):
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.content = content
        self.type = message_type  # 'text', 'image', 'video', etc.
        self.timestamp = datetime.now()
        self.status = "sent"  # sent, delivered, read

# API Endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    phone_number = data.get('phone_number')
    name = data.get('name')
    
    if phone_number in users:
        return jsonify({"error": "User already exists"}), 400
    
    user = User(phone_number, name)
    users[phone_number] = user
    return jsonify({"user_id": user.id, "status": "success"}), 201

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    # In production, integrate with SMS service like Twilio
    phone_number = request.json.get('phone_number')
    otp = "123456"  # Generate random OTP in production
    return jsonify({"status": "OTP sent", "otp": otp}), 200

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    user_id = request.args.get('user_id')
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    user = users[user_id]
    return jsonify({"contacts": user.contacts}), 200

@app.route('/api/chats', methods=['GET'])
def get_chats():
    user_id = request.args.get('user_id')
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    
    user_chats = [chat for chat in chats.values() if user_id in chat.participants]
    return jsonify({"chats": [chat.id for chat in user_chats]}), 200

@app.route('/api/messages', methods=['GET'])
def get_messages():
    chat_id = request.args.get('chat_id')
    if chat_id not in chats:
        return jsonify({"error": "Chat not found"}), 404
    
    chat = chats[chat_id]
    return jsonify({"messages": chat.messages}), 200

# WebSocket Handlers
@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data['chat_id']
    sender_id = data['sender_id']
    content = data['content']
    
    if chat_id not in chats:
        emit('error', {'message': 'Chat not found'})
        return
    
    message = Message(sender_id, content)
    chats[chat_id].messages.append(message)
    
    # Notify all participants in the chat
    for participant in chats[chat_id].participants:
        emit('receive_message', {
            'chat_id': chat_id,
            'message': {
                'id': message.id,
                'sender_id': sender_id,
                'content': content,
                'timestamp': message.timestamp.isoformat(),
                'status': message.status
            }
        }, room=participant)

@socketio.on('connect')
def handle_connect():
    user_id = request.args.get('user_id')
    if user_id in users:
        users[user_id].last_seen = datetime.now()
        emit('connection_success', {'user_id': user_id})

# Command Line Interface (Simple demo)
def cli_interface():
    print("Welcome to WhatsApp Clone (Python Edition)")
    
    while True:
        print("\nOptions:")
        print("1. Register")
        print("2. Send Message")
        print("3. View Chats")
        print("4. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            phone = input("Enter phone number: ")
            name = input("Enter your name: ")
            user = User(phone, name)
            users[phone] = user
            print(f"Registered successfully! Your ID: {user.id}")
            
        elif choice == "2":
            sender = input("Your phone number: ")
            if sender not in users:
                print("User not found. Please register first.")
                continue
                
            receiver = input("Recipient phone number: ")
            if receiver not in users:
                print("Recipient not found.")
                continue
                
            # Create or find chat
            chat_id = None
            for chat in chats.values():
                if set([sender, receiver]) == set(chat.participants):
                    chat_id = chat.id
                    break
                    
            if not chat_id:
                new_chat = Chat('private', [sender, receiver])
                chats[new_chat.id] = new_chat
                chat_id = new_chat.id
                
            message = input("Your message: ")
            msg = Message(sender, message)
            chats[chat_id].messages.append(msg)
            print("Message sent!")
            
        elif choice == "3":
            phone = input("Your phone number: ")
            if phone not in users:
                print("User not found.")
                continue
                
            print("\nYour Chats:")
            for chat in chats.values():
                if phone in chat.participants:
                    other_user = [p for p in chat.participants if p != phone][0]
                    print(f"Chat with {users[other_user].name} ({other_user})")
                    for msg in chat.messages:
                        prefix = "You: " if msg.sender_id == phone else f"{users[msg.sender_id].name}: "
                        print(f"{prefix}{msg.content}")
                    print("---")
                    
        elif choice == "4":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Try again.")

if __name__ == '__main__':
    # Start the CLI interface or the server
    mode = input("Run as (1) CLI or (2) Server? ")
    
    if mode == "1":
        cli_interface()
    else:
        print("Starting server on http://localhost:5000")
        socketio.run(app, debug=True)