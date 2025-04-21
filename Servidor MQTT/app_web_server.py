import base64
import time
import threading
import uuid  # Para gerar client_id único

from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

# ========== CONFIGURAÇÃO ==========
BROKER = "26.93.244.10"
PORT = 1883

client_id = f"web_{uuid.uuid4().hex[:6]}"  # Gera um ID único para este cliente
TOPIC_UPLOAD = f"arquivo/upload/{client_id}"     # Upload com ID único
TOPIC_DOWNLOAD = f"arquivo/download/{client_id}" # Somente este cliente receberá aqui

# ========== FLASK APP ==========
app = Flask(__name__)
mqtt_client = mqtt.Client(client_id=client_id)
response_data = {}

# ========== CALLBACKS ==========
def on_connect(client, userdata, flags, rc):
    print(f"🟢 Conectado ao broker MQTT como {client_id} com código: {rc}")
    client.subscribe(TOPIC_DOWNLOAD)
    print(f"🔔 Subscrito ao tópico: {TOPIC_DOWNLOAD}")

def on_message(client, userdata, msg):
    print(f"📩 Mensagem recebida no tópico {msg.topic}")
    try:
        filename, b64 = msg.payload.decode().split(";", 1)
        content = base64.b64decode(b64).decode()
        response_data["filename"] = filename
        response_data["content"] = content
        response_data["received"] = True
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()

# ========== ROTAS ==========
@app.route('/')
def index():
    return render_template("index.html", client_id=client_id)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    content = file.read().decode()
    encoded = base64.b64encode(content.encode()).decode()
    payload = f"{file.filename};{encoded};{client_id}"  # Inclui ID

    response_data.clear()
    response_data["received"] = False

    print(f"📤 Enviando arquivo: {file.filename} para tópico: {TOPIC_UPLOAD}")
    start_time = time.time()
    mqtt_client.publish(TOPIC_UPLOAD, payload)

    # Espera a resposta até 10 segundos
    timeout = 10
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

# ========== EXECUTA ==========
if __name__ == '__main__':
    app.run(debug=True)
