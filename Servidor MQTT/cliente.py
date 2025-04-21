import paho.mqtt.client as mqtt
import base64
import time
import os
import sys

# ==================================================================
# CONFIGURAÇÃO DO CLIENTE MQTT
# ==================================================================
# Define o endereço e porta do broker MQTT
BROKER = "26.93.244.10"
PORT = 1883

# Gera o client_id a partir do argumento de linha de comando ou usa um default
# Isso permite múltiplos clientes independentes no mesmo broker.
client_id = sys.argv[1] if len(sys.argv) > 1 else "cliente_default"

# Tópicos exclusivos para upload e download, incorporando client_id
TOPIC_UPLOAD = f"arquivo/upload/{client_id}"
TOPIC_DOWNLOAD = f"arquivo/download/{client_id}"

# ==================================================================
# VARIÁVEIS GLOBAIS PARA CONTROLE DE ESTADO
# ==================================================================
# Armazena nome do arquivo pendente de resposta e horário de envio
pending_filename = None
upload_time = None

# ==================================================================
# CALLBACK DE RECEPÇÃO (DOWNLOAD)
# ==================================================================
def on_message(client, userdata, msg):
    """
    Chamado quando chega uma mensagem no tópico de download.
    Decodifica payload base64, salva em arquivo e calcula estatísticas.

    :param client: instância do cliente MQTT
    :param userdata: dados do usuário (não utilizado)
    :param msg: objeto com .topic e .payload (bytes)
    """
    global upload_time, pending_filename

    download_time = time.time()  # marca hora de recebimento
    payload = msg.payload.decode()

    try:
        # Payload no formato: "<filename>;<base64_data>"
        filename, file_data = payload.split(";", 1)
        # Decodifica conteúdo e escreve em arquivo local
        decoded_bytes = base64.b64decode(file_data)
        with open(filename, "wb") as f:
            f.write(decoded_bytes)

        print(f"✅ Arquivo recebido: {filename}")

        # Se este download corresponde a um upload pendente, calcula estatísticas
        original_name = filename.replace("CAPS_", "")
        if upload_time and pending_filename == original_name:
            size = os.path.getsize(filename)
            response_time = download_time - upload_time
            print("\n📊 Estatísticas:")
            print(f"📎 Tamanho: {size} bytes")
            print(f"⏱️ Tempo de resposta: {response_time:.2f} segundos")

    except Exception as e:
        print(f"❌ Erro ao processar resposta: {e}")

    # Reseta estado após processamento
    upload_time = None
    pending_filename = None

# ==================================================================
# FUNÇÃO DE SELEÇÃO DE ARQUIVO
# ==================================================================
def select_file():
    """
    Solicita ao usuário o caminho para um arquivo .txt.
    Retorna (filename, content) ou (None, None) em caso de 'sair'.
    """
    path = input("\n📂 Caminho do arquivo (.txt) ou 'sair': ").strip()
    if path.lower() == "sair":
        return None, None

    if not os.path.isfile(path):
        print("❌ Arquivo não encontrado.")
        return select_file()  # tenta novamente

    filename = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return filename, content

# ==================================================================
# CONFIGURA E INICIA O CLIENTE MQTT
# ==================================================================
# Cria o cliente com ID único e associa callback de mensagem
client = mqtt.Client(client_id=client_id)
client.on_message = on_message

print("🔌 Conectando ao broker...")
client.connect(BROKER, PORT, keepalive=60)
# Subscrição ao tópico de download exclusivo deste cliente
client.subscribe(TOPIC_DOWNLOAD)
client.loop_start()  # inicia loop em thread separada
print(f"✅ Cliente '{client_id}' conectado e subscrito em '{TOPIC_DOWNLOAD}'.\n")

# ==================================================================
# LOOP PRINCIPAL DE UPLOAD
# ==================================================================
try:
    while True:
        # Seleciona arquivo ou sai
        filename, content = select_file()
        if not filename:
            print("👋 Encerrando cliente.")
            break

        # Codifica conteúdo em base64 para envio
        encoded_data = base64.b64encode(content.encode()).decode()
        pending_filename = filename  # guarda nome para estatísticas
        upload_time = time.time()    # guarda hora de envio

        # Publica payload no tópico de upload
        payload = f"{filename};{encoded_data}"
        client.publish(TOPIC_UPLOAD, payload)
        print(f"📤 Arquivo '{filename}' enviado. Aguardando resposta...\n")

        # Espera por resposta por até 20 segundos
        wait = 0
        while upload_time and wait < 20:
            time.sleep(1)
            wait += 1

        # Timeout
        if upload_time:
            print("⚠️ Tempo limite excedido (20s).\n")
            upload_time = None
            pending_filename = None

except KeyboardInterrupt:
    # Captura Ctrl+C para desligar graciosamente
    print("\n🛑 Cliente interrompido pelo usuário.")

# Para o loop do MQTT antes de encerrar
client.loop_stop()
