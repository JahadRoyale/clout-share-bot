from flask import Flask, request, jsonify
import subprocess
import json

app = Flask(__name__)

@app.route('/api/share', methods=['POST'])
def trigger_share():
    data = request.json or {}
    target_link = data.get('link')
    shares_per_bot = data.get('shares_per_bot', 10)
    bots = data.get('bots', [])
    
    if not target_link or not bots:
        return jsonify({"success": False, "error": "Missing target link or bot payload"}), 400

    payload_str = json.dumps({
        'link': target_link,
        'shares_per_bot': shares_per_bot,
        'bots': bots
    })

    # Spawn asynchronous worker process
    subprocess.Popen(["python", "BotShare.py", payload_str])
    
    return jsonify({"success": True, "message": "Batch execution started"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
