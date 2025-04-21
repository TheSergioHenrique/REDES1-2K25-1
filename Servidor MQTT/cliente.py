import paho.mqtt.client as mqtt
import base64
import time
import os
import sys

# ================
# CONFIGURAÇÃO
# ================

BROKER = "26.93.244.10"
PORT = 1883

client_id = sys.argv[1] if len(sys.argv) > 1 else "cliente_default"

TOPIC_UPLOAD = f"arquivo/upload/{client_id}"     # Upload exclusivo com ID
TOPIC_DOWNLOAD = f"arquivo/download/{client_id}" # Download exclusivo

# ================
# VARIÁVEIS GLOBAIS
# ================

pending_filename = None
upload_time = None

# ======================
# CALLBACK DE DOWNLOAD
# ======================

def on_message(client, userdata, msg):
    global upload_time, pending_filename

    download_time = time.time()
    payload = msg.payload.decode()

    try:
        filename, file_data = payload.split(";", 1)
        with open(filename, "w") as f:
            f.write(base64.b64decode(file_data).decode())

        print(f"✅ Arquivo recebido: {filename}")

        if upload_time and pending_filename == filename.replace("CAPS_", ""):
            size = os.path.getsize(filename)
            response_time = download_time - upload_time
            print(f"\n📊 Estatísticas:")
            print(f"📎 Tamanho: {size} bytes")
            print(f"⏱️ Tempo de resposta: {response_time:.2f} segundos")

    except Exception as e:
        print(f"❌ Erro ao processar resposta: {e}")

    upload_time = None
    pending_filename = None

# ==============================
# SELEÇÃO DO ARQUIVO .TXT
# ==============================

def select_file():
    path = input("\n📂 Caminho do arquivo (.txt) ou 'sair': ").strip()
    if path.lower() == "sair":
        return None, None
    if not os.path.isfile(path):
        print("❌ Arquivo não encontrado.")
        return select_file()
    filename = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return filename, content

# ================
# CONEXÃO AO BROKER
# ================

client = mqtt.Client(client_id=client_id)
client.on_message = on_message

print("🔌 Conectando ao broker...")
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC_DOWNLOAD)  # Apenas para este cliente
client.loop_start()
print(f"✅ Cliente '{client_id}' conectado.\n")

# ==============================
# LOOP PRINCIPAL
# ==============================

try:
    while True:
        filename, content = select_file()
        if not filename:
            print("👋 Encerrando cliente.")
            break

        encoded_data = base64.b64encode(content.encode()).decode()
        pending_filename = filename
        upload_time = time.time()

        # Envia o arquivo para o servidor
        client.publish(TOPIC_UPLOAD, f"{filename};{encoded_data}")
        print(f"📤 Arquivo '{filename}' enviado. Aguardando resposta...\n")

        wait = 0
        while upload_time and wait < 20:
            time.sleep(1)
            wait += 1

        if upload_time:
            print("⚠️ Tempo limite excedido (20s).\n")
            upload_time = None
            pending_filename = None

except KeyboardInterrupt:
    print("\n🛑 Cliente interrompido.")

client.loop_stop()
