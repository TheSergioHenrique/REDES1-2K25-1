import paho.mqtt.client as mqtt   # Cliente MQTT
import base64                    # Codificação base64 para arquivos
import time                      # Medição de tempo
import threading                 # Para executar servidor web em paralelo
from flask import Flask         # Framework web Flask

# ======================
# CONFIGURAÇÃO DO BROKER
# ======================

BROKER = "localhost"
PORT = 1883

TOPIC_UPLOAD = "arquivo/upload/#"  # Escuta todos os uploads com ID do cliente no tópico

# =============================================
# CALLBACK QUANDO CONECTA AO BROKER
# =============================================

def on_connect(client, userdata, flags, rc):
    print(f"\n🔌 Conectado ao broker! Código: {rc}")
    if rc == 0:
        print(f"🔔 Subscrito ao tópico: {TOPIC_UPLOAD}")
        client.subscribe(TOPIC_UPLOAD)  # Escuta todos os uploads com ID de cliente
    else:
        print("❌ Falha na conexão.")

# =============================================
# CALLBACK QUANDO RECEBE UMA MENSAGEM
# =============================================

def on_message(client, userdata, msg):
    print(f"\n📥 Mensagem recebida no tópico: {msg.topic}")

    try:
        payload = msg.payload.decode()
        print(f"📦 Payload recebido: {payload}")

        # Extrai client_id do tópico: ex. "arquivo/upload/cliente123"
        client_id = msg.topic.split("/")[-1]
        if not client_id:
            print("⚠️ ID de cliente não encontrado no tópico.")
            return

        # Payload: nome.txt;base64conteudo
        filename, file_data = payload.split(";", 1)
        content = base64.b64decode(file_data).decode().upper()

        # Novo nome para o arquivo processado
        new_filename = f"CAPS_{filename}"
        with open(new_filename, "w") as f:
            f.write(content)

        # Codifica conteúdo novamente
        new_file_data = base64.b64encode(content.encode()).decode()

        # Publica apenas para o cliente que enviou
        response_topic = f"arquivo/download/{client_id}"
        client.publish(response_topic, f"{new_filename};{new_file_data}")
        print(f"📤 Resposta enviada para {response_topic}")

    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")

# =============================================
# FUNÇÃO PARA INICIAR O SERVIDOR WEB FLASK
# =============================================

def iniciar_servidor_web():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Servidor MQTT está ativo!"

    app.run(port=5000, debug=False)

# =============================================
# EXECUÇÃO PRINCIPAL DO SERVIDOR
# =============================================

def main():
    print("🚀 Iniciando servidor MQTT...")
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    # Inicia o servidor web Flask em uma thread separada
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")
        client.loop_stop()

if __name__ == "__main__":
    main()
