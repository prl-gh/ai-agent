from flask import Flask, render_template, request, jsonify
from stock_agent_service import StockInfoAgent
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
agent = StockInfoAgent()

# Set up the web console callback
def send_to_client(message):
    socketio.emit('console_output', {'message': message})
agent.console.set_output_callback(send_to_client)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_query = request.json.get('query')
    response = agent.process_user_query(user_query)
    return jsonify({'response': response})

@socketio.on('user_input')
def handle_user_input(data):
    user_input = data.get('input')
    agent.console.provide_input(user_input)

if __name__ == '__main__':
    socketio.run(app, debug=True)