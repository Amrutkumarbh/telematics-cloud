"""
app.py  -  Telematics Cloud Server
Deployed on Render.com (free tier)

Fixes applied vs original:
  1. CRITICAL - Render free-tier spin-down resets in-memory state.
     current_command and telemetry_logs are now persisted to a flat
     JSON file (data.json) on every write. On startup the file is
     loaded back so the command state and logs survive restarts.
     Without this: an immobilized vehicle auto-mobilizes on server
     spin-up because current_command resets to "NONE".

  2. THREADING - replaced bare list + global with a threading.Lock
     so concurrent POST requests from the STM32 (5s poll + fault
     uploads) cannot corrupt telemetry_logs or current_command.
     Also works correctly under gunicorn single-worker (default on
     Render free tier).

  3. MINOR - pop(0) on a list is O(n). Replaced with collections.deque
     (maxlen=100) which drops from the left in O(1). Limit raised to
     100 events so the dashboard has more history.

  4. MINOR - added /api/status endpoint so the STM32 or a monitoring
     script can confirm the server is alive without triggering a full
     telemetry fetch.

  5. Dashboard auto-refresh reduced from 3000ms to 2000ms to show
     faults faster.

  6. Event row colours extended: FAULT rows are orange/yellow,
     CRASH rows pulse red, HEARTBEAT rows are dimmed grey.
     All other events (BODY, ACK, etc.) are white default.

  7. Timestamp now includes date (YYYY-MM-DD HH:MM:SS) and is natively
     locked to IST (UTC+5:30) so logs are always accurate.

  8. "No Events Logged Yet" message preserved and centred.
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timezone, timedelta
from collections import deque
import threading
import json
import os

app = Flask(__name__)

# Define IST offset (UTC + 5 hours 30 mins)
IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------
DATA_FILE = "data.json"
_lock = threading.Lock()

def _load_state():
    """Load persisted state from disk on startup."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                return d.get("command", "NONE"), deque(d.get("logs", []), maxlen=100)
        except Exception:
            pass
    return "NONE", deque(maxlen=100)

def _save_state(command, logs):
    """Persist current state to disk. Called inside _lock."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"command": command, "logs": list(logs)}, f)
    except Exception as e:
        app.logger.error(f"Failed to save state: {e}")

# Load state at startup (survives Render spin-down restarts)
current_command, telemetry_logs = _load_state()

# ---------------------------------------------------------------
# HTML Dashboard
# ---------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telematics Command Center</title>
    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            background: rgba(255,255,255,0.05);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.37);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.18);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        .status {
            color: #00FFcc;
            font-weight: bold;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
        }
        button {
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .btn-red   { background-color: #ff416c; color: white; }
        .btn-red:hover   { background-color: #ff4b2b; transform: scale(1.05); }
        .btn-green { background-color: #11998e; color: white; }
        .btn-green:hover { background-color: #38ef7d; transform: scale(1.05); }

        .data-section {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            text-align: center;
            word-break: break-word;
        }
        th {
            background-color: rgba(255,255,255,0.05);
            color: #aaa;
            text-transform: uppercase;
            font-size: 0.9em;
        }

        /* Event row colour coding */
        .crash-row {
            background-color: rgba(255,0,0,0.4);
            color: white;
            font-weight: bold;
            animation: pulse 2s infinite;
        }
        .fault-row {
            background-color: rgba(255,165,0,0.2);
            color: #ffcc00;
            font-weight: bold;
        }
        .heartbeat-row { color: #777; font-size: 0.9em; }
        .default-row   { color: #ccc; }

        @keyframes pulse {
            0%   { box-shadow: 0 0 0 0   rgba(255,0,0,0.7); }
            70%  { box-shadow: 0 0 0 10px rgba(255,0,0,0); }
            100% { box-shadow: 0 0 0 0   rgba(255,0,0,0); }
        }

        #live-dot {
            display: inline-block;
            width: 10px; height: 10px;
            border-radius: 50%;
            background: #38ef7d;
            margin-left: 8px;
            animation: blink 1s step-start infinite;
        }
        @keyframes blink { 50% { opacity: 0; } }
    </style>
</head>
<body>
<div class="container">
    <h1>Telematics Dashboard</h1>
    <div class="status">
        Current Command State: <span id="cmd-state">{{ current_command }}</span>
        <span id="live-dot"></span>
    </div>

    <div class="controls">
        <button class="btn-red"   onclick="sendCommand('IMMOBILIZE')">Immobilize Vehicle</button>
        <button class="btn-green" onclick="sendCommand('MOBILIZE')"  >Mobilize Vehicle</button>
    </div>

    <div class="data-section">
        <h2>Live Vehicle Event Log</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Event Type</th>
                    <th>Source ECU</th>
                    <th>Message / Details</th>
                </tr>
            </thead>
            <tbody id="event-table-body"></tbody>
        </table>
    </div>
</div>

<script>
    function sendCommand(cmd) {
        fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cmd })
        })
        .then(r => r.json())
        .then(data => { document.getElementById('cmd-state').innerText = data.command; });
    }

    function fetchLogs() {
        fetch('/api/telemetry')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('event-table-body');
            tbody.innerHTML = '';

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="color:#38ef7d; text-align:center;">No Events Logged Yet.</td></tr>';
                return;
            }

            // Show newest first
            data.slice().reverse().forEach(log => {
                let rowClass = 'default-row';
                if (log.event === 'CRASH')     rowClass = 'crash-row';
                else if (log.event === 'FAULT') rowClass = 'fault-row';
                else if (log.event === 'HEARTBEAT') rowClass = 'heartbeat-row';

                const ecu     = log.ecu     || 'SYSTEM';
                const message = log.message || log.status || 'N/A';

                tbody.innerHTML += `<tr class="${rowClass}">
                    <td>${log.timestamp}</td>
                    <td>${log.event}</td>
                    <td>${ecu}</td>
                    <td>${message}</td>
                </tr>`;
            });
        })
        .catch(() => {});  // Silently ignore network errors on auto-refresh
    }

    // Also refresh the command state label every 2s
    function fetchCommandState() {
        fetch('/api/command')
        .then(r => r.json())
        .then(data => { document.getElementById('cmd-state').innerText = data.command; })
        .catch(() => {});
    }

    setInterval(fetchLogs,         2000);   // Refresh event log every 2s
    setInterval(fetchCommandState, 2000);   // Keep command label in sync
    fetchLogs();
    fetchCommandState();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------
# Routes
# ---------------------------------------------------------------

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, current_command=current_command)

@app.route('/api/command', methods=['GET', 'POST'])
def handle_command():
    global current_command
    if request.method == 'POST':
        data = request.get_json(silent=True, force=True)
        if data and 'command' in data:
            with _lock:
                current_command = data['command']
                _save_state(current_command, telemetry_logs)
            return jsonify({"status": "success", "command": current_command})
        return jsonify({"status": "bad request"}), 400
    # GET - returns current command (polled by STM32 every 5s)
    return jsonify({"command": current_command})

@app.route('/api/telemetry', methods=['GET', 'POST'])
def handle_telemetry():
    global telemetry_logs
    if request.method == 'POST':
        data = request.get_json(silent=True, force=True)  # force=True accepts any content-type
        if data:
            # Added IST Offset here
            data['timestamp'] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
            with _lock:
                telemetry_logs.append(data)
                _save_state(current_command, telemetry_logs)
            return jsonify({"status": "logged successfully"}), 200
        return jsonify({"status": "bad request"}), 400

    # GET - returns full log list (consumed by dashboard JS)
    with _lock:
        logs = list(telemetry_logs)
    return jsonify(logs)

@app.route('/api/status', methods=['GET'])
def status():
    """Health-check endpoint. STM32 or monitoring can poll this."""
    with _lock:
        count = len(telemetry_logs)
    return jsonify({
        "status": "online",
        "current_command": current_command,
        "log_count": count,
        "server_time": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)