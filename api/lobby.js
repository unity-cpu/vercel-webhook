from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"Room: {data.get('roomName')}, Player: {data.get('playerName')}, PlayFabID: {data.get('playFabId')}", file=sys.stderr)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400