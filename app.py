from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

vehicle_command = "NONE"

# =========================
# 1. DASHBOARD (Web UI)
# =========================
@app.route('/')
def dashboard():
    return render_template_string('''
    <html>
    <head>
        <title>Telematics Dashboard</title>
    </head>
    <body style="text-align:center; font-family:Arial; background:black; color:white;">
        <h1>Telematics ECU Dashboard</h1>
        <br>
        <button onclick="fetch('/api/immobilize')"
        style="width:250px;height:60px;font-size:20px;background:red;color:white;cursor:pointer;">
        IMMOBILIZE
        </button>
        <br><br>
        <button onclick="fetch('/api/mobilize')"
        style="width:250px;height:60px;font-size:20px;background:green;color:white;cursor:pointer;">
        MOBILIZE
        </button>
    </body>
    </html>
    ''')

# =========================
# 2. COMMAND ROUTES (Buttons to Server)
# =========================
@app.route('/api/immobilize')
def immobilize():
    global vehicle_command
    vehicle_command = "IMMOBILIZE"
    print("SERVER: Vehicle set to IMMOBILIZE")
    return jsonify({"command": vehicle_command})

@app.route('/api/mobilize')
def mobilize():
    global vehicle_command
    vehicle_command = "MOBILIZE"
    print("SERVER: Vehicle set to MOBILIZE")
    return jsonify({"command": vehicle_command})

# =========================
# 3. ECU PULL ROUTE (STM32 asks: "What should I do?")
# =========================
@app.route('/api/command')
def command():
    global vehicle_command
    return jsonify({"command": vehicle_command})

# =========================
# 4. ECU PUSH ROUTE (STM32 says: "I crashed!")
# =========================
@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    # Get the JSON payload sent by the STM32
    data = request.get_json()
    
    # Print it to your Render terminal so you can see it
    print(f"\n[URGENT] MESSAGE FROM VEHICLE: {data}\n")
    
    # Check if it's a crash
    if data and data.get("event") == "CRASH":
        print("!!! INITIATING eCALL PROCEDURES !!!")
        # You can add email/SMS alerts here later
        
    # Reply to the STM32 so it knows we got the message
    return jsonify({"status": "Message Received Successfully"}), 200

# =========================
# MAIN
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)