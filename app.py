from flask import Flask, request, jsonify

app = Flask(__name__)

latest_data = {}

vehicle_command = "NONE"

# HOME PAGE
@app.route('/')
def home():
    return "Telematics Server Running"

# RECEIVE TELEMETRY FROM ESP32
@app.route('/api/telemetry', methods=['POST'])
def telemetry():

    global latest_data

    latest_data = request.json

    print("Received Data:")
    print(latest_data)

    return jsonify({
        "status": "received"
    })

# GET LATEST TELEMETRY
@app.route('/api/latest')
def latest():

    return jsonify(latest_data)

# ESP32 READS COMMAND FROM HERE
@app.route('/api/command')
def command():

    global vehicle_command

    return jsonify({
        "command": vehicle_command
    })

# IMMOBILIZE COMMAND
@app.route('/api/immobilize')
def immobilize():

    global vehicle_command

    vehicle_command = "IMMOBILIZE"

    return "IMMOBILIZE COMMAND SENT"

# MOBILIZE COMMAND
@app.route('/api/mobilize')
def mobilize():

    global vehicle_command

    vehicle_command = "MOBILIZE"

    return "MOBILIZE COMMAND SENT"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)