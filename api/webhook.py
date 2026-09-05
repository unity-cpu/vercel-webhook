import os
import sys
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Webhook URLs
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STAFF_WEBHOOK_URL = os.environ.get("STAFF_WEBHOOK_URL")
API_SECRET = os.environ.get("API_SECRET", "")

# ─── Hardcoded staff PlayFab IDs ─────────────────────────────────
STAFF_IDS = {
    "369232A6ECBC8ABD",
}

# ─── Staff names mapping (PlayFab ID → your custom nickname) ─────
STAFF_NAMES = {
    "369232A6ECBC8ABD": "frog",
}


def handle_webhook():
    # Optional shared-secret check
    if API_SECRET:
        provided = request.headers.get("x-api-key")
        if provided != API_SECRET:
            return jsonify({"status": "error", "message": "unauthorized"}), 401

    # Parse JSON from Unity
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

    # Check if player is staff
    is_staff = play_fab_id in STAFF_IDS

    if is_staff:
        target_webhook = STAFF_WEBHOOK_URL
        if not target_webhook:
            print("STAFF_WEBHOOK_URL not set, falling back to main webhook", file=sys.stderr)
            target_webhook = DISCORD_WEBHOOK_URL
        print(f"Staff join detected: {play_fab_id}", file=sys.stderr)
        # Use custom name if available, otherwise fallback to PlayFab display name
        display_name = STAFF_NAMES.get(play_fab_id, player_name)
    else:
        target_webhook = DISCORD_WEBHOOK_URL
        display_name = player_name

    if not target_webhook:
        print("No webhook URL configured", file=sys.stderr)
        return jsonify({"status": "error", "message": "server misconfigured"}), 500

    # Build embed
    embed = {
        "title": "Staff Member Joined Room" if is_staff else "Player Joined Room",
        "fields": [
            {"name": "Room Name",        "value": str(room_name),          "inline": True},
            {"name": "Staff Name" if is_staff else "Name In Playfab",
                                         "value": str(display_name),       "inline": True},
            {"name": "In Game Name",     "value": str(photon_nickname),    "inline": True},
            {"name": "PlayFab ID",       "value": str(play_fab_id),        "inline": True},
            {"name": "Players in Lobby", "value": f"{player_count} / {max_players} \n <@1443807588864098316>", "inline": True},
        ],
        "footer": {"text": "room logs made by unity.lolz"},
    }

    if is_staff:
        embed["color"] = 0x9b59b6   # purple

    # Send to Discord
    try:
        discord_res = requests.post(
            target_webhook,
            json={"embeds": [embed]},
            timeout=10,
        )
        if discord_res.status_code >= 300:
            print(f"Discord error: {discord_res.status_code} {discord_res.text}", file=sys.stderr)
            return jsonify({"status": "error", "message": "failed to notify discord"}), 502
    except Exception as e:
        print(f"Discord send error: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "internal error"}), 500

    print(f"Logged – Room: {room_name}, Staff: {display_name} ({play_fab_id})", file=sys.stderr)
    return jsonify({"status": "ok"}), 200


# Vercel routes all POST paths here
@app.route("/", methods=["POST"])
def webhook_root():
    return handle_webhook()


@app.route("/<path:_path>", methods=["POST"])
def webhook_any(_path):
    return handle_webhook()
