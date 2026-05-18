from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

vehicle_command = "NONE"

# =========================
# DASHBOARD
# =========================

@app.route('/')
def dashboard():

    return render_template_string('''

    <html>

    <head>
        <title>Telematics Dashboard</title>
    </head>

    <body style="text-align:center;
                 font-family:Arial;
                 background:black;
                 color:white;">

        <h1>Telematics ECU Dashboard</h1>

        <br>

        <button onclick="fetch('/api/immobilize')"
        style="width:250px;height:60px;font-size:20px;background:red;color:white;">
        IMMOBILIZE
        </button>

        <br><br>

        <button onclick="fetch('/api/mobilize')"
        style="width:250px;height:60px;font-size:20px;background:green;color:white;">
        MOBILIZE
        </button>

    </body>

    </html>

    ''')

# =========================
# IMMOBILIZE
# =========================

@app.route('/api/immobilize')
def immobilize():

    global vehicle_command

    vehicle_command = "IMMOBILIZE"

    return jsonify({
        "command": vehicle_command
    })

# =========================
# MOBILIZE
# =========================

@app.route('/api/mobilize')
def mobilize():

    global vehicle_command

    vehicle_command = "MOBILIZE"

    return jsonify({
        "command": vehicle_command
    })

# =========================
# COMMAND API
# =========================

@app.route('/api/command')
def command():

    global vehicle_command

    return jsonify({
        "command": vehicle_command
    })

# =========================
# MAIN
# =========================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)