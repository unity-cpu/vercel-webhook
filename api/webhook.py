from flask import Flask, request, jsonify
import json
import sys

app = Flask(__name__)

@app.route('/api/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        # You can do anything with the data: log it, forward to Discord, etc.
        print(f"Room: {data.get('roomName')}, Player: {data.get('playerName')}, PlayFabID: {data.get('playFabId')}", file=sys.stderr)

        # Example: if you want to forward to Discord, uncomment the next line
        # send_to_discord(data)

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400