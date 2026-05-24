from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

current_command = "NONE"
telemetry_logs = [] 

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
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.05);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        h1 { font-size: 2.5em; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 2px;}
        .status { color: #00FFcc; font-weight: bold; margin-bottom: 30px; font-size: 1.2em; }
        
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
        .btn-red { background-color: #ff416c; color: white; }
        .btn-red:hover { background-color: #ff4b2b; transform: scale(1.05); }
        .btn-green { background-color: #11998e; color: white; }
        .btn-green:hover { background-color: #38ef7d; transform: scale(1.05); }
        
        .data-section {
            background: rgba(0, 0, 0, 0.3);
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
        }
        th { background-color: rgba(255,255,255,0.05); color: #aaa; text-transform: uppercase; font-size: 0.9em;}
        
        /* NEW: DISTINCT STYLES FOR FAULTS VS CRASHES */
        .fault-row { background-color: rgba(255, 165, 0, 0.2); color: #ffcc00; font-weight: bold;}
        .crash-row { background-color: rgba(255, 0, 0, 0.4); color: white; font-weight: bold; animation: pulse 2s infinite;}
        .heartbeat-row { color: #aaa; font-size: 0.9em; }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 0, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Telematics Dashboard</h1>
        <div class="status">Current Command State: <span id="cmd-state">{{ current_command }}</span></div>
        
        <div class="controls">
            <button class="btn-red" onclick="sendCommand('IMMOBILIZE')">Immobilize Vehicle</button>
            <button class="btn-green" onclick="sendCommand('MOBILIZE')">Mobilize Vehicle</button>
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
                <tbody id="event-table-body">
                    </tbody>
            </table>
        </div>
    </div>

    <script>
        function sendCommand(cmd) {
            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmd })
            }).then(response => response.json())
              .then(data => { document.getElementById('cmd-state').innerText = data.command; });
        }

        function fetchLogs() {
            fetch('/api/telemetry')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('event-table-body');
                    tbody.innerHTML = ''; 

                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" style="color:#38ef7d;">No Events Logged Yet.</td></tr>';
                        return;
                    }

                    data.slice().reverse().forEach(log => {
                        let rowClass = 'heartbeat-row'; // Default
                        if (log.event === 'CRASH') rowClass = 'crash-row';
                        if (log.event === 'FAULT') rowClass = 'fault-row';
                        
                        let ecu = log.ecu ? log.ecu : 'SYSTEM';
                        let message = log.message ? log.message : (log.status ? log.status : 'N/A');

                        let row = `<tr class="${rowClass}">
                            <td>${log.timestamp}</td>
                            <td>${log.event}</td>
                            <td>${ecu}</td>
                            <td>${message}</td>
                        </tr>`;
                        tbody.innerHTML += row;
                    });
                });
        }

        setInterval(fetchLogs, 3000);
        fetchLogs(); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, current_command=current_command)

@app.route('/api/command', methods=['GET', 'POST'])
def handle_command():
    global current_command
    if request.method == 'POST':
        data = request.json
        if data and 'command' in data:
            current_command = data['command']
            return jsonify({"status": "success", "command": current_command})
    return jsonify({"command": current_command})

@app.route('/api/telemetry', methods=['GET', 'POST'])
def handle_telemetry():
    global telemetry_logs
    if request.method == 'POST':
        data = request.json
        if data:
            data['timestamp'] = datetime.now().strftime("%H:%M:%S")
            telemetry_logs.append(data)
            if len(telemetry_logs) > 50:
                telemetry_logs.pop(0)
            return jsonify({"status": "logged successfully"}), 200
        return jsonify({"status": "bad request"}), 400
        
    return jsonify(telemetry_logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)