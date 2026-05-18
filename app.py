from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# GLOBAL VEHICLE STATE
vehicle_command = "NONE"
vehicle_fault = "NONE"
crash_status = 0

# =========================
# DASHBOARD PAGE
# =========================

@app.route('/')
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Telematics Dashboard</title>
        <style>
            body {
                font-family: Arial;
                background: #111;
                color: white;
                text-align: center;
                padding-top: 50px;
            }

            button {
                width: 250px;
                height: 60px;
                margin: 15px;
                font-size: 20px;
                border-radius: 10px;
                border: none;
                cursor: pointer;
            }

            .immob {
                background: red;
                color: white;
            }

            .mob {
                background: green;
                color: white;
            }

            .crash {
                background: orange;
                color: black;
            }

            .fault {
                background: yellow;
                color: black;
            }

            .status {
                margin-top: 30px;
                font-size: 24px;
            }
        </style>
    </head>

    <body>

        <h1>Telematics ECU Dashboard</h1>

        <button class="immob" onclick="sendCommand('/api/immobilize')">
            IMMOBILIZE
        </button>
        <button class="mob" onclick="sendCommand('/api/mobilize')">
            MOBILIZE
        </button>
        <button class="crash" onclick="sendCommand('/api/crash')">
            CRASH
        </button>
        <button class="fault" onclick="sendCommand('/api/fault')">
            FAULT
        </button>

        <div class="status">
            <p>Vehicle Command: {{ vehicle_command }}</p>
            <p>Vehicle Fault: {{ vehicle_fault }}</p>
            <p>Crash Status: {{ crash_status }}</p>
        </div>

    </body>
    </html>
    ''', vehicle_command=vehicle_command, vehicle_fault=vehicle_fault, crash_status=crash_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)