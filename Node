# node.py - Fuldt distribueret Kubernetes Pod (matcher UML på side 3, 4 og 10)
import os, socket, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Udled proces-ID (P1..PN) fra Kubernetes StatefulSet hostname (bully-0 -> P1)
HOSTNAME = socket.gethostname()
MY_ID = int(HOSTNAME.split("-")[-1]) + 1 if "-" in HOSTNAME and HOSTNAME.split("-")[-1].isdigit() else int(os.environ.get("PROCESS_ID", 1))
TOTAL_NODES = int(os.environ.get("TOTAL_NODES", 6))
SERVICE_NAME = os.environ.get("SERVICE_NAME", "bully-svc")
TIMEOUT = 0.4

state = {"role": "FOLLOWER", "leader": TOTAL_NODES, "crashed": False}

def peer_url(pid: int, path: str) -> str:
    return f"http://bully-{pid - 1}.{SERVICE_NAME}:5000{path}"

def broadcast_coordinator() -> int:
    """Svarer til LEADER state Entry på side 3: Broadcast COORDINATOR til levende peers."""
    state["role"] = "LEADER"
    state["leader"] = MY_ID
    coord_msgs = 0
    for pid in range(1, TOTAL_NODES + 1):
        if pid != MY_ID:
            try:
                r = requests.post(peer_url(pid, "/msg/coordinator"), json={"leader": MY_ID}, timeout=TIMEOUT)
                if r.status_code == 200:
                    coord_msgs += 1
            except requests.RequestException:
                pass
    return coord_msgs

@app.route("/msg/election", methods=["POST"])
def rx_election():
    if state["crashed"]:
        return "Crashed", 503
    return jsonify({"reply": "OK", "from": MY_ID}), 200

@app.route("/msg/alive", methods=["GET"])
def rx_are_you_alive():
    """Matcher State Diagram (side 3): Rx 'ARE YOU ALIVE?' from lower ID -> transition to LEADER."""
    if state["crashed"]:
        return "Crashed", 503
    # Da lavere node poller top-down, ved denne node nu, at ingen højere noder lever!
    coord_msgs = broadcast_coordinator()
    return jsonify({"reply": "YES", "from": MY_ID, "coord_messages": coord_msgs}), 200

@app.route("/msg/coordinator", methods=["POST"])
def rx_coordinator():
    if state["crashed"]:
        return "Crashed", 503
    state["role"] = "FOLLOWER"
    state["leader"] = request.json["leader"]
    return jsonify({"ack": True}), 200

@app.route("/election/original", methods=["POST"])
def start_original():
    """Matcher UML Original Bully (side 10) og bully_election() (side 5-6)."""
    if state["crashed"]:
        return jsonify({"error": "Initiator is crashed"}), 400
    messages = 0
    answers = []
    for pid in range(MY_ID + 1, TOTAL_NODES + 1):
        messages += 1  # ELECTION
        try:
            r = requests.post(peer_url(pid, "/msg/election"), json={"from": MY_ID}, timeout=TIMEOUT)
            if r.status_code == 200:
                messages += 1  # OK
                answers.append(pid)
        except requests.RequestException:
            pass

    if not answers:
        messages += broadcast_coordinator()
        return jsonify({"leader": MY_ID, "messages": messages}), 200

    # Handover til højeste proces i answers (f.eks. P2 -> P5 på side 10)
    highest = max(answers)
    r = requests.post(peer_url(highest, "/election/original"), timeout=5.0).json()
    return jsonify({"leader": r["leader"], "messages": messages + r["messages"]}), 200

@app.route("/election/improved", methods=["POST"])
def start_improved():
    """Matcher UML Improved Bully (side 3 & 4) og improved_bully() (side 7-8)."""
    if state["crashed"]:
        return jsonify({"error": "Initiator is crashed"}), 400
    state["role"] = "POLLING"
    messages = 0

    for target_id in range(TOTAL_NODES, MY_ID, -1):
        messages += 1  # "ARE YOU ALIVE?"
        try:
            r = requests.get(peer_url(target_id, "/msg/alive"), timeout=TIMEOUT)
            if r.status_code == 200:
                messages += 1  # "YES"
                data = r.json()
                state["role"] = "FOLLOWER"
                state["leader"] = target_id
                # Læg de COORDINATOR-beskeder til, som den nye leader (P5) netop har broadcastet
                return jsonify({"leader": target_id, "messages": messages + data["coord_messages"]}), 200
        except requests.RequestException:
            pass  # No response (target_id -= 1)

    # target_id == self (Ingen højere noder lever -> denne node bliver selv LEADER)
    messages += broadcast_coordinator()
    return jsonify({"leader": MY_ID, "messages": messages}), 200

@app.route("/crash", methods=["POST"])
def set_crash():
    state["crashed"] = bool(request.json.get("crashed", True))
    return jsonify({"id": MY_ID, "crashed": state["crashed"]}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
