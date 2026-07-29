from flask import Flask, request, jsonify
import requests
import sys

app = Flask(__name__)

# Replace with your actual Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1492214150766657737/UvIhsRYchm-mW6qdQowOtFdq4eQ_djzZdgtTUioFVHRtGvqBK3pEQNTDL-xJcbE0WWC8"

def send_to_discord(data):
    embed = {
        "title": f"Room: {data.get('roomName')}",
        "color": 0x00ff00,
        "fields": [
            {"name": "Player",        "value": data.get("playerName"),      "inline": True},
            {"name": "PlayFab ID",    "value": data.get("playFabId"),       "inline": True},
            {"name": "Photon Nick",   "value": data.get("photonNickname"),  "inline": True},
            {"name": "Players",       "value": f"{data.get('playerCount')}/{data.get('maxPlayers')}", "inline": True}
        ]
    }
    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"Room: {data.get('roomName')}, Player: {data.get('playerName')}", file=sys.stderr)
        send_to_discord(data)  # forward to Discord
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400