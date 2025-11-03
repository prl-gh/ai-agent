import json
from flask import Flask, request, jsonify
from stock_agent_service import StockInfoAgent

app = Flask(__name__)
agent = StockInfoAgent()

@app.route('/query', methods=['POST'])
def query_agent():
    user_query = request.json.get('query')
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        response = agent.process_user_query(user_query)
        return jsonify({"response": response}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)