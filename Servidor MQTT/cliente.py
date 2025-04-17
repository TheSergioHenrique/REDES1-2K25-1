import paho.mqtt.client as mqtt     # Biblioteca oficial para cliente MQTT em Python
import base64                       # Para codificar arquivos em texto (base64)
import time                         # Para medir tempos de upload/download
import os                           # Para operações com arquivos locais
import sys                          # Para pegar argumentos de linha de comando (como client_id)

# ======================
# CONFIGURAÇÃO DO BROKER
# ======================

BROKER = "localhost"  # IP do broker MQTT (pode ser o localhost ou IP em rede)
PORT = 1883           # Porta padrão do protocolo MQTT sem TLS

# Tópicos MQTT utilizados:
TOPIC_UPLOAD = "arquivo/upload"     # Cliente publica arquivos aqui
TOPIC_DOWNLOAD = "arquivo/download" # Cliente recebe os arquivos processados aqui

# ================================
# VARIÁVEIS GLOBAIS DE CONTROLE
# ================================

pending_filename = None  # Guarda o nome do arquivo enviado, esperando a resposta
upload_time = None       # Marca o tempo de envio para cálculo posterior

# =====================================
# CALLBACK: QUANDO UMA MENSAGEM É RECEBIDA
# =====================================

def on_message(client, userdata, msg):
    global upload_time, pending_filename

    download_time = time.time()  # Marca o tempo de chegada da resposta
    payload = msg.payload.decode()
    print(f"\n📩 Mensagem recebida do servidor: {payload}")

    try:
        # O payload é no formato "nome_do_arquivo;base64_conteudo"
        filename, file_data = payload.split(";", 1)

        # Decodifica o conteúdo e salva em um novo arquivo
        with open(filename, "w") as f:
            f.write(base64.b64decode(file_data).decode())

        print(f"✅ Arquivo processado recebido: {filename}")
        print(f"💾 Salvo como: {filename}")

        # Se o nome bate com o que foi enviado, calcula estatísticas
        if upload_time and pending_filename == filename.replace("CAPS_", ""):
            size = os.path.getsize(filename)
            upload_duration = download_time - upload_time
            download_duration = time.time() - download_time
            print(f"📊 Transferência:")
            print(f"  📎 Tamanho: {size} bytes")
            print(f"  ⏱️ Upload: {upload_duration:.2f} s")
            print(f"  ⏱️ Download: {download_duration:.2f} s")

    except Exception as e:
        print(f"❌ Erro ao processar a resposta: {e}")

    # Reseta variáveis após processamento
    upload_time = None
    pending_filename = None

# ================================
# FUNÇÃO PARA ESCOLHER ARQUIVO .TXT
# ================================

def select_file():
    path = input("\n📂 Caminho do arquivo .txt (ou 'sair'): ").strip()
    if path.lower() == "sair":
        return None, None
    if not os.path.isfile(path):
        print("❌ Arquivo não encontrado.")
        return select_file()
    filename = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return filename, content

# ====================================
# CRIAÇÃO DO CLIENTE MQTT
# ====================================

# Nome do cliente pode ser passado via terminal, senão usa default
client_id = sys.argv[1] if len(sys.argv) > 1 else "cliente_default"
client = mqtt.Client(client_id=client_id)
client.on_message = on_message  # Define a função de callback para mensagens

# ====================================
# CONEXÃO AO BROKER MQTT
# ====================================

print("🔌 Conectando ao broker...")
client.connect(BROKER, PORT, 60)          # Estabelece conexão com o broker
client.subscribe(TOPIC_DOWNLOAD)         # Inscreve-se para receber arquivos de volta
client.loop_start()                      # Inicia o loop de recebimento de mensagens (assíncrono)
print(f"✅ Cliente '{client_id}' conectado ao broker.\n")

# ====================================
# LOOP PRINCIPAL: ENVIO DE ARQUIVOS
# ====================================

try:
    while True:
        filename, content = select_file()
        if not filename or not content:
            print("👋 Encerrando cliente.")
            break

        # Codifica o conteúdo para garantir que seja transmitido como texto via MQTT
        encoded_data = base64.b64encode(content.encode()).decode()

        # Guarda nome e tempo de envio para referência
        pending_filename = filename
        upload_time = time.time()

        # Publica no tópico de upload no formato "nome_arquivo;base64_conteudo"
        client.publish(TOPIC_UPLOAD, f"{filename};{encoded_data}")
        print(f"📤 Arquivo '{filename}' enviado. Aguardando resposta...\n")

        # Aguarda resposta por até 20 segundos
        wait = 0
        while upload_time is not None and wait < 20:
            time.sleep(1)
            wait += 1
        if upload_time is not None:
            print("⚠️ Tempo de resposta excedido.\n")
            upload_time = None
            pending_filename = None

except KeyboardInterrupt:
    print("\n🛑 Cliente interrompido pelo usuário.")

# ====================================
# FINALIZAÇÃO DO CLIENTE
# ====================================
client.loop_stop()  # Encerra o loop de escuta do MQTT
