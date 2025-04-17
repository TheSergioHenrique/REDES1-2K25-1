import base64
import time
import threading

from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

# MQTT config
BROKER = "localhost"
PORT = 1883
TOPIC_UPLOAD = "arquivo/upload"
TOPIC_DOWNLOAD = "arquivo/download"

# Flask app
app = Flask(__name__)
mqtt_client = mqtt.Client()
response_data = {}

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print("🟢 Conectado ao broker MQTT com código:", rc)
    client.subscribe(TOPIC_DOWNLOAD)

def on_message(client, userdata, msg):
    print(f"📩 Mensagem recebida no tópico {msg.topic}")
    filename, b64 = msg.payload.decode().split(";", 1)
    content = base64.b64decode(b64).decode()
    response_data["filename"] = filename
    response_data["content"] = content
    response_data["received"] = True

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    content = file.read().decode()
    encoded = base64.b64encode(content.encode()).decode()
    payload = f"{file.filename};{encoded}"
    
    # Zera a flag de controle de resposta
    response_data.clear()
    response_data["received"] = False

    print(f"📤 Enviando arquivo: {file.filename}")
    start_time = time.time()
    mqtt_client.publish(TOPIC_UPLOAD, payload)

    # Aguarda resposta por até 5 segundos
    timeout = 5
    while not response_data["received"] and time.time() - start_time < timeout:
        time.sleep(0.1)

    if response_data["received"]:
        duration = round(time.time() - start_time, 2)
        print(f"✅ Resposta recebida em {duration} segundos")
        return jsonify({
            "filename": response_data["filename"],
            "content": response_data["content"],
            "duration": duration
        })
    else:
        return jsonify({"error": "Timeout esperando resposta do servidor MQTT"}), 504

if __name__ == '__main__':
    app.run(debug=True)
