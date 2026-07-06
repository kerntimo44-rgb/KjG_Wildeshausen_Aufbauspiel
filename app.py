from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import time
import copy

app = Flask(__name__)
app.config["SECRET_KEY"] = "zeltlager-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

DEFAULTS = {
    "stationCount": 10,
    "gamesPerStation": 2,
    "teamCount": 10,
    "roundCount": 6,
    "roundDurationSec": 15 * 60,
    "gameDurationSec": 60,
    "activeRound": 1,
    "roundRemainingSec": 15 * 60,
    "roundRunning": False,
    "roundLastStartedAt": None,
    "stations": {},
    "teams": {},
    "orgaClientId": None,
    "helpRequests": [],
}

state = {}
clients = {}
stopwatches = {}

CLANS = [
    {"id": "CLAN_Feder", "file": "CLAN_Feder.png", "name": "Huruhuru", "label": "Feder"},
    {"id": "CLAN_Fisch", "file": "CLAN_Fisch.png", "name": "Ika", "label": "Fisch"},
    {"id": "CLAN_Sterne", "file": "CLAN_Sterne.png", "name": "Whetū", "label": "Sterne"},
    {"id": "CLAN_Schildkröte", "file": "CLAN_Schildkröte.png", "name": "Honu", "label": "Schildkröte"},
    {"id": "CLAN_Maske", "file": "CLAN_Maske.png", "name": "Kanohi", "label": "Maske"},
    {"id": "CLAN_Delfin", "file": "CLAN_Delfin.png", "name": "Aihe", "label": "Delfin"},
    {"id": "CLAN_Schiff", "file": "CLAN_Schiff.png", "name": "Waka", "label": "Schiff"},
    {"id": "CLAN_Sonne", "file": "CLAN_Sonne.png", "name": "Rā", "label": "Sonne"},
    {"id": "CLAN_Haken", "file": "CLAN_Haken.png", "name": "Matau", "label": "Haken"},
    {"id": "CLAN_Hibiskus", "file": "CLAN_Hibiskus.png", "name": "Kōkio", "label": "Hibiskus"},
    {"id": "CLAN_Welle", "file": "CLAN_Welle.png", "name": "Ngaru", "label": "Welle"},
]



def default_station(station_number):
    default_names = {
        1: "Holz 1",
        2: "Holz 2",
        3: "Fisch 1",
        4: "Fisch 2",
        5: "Stein 1",
        6: "Stein 2",
        7: "Kokosnuss 1",
        8: "Kokosnuss 2",
        9: "Schilf 1",
        10: "Schilf 2",
    }
    return {
        "name": default_names.get(int(station_number), f"Station {station_number}"),
        "occupiedBy": None,
    }


def build_state():
    new_state = copy.deepcopy(DEFAULTS)
    new_state["stations"] = {
        str(station): default_station(station)
        for station in range(1, new_state["stationCount"] + 1)
    }
    new_state["teams"] = {}
    for team in range(1, new_state["teamCount"] + 1):
        default_clan = CLANS[team - 1] if team - 1 < len(CLANS) else None
        new_state["teams"][str(team)] = {
            "occupiedBy": None,
            "name": default_clan["name"] if default_clan else f"Team {team}",
            "clan": default_clan["id"] if default_clan else None,
            "villages": 0,
            "towns": 0,
            "cities": 0,
        }
    return new_state


state.update(build_state())


def current_round_remaining():
    if not state["roundRunning"] or state["roundLastStartedAt"] is None:
        return max(0, int(state["roundRemainingSec"]))

    elapsed = int(time.time() - state["roundLastStartedAt"])
    return max(0, int(state["roundRemainingSec"]) - elapsed)


def snapshot():
    snap = copy.deepcopy(state)
    snap["clans"] = CLANS
    snap["roundRemainingSec"] = current_round_remaining()
    if snap["roundRemainingSec"] <= 0:
        snap["roundRunning"] = False
    return snap


def broadcast_state():
    socketio.emit("state", snapshot())


def normalize_structure():
    old_stations = state.get("stations", {})
    old_teams = state.get("teams", {})

    new_stations = {}
    for station in range(1, int(state["stationCount"]) + 1):
        key = str(station)
        old = old_stations.get(key, {})
        if isinstance(old, dict):
            new_stations[key] = {
                "name": old.get("name") or default_station(station)["name"],
                "occupiedBy": old.get("occupiedBy"),
            }
        else:
            new_stations[key] = default_station(station)
    state["stations"] = new_stations

    state["teams"] = {
        str(team): old_teams.get(str(team), {"occupiedBy": None, "name": f"Team {team}", "clan": None, "villages": 0, "towns": 0, "cities": 0})
        for team in range(1, int(state["teamCount"]) + 1)
    }

    valid_station_keys = set(state["stations"].keys())
    for key in list(stopwatches.keys()):
        station = key.split(":")[0]
        if station not in valid_station_keys:
            stopwatches.pop(key, None)



def remove_help_requests_for_sid(sid):
    team_ids = [team_id for team_id, team in state["teams"].items() if team.get("occupiedBy") == sid]
    station_ids = [station_id for station_id, station in state["stations"].items() if station.get("occupiedBy") == sid]
    state["helpRequests"] = [
        item for item in state["helpRequests"]
        if not ((item["kind"] == "team" and item["id"] in team_ids) or (item["kind"] == "station" and item["id"] in station_ids))
    ]


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    clients[request.sid] = {"sid": request.sid}
    emit("client_id", request.sid)
    emit("state", snapshot())


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    clients.pop(sid, None)
    remove_help_requests_for_sid(sid)

    for station in state["stations"].values():
        if station.get("occupiedBy") == sid:
            station["occupiedBy"] = None

    for team in state["teams"].values():
        if team.get("occupiedBy") == sid:
            team["occupiedBy"] = None

    broadcast_state()


@socketio.on("request_orga")
def request_orga():
    emit("orga_granted", True)
    broadcast_state()


@socketio.on("leave_orga")
def leave_orga():
    broadcast_state()


@socketio.on("update_config")
def update_config(data):
    state["roundRemainingSec"] = current_round_remaining()

    for key in ["stationCount", "gamesPerStation", "teamCount", "roundCount", "roundDurationSec", "gameDurationSec"]:
        if key in data:
            state[key] = max(1, int(data[key]))

    if "roundDurationSec" in data:
        state["roundRemainingSec"] = int(state["roundDurationSec"])
        state["roundRunning"] = False
        state["roundLastStartedAt"] = None

    normalize_structure()
    broadcast_state()


@socketio.on("update_station_name")
def update_station_name(data):
    station_id = str(data.get("station"))
    name = str(data.get("name", "")).strip()

    if station_id in state["stations"]:
        state["stations"][station_id]["name"] = name or f"Station {station_id}"

    broadcast_state()




@socketio.on("update_team_clan")
def update_team_clan(data):
    team_id = str(data.get("team"))
    clan_id = str(data.get("clan", "")).strip() or None

    if team_id not in state["teams"]:
        return

    if clan_id is not None and not any(clan["id"] == clan_id for clan in CLANS):
        return

    if clan_id is not None:
        for other_id, other_team in state["teams"].items():
            if other_id != team_id and other_team.get("clan") == clan_id:
                return

    state["teams"][team_id]["clan"] = clan_id
    selected = next((clan for clan in CLANS if clan["id"] == clan_id), None)
    if selected:
        state["teams"][team_id]["name"] = selected["name"]

    broadcast_state()


@socketio.on("update_team_name")
def update_team_name(data):
    team_id = str(data.get("team"))
    name = str(data.get("name", "")).strip()

    if team_id in state["teams"]:
        state["teams"][team_id]["name"] = name or f"Team {team_id}"

    broadcast_state()


@socketio.on("set_active_round")
def set_active_round(data):
    try:
        requested_round = int(data.get("round"))
    except (TypeError, ValueError):
        return

    state["activeRound"] = max(1, min(int(state["roundCount"]), requested_round))
    broadcast_state()


@socketio.on("reset_round_timer")
def reset_round_timer():
    state["roundRemainingSec"] = int(state["roundDurationSec"])
    state["roundRunning"] = False
    state["roundLastStartedAt"] = None
    broadcast_state()


@socketio.on("reset_game")
def reset_game():
    state.clear()
    state.update(build_state())
    stopwatches.clear()
    broadcast_state()


@socketio.on("toggle_round")
def toggle_round():
    remaining = current_round_remaining()
    if state["roundRunning"]:
        state["roundRemainingSec"] = remaining
        state["roundRunning"] = False
        state["roundLastStartedAt"] = None
    else:
        if remaining <= 0:
            remaining = int(state["roundDurationSec"])
        state["roundRemainingSec"] = remaining
        state["roundRunning"] = True
        state["roundLastStartedAt"] = time.time()

    broadcast_state()


@socketio.on("next_round")
def next_round():
    state["activeRound"] = min(int(state["roundCount"]), int(state["activeRound"]) + 1)
    state["roundRemainingSec"] = int(state["roundDurationSec"])
    state["roundRunning"] = False
    state["roundLastStartedAt"] = None
    broadcast_state()


@socketio.on("join_station")
def join_station(data):
    station = str(data.get("station"))
    if station in state["stations"] and state["stations"][station].get("occupiedBy") is None:
        state["stations"][station]["occupiedBy"] = request.sid
    broadcast_state()


@socketio.on("join_team")
def join_team(data):
    team_id = str(data.get("team"))
    if team_id in state["teams"] and state["teams"][team_id].get("occupiedBy") is None:
        state["teams"][team_id]["occupiedBy"] = request.sid
    broadcast_state()


@socketio.on("leave_slot")
def leave_slot():
    sid = request.sid
    remove_help_requests_for_sid(sid)
    for station in state["stations"].values():
        if station.get("occupiedBy") == sid:
            station["occupiedBy"] = None

    for team in state["teams"].values():
        if team.get("occupiedBy") == sid:
            team["occupiedBy"] = None

    broadcast_state()


@socketio.on("update_team")
def update_team(data):
    team_id = str(data.get("team"))
    action = data.get("action")

    if team_id not in state["teams"]:
        return

    team = state["teams"][team_id]
    if team.get("occupiedBy") != request.sid:
        return

    if action == "village_plus":
        team["villages"] += 1
    elif action == "village_minus":
        team["villages"] = max(0, team["villages"] - 1)
    elif action == "town_plus" and team["villages"] > 0:
        team["villages"] -= 1
        team["towns"] += 1
    elif action == "town_minus" and team["towns"] > 0:
        team["towns"] -= 1
        team["villages"] += 1
    elif action == "city_plus" and team["towns"] > 0:
        team["towns"] -= 1
        team["cities"] += 1
    elif action == "city_minus" and team["cities"] > 0:
        team["cities"] -= 1
        team["towns"] += 1

    broadcast_state()



@socketio.on("toggle_help_request")
def toggle_help_request(data):
    kind = str(data.get("kind"))
    entity_id = str(data.get("id"))

    if kind not in ("team", "station"):
        return

    if kind == "team":
        entity = state["teams"].get(entity_id)
        if not entity or entity.get("occupiedBy") != request.sid:
            return
        label = entity.get("name") or f"Team {entity_id}"
    else:
        entity = state["stations"].get(entity_id)
        if not entity or entity.get("occupiedBy") != request.sid:
            return
        label = entity.get("name") or f"Station {entity_id}"

    existing = next((item for item in state["helpRequests"] if item["kind"] == kind and item["id"] == entity_id), None)

    if existing:
        state["helpRequests"] = [
            item for item in state["helpRequests"]
            if not (item["kind"] == kind and item["id"] == entity_id)
        ]
    else:
        state["helpRequests"].append({
            "kind": kind,
            "id": entity_id,
            "label": label,
            "status": "red",
            "createdAt": time.time(),
        })

    broadcast_state()


@socketio.on("helper_toggle_help")
def helper_toggle_help(data):
    kind = str(data.get("kind"))
    entity_id = str(data.get("id"))

    for item in list(state["helpRequests"]):
        if item["kind"] == kind and item["id"] == entity_id:
            if item.get("status") == "red":
                item["status"] = "yellow"
            else:
                state["helpRequests"] = [
                    req for req in state["helpRequests"]
                    if not (req["kind"] == kind and req["id"] == entity_id)
                ]
            break

    broadcast_state()



def stopwatch_snapshot():
    now = time.time()
    result = {}
    for key, sw in stopwatches.items():
        remaining = sw["remaining"]
        if sw["running"]:
            remaining = max(0, int(sw["remaining"] - (now - sw["startedAt"])))
            if remaining <= 0:
                sw["running"] = False
                sw["remaining"] = 0
                sw["startedAt"] = None
        result[key] = {"remaining": int(remaining), "running": sw["running"]}
    return result


@socketio.on("get_stopwatches")
def get_stopwatches():
    emit("stopwatches", stopwatch_snapshot())


@socketio.on("toggle_stopwatch")
def toggle_stopwatch(data):
    station = str(data.get("station"))
    watch = str(data.get("watch"))
    key = f"{station}:{watch}"

    owner = state["stations"].get(station, {}).get("occupiedBy")
    if owner != request.sid:
        return

    sw = stopwatches.setdefault(key, {"remaining": int(state["gameDurationSec"]), "running": False, "startedAt": None})
    now = time.time()

    if sw["running"]:
        sw["remaining"] = max(0, int(sw["remaining"] - (now - sw["startedAt"])))
        sw["running"] = False
        sw["startedAt"] = None
    else:
        if sw["remaining"] <= 0:
            sw["remaining"] = int(state["gameDurationSec"])
        sw["running"] = True
        sw["startedAt"] = now

    socketio.emit("stopwatches", stopwatch_snapshot())


@socketio.on("reset_stopwatch")
def reset_stopwatch(data):
    station = str(data.get("station"))
    watch = str(data.get("watch"))
    key = f"{station}:{watch}"

    owner = state["stations"].get(station, {}).get("occupiedBy")
    if owner != request.sid:
        return

    stopwatches[key] = {"remaining": int(state["gameDurationSec"]), "running": False, "startedAt": None}
    socketio.emit("stopwatches", stopwatch_snapshot())


def ticker():
    while True:
        socketio.sleep(1)
        if state.get("roundRunning"):
            remaining = current_round_remaining()
            if remaining <= 0:
                state["roundRemainingSec"] = 0
                state["roundRunning"] = False
                state["roundLastStartedAt"] = None
            broadcast_state()
        socketio.emit("stopwatches", stopwatch_snapshot())


socketio.start_background_task(ticker)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
