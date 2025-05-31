from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()
from flask import Flask, request
from langchain_chat import Chat

app = Flask(__name__)
socketio = SocketIO(app,async_mode="eventlet",async_handlers=True)

ChatSessions = {}

@socketio.on('connect')
def handle_connect():
    """
    Handle a new WebSocket connection.
    Initializes a new Chat instance and chat history for the connecting client
    and stores it in the ChatSessions dictionary using the session ID (SID).
    """
    sid = request.sid
    ChatSessions[sid] = {'chat_instance':Chat(),'chat_history':[]}
    print(f"Chat Connected for SID : {sid}",)

@socketio.on('message')
def handle_message(user_input):
    """
    Handle incoming chat messages from the client.
    Forwards the message to corresponding Chat instance, receives a response,
    updates the chat history, and emits the response back to the client.
    """
    sid = request.sid 
    try:
        message = user_input.get('message','')
        print(f"Message from {sid} : {message}")
        chat = ChatSessions[sid]['chat_instance']
        response, chat_history = chat.chat(message)
        ChatSessions[sid]['chat_history'] = chat_history
        print(f"UPDATED CHAT HISTORY : ",chat_history)
        response_obj = {"message":response}
        emit('response',response_obj)

    except Exception as e:
        print(f"Error SID: {sid} | {e}")
        emit('error', {'error': str(e)})

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle WebSocket disconnection.
    Cleans up the ChatSessions dictionary by removing the disconnected client's session.
    """
    sid = request.sid
    if sid in ChatSessions:
        del ChatSessions[sid]
    print(f"Chat Disconnected for SID : {sid}",)

if __name__ == '__main__':
    print('Chat is live')
    socketio.run(app, host="0.0.0.0", port=3090, debug=False)