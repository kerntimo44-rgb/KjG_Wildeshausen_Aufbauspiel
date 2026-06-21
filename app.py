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
}

state = {}
clients = {}
stopwatches = {}


def default_station(station_number):
    return {
        "name": f"Station {station_number}",
        "occupiedBy": None,
    }


def build_state():
    new_state = copy.deepcopy(DEFAULTS)
    new_state["stations"] = {
        str(station): default_station(station)
        for station in range(1, new_state["stationCount"] + 1)
    }
    new_state["teams"] = {
        str(team): {"occupiedBy": None, "villages": 0, "towns": 0, "cities": 0}
        for team in range(1, new_state["teamCount"] + 1)
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
                "name": old.get("name") or f"Station {station}",
                "occupiedBy": old.get("occupiedBy"),
            }
        else:
            new_stations[key] = default_station(station)
    state["stations"] = new_stations

    state["teams"] = {
        str(team): old_teams.get(str(team), {"occupiedBy": None, "villages": 0, "towns": 0, "cities": 0})
        for team in range(1, int(state["teamCount"]) + 1)
    }

    valid_station_keys = set(state["stations"].keys())
    for key in list(stopwatches.keys()):
        station = key.split(":")[0]
        if station not in valid_station_keys:
            stopwatches.pop(key, None)


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

    if state.get("orgaClientId") == sid:
        state["orgaClientId"] = None

    for station in state["stations"].values():
        if station.get("occupiedBy") == sid:
            station["occupiedBy"] = None

    for team in state["teams"].values():
        if team.get("occupiedBy") == sid:
            team["occupiedBy"] = None

    broadcast_state()


@socketio.on("request_orga")
def request_orga():
    sid = request.sid
    if state.get("orgaClientId") in (None, sid):
        state["orgaClientId"] = sid
        emit("orga_granted", True)
    else:
        emit("orga_granted", False)
    broadcast_state()


@socketio.on("leave_orga")
def leave_orga():
    if state.get("orgaClientId") == request.sid:
        state["orgaClientId"] = None
    broadcast_state()


@socketio.on("update_config")
def update_config(data):
    if state.get("orgaClientId") != request.sid:
        return

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
    if state.get("orgaClientId") != request.sid:
        return

    station_id = str(data.get("station"))
    name = str(data.get("name", "")).strip()

    if station_id in state["stations"]:
        state["stations"][station_id]["name"] = name or f"Station {station_id}"

    broadcast_state()


@socketio.on("reset_game")
def reset_game():
    if state.get("orgaClientId") != request.sid:
        return

    state.clear()
    state.update(build_state())
    stopwatches.clear()
    broadcast_state()


@socketio.on("toggle_round")
def toggle_round():
    if state.get("orgaClientId") != request.sid:
        return

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
    if state.get("orgaClientId") != request.sid:
        return

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
