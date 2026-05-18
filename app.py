from flask import Flask, request, jsonify

app = Flask(__name__)

latest_data = {}

@app.route('/')
def home():
    return "Telematics Server Running"

@app.route('/api/telemetry', methods=['POST'])
def telemetry():

    global latest_data

    latest_data = request.json

    print("Received Data:")
    print(latest_data)

    return jsonify({
        "status": "received"
    })

@app.route('/api/latest')
def latest():

    return jsonify(latest_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)