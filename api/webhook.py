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
    "6F4FBE2BCA16068A",
    "B80667DDCD44DC17",
    "BF29B79A2B400090",
    "DB8E46A11F243DD3",
    "DD84C718E8AFD777",
    "B716F79A9FC37CC9",
    "59FE193D73752516",
    "5433C00BD5343624",
    "56BAE470B62F4CDD",
    "5ADD21B0BF6FB425",
    "CDAD910551C5B3C5",
    "BB75C720D543C50C",
    "EA12FC6A4F8AF723",
    "2A4D748DEE715B68",
    "4AB371870F86220B",
    "CEF3083A3BE0F883",
    "532CC7565FB89085",
    "7F5D7550CC93FFE6",
    "A1E0B337A62E068E",
    "35764A5E18580CF",
    "8804634281761F0",
    "B5346D0LCA3982424",   # ⚠️ contains 'L' — verify if correct
    "4F5C99FA420D8B74",
    "79598F060F96210E",
    "12B8C250B9656538",
    "C7FA6FECFEAE36F0",
    "A8750682ABA4DDD1",
    "E7DF087A7D57AA49",
    "71469BA4796CD3E4",
    "5433C00BD5343624",    # duplicate of Jax (harmless)
    "E2B0AC15801DC134",
}

# ─── Staff names mapping (PlayFab ID → your custom nickname) ─────
STAFF_NAMES = {
    "6F4FBE2BCA16068A": " ",
    "B80667DDCD44DC17": "Tempted",
    "BF29B79A2B400090": "Milk",
    "DB8E46A11F243DD3": "purplegirl",
    "DD84C718E8AFD777": "SOT",
    "B716F79A9FC37CC9": "DADDY TOAST :33",
    "59FE193D73752516": "Hasser",
    "5433C00BD5343624": "Jax",
    "56BAE470B62F4CDD": "Notagirl",
    "5ADD21B0BF6FB425": "sandman",
    "CDAD910551C5B3C5": "Cl0udz",
    "BB75C720D543C50C": "JAXJR",
    "EA12FC6A4F8AF723": "PRINCESS",
    "2A4D748DEE715B68": "FLOWERY BOI",
    "4AB371870F86220B": "NASTY PLEMBA",
    "CEF3083A3BE0F883": "Techno",
    "532CC7565FB89085": "MOMMY FLOWERS :3",
    "7F5D7550CC93FFE6": "UNDERAGE GUINEA",
    "A1E0B337A62E068E": "crazy",
    "35764A5E18580CF": "cat",
    "8804634281761F0": "CASS",
    "B5346D0LCA3982424": "GUINEA",
    "4F5C99FA420D8B74": "TABLE THE FATTY",
    "79598F060F96210E": "draco the fatty",
    "12B8C250B9656538": " ",
    "C7FA6FECFEAE36F0": "frog",
    "A8750682ABA4DDD1": "GAY BOY SWAG",
    "E7DF087A7D57AA49": "i love dada crazy -PRINCE",
    "71469BA4796CD3E4": "BUNNY",
    "E2B0AC15801DC134": "VEXT",
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
            {"name": "Players in Lobby", "value": f"{player_count} / {max_players}", "inline": True},
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