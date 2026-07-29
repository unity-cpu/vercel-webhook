import os
import sys
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
API_SECRET = os.environ.get("API_SECRET")


def handle_webhook():
    # Optional shared-secret check so randoms can't spam your webhook
    if API_SECRET:
        provided = request.headers.get("x-api-key")
        if provided != API_SECRET:
            return jsonify({"status": "error", "message": "unauthorized"}), 401

    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL is not set", file=sys.stderr)
        return jsonify({"status": "error", "message": "server misconfigured"}), 500

    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"bad json: {e}"}), 400

    room_name = data.get("roomName")
    if not room_name:
        return jsonify({"status": "error", "message": "missing roomName"}), 400

    player_name = data.get("playerName", "Unknown")
    play_fab_id = data.get("playFabId", "Unknown")
    photon_nickname = data.get("photonNickname", "Unknown")
    player_count = data.get("playerCount", "?")
    max_players = data.get("maxPlayers", "?")

    embed = {
        "title": "Player Joined Room",
        "fields": [
            {"name": "Room Name", "value": str(room_name), "inline": True},
            {"name": "Name In Playfab", "value": str(player_name), "inline": True},
            {"name": "In Game Name", "value": str(photon_nickname), "inline": True},
            {"name": "PlayFab ID", "value": str(play_fab_id), "inline": True},
            {"name": "Players in Lobby", "value": f"{player_count} / {max_players}", "inline": True},
        ],
        "footer": {"text": "room logs made by unity.lolz"},
    }

    try:
        discord_res = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"embeds": [embed]},
            timeout=10,
        )
        if discord_res.status_code >= 300:
            print(f"Discord webhook error: {discord_res.status_code} {discord_res.text}", file=sys.stderr)
            return jsonify({"status": "error", "message": "failed to notify discord"}), 502
    except Exception as e:
        print(f"Error forwarding to Discord: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "internal error"}), 500

    print(f"Room: {room_name}, Player: {player_name}, PlayFabID: {play_fab_id}", file=sys.stderr)
    return jsonify({"status": "ok"}), 200


# Vercel routes the *whole* incoming path to this file, so we accept both
# "/" and "/api/webhook" (and anything else) to be safe regardless of how
# the URL is written on the Unity side.
@app.route("/", methods=["POST"])
def webhook_root():
    return handle_webhook()


@app.route("/<path:_path>", methods=["POST"])
def webhook_any(_path):
    return handle_webhook()