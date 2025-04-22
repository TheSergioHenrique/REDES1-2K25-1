import paho.mqtt.client as mqtt   # Biblioteca para comunicação MQTT
import base64                    # Para codificação e decodificação dos dados dos arquivos
import time                      # Para medir o tempo de resposta
import os                        # Para manipulação de arquivos locais
import sys                       # Para ler argumentos da linha de comando

# ================
# CONFIGURAÇÃO
# ================

BROKER = "26.93.244.10"          # IP do broker MQTT (pode ser local ou remoto)
PORT = 1883                      # Porta padrão do protocolo MQTT

# Identificação única do cliente (pode ser passada como argumento ao executar o script)
client_id = sys.argv[1] if len(sys.argv) > 1 else "cliente_default"

# Tópicos de envio (upload) e recebimento (download) específicos para este cliente
TOPIC_UPLOAD = f"arquivo/upload/{client_id}"
TOPIC_DOWNLOAD = f"arquivo/download/{client_id}"

# ================
# VARIÁVEIS GLOBAIS
# ================

pending_filename = None          # Nome do arquivo que está aguardando resposta
upload_time = None               # Timestamp do envio, para cálculo do tempo de resposta

# ======================
# CALLBACK DE DOWNLOAD
# ======================

# Esta função é executada automaticamente quando uma mensagem chega no tópico de download
def on_message(client, userdata, msg):
    global upload_time, pending_filename

    download_time = time.time()                       # Marca o tempo da chegada da resposta
    payload = msg.payload.decode()                    # Decodifica a mensagem recebida

    try:
        # Espera-se que o payload esteja no formato: "nome_do_arquivo;base64_dos_dados"
        filename, file_data = payload.split(";", 1)

        # Cria o arquivo com o conteúdo decodificado
        with open(filename, "w") as f:
            f.write(base64.b64decode(file_data).decode())

        print(f"✅ Arquivo recebido: {filename}")

        # Exibe estatísticas se estivermos esperando resposta deste arquivo
        if upload_time and pending_filename == filename.replace("CAPS_", ""):
            size = os.path.getsize(filename)
            response_time = download_time - upload_time
            print(f"\n📊 Estatísticas:")
            print(f"📎 Tamanho: {size} bytes")
            print(f"⏱️ Tempo de resposta: {response_time:.2f} segundos")

    except Exception as e:
        print(f"❌ Erro ao processar resposta: {e}")

    # Limpa os dados para próxima requisição
    upload_time = None
    pending_filename = None

# ==============================
# SELEÇÃO DO ARQUIVO .TXT
# ==============================

# Solicita ao usuário que informe o caminho do arquivo .txt a ser enviado
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

# Cria o cliente MQTT com um ID único
client = mqtt.Client(client_id=client_id)

# Define a função que será chamada quando uma mensagem for recebida
client.on_message = on_message

# Conecta ao broker MQTT
print("🔌 Conectando ao broker...")
client.connect(BROKER, PORT, 60)

# Inscreve-se no tópico de download exclusivo deste cliente
client.subscribe(TOPIC_DOWNLOAD)

# Inicia o loop em segundo plano para lidar com eventos MQTT
client.loop_start()
print(f"✅ Cliente '{client_id}' conectado.\n")

# ==============================
# LOOP PRINCIPAL
# ==============================

# Loop principal da aplicação (permite enviar arquivos até o usuário desejar sair)
try:
    while True:
        filename, content = select_file()
        if not filename:
            print("👋 Encerrando cliente.")
            break

        # Codifica o conteúdo do arquivo em base64 para envio seguro via MQTT
        encoded_data = base64.b64encode(content.encode()).decode()

        # Armazena informações para estatísticas
        pending_filename = filename
        upload_time = time.time()

        # Publica a mensagem no tópico de upload do servidor
        client.publish(TOPIC_UPLOAD, f"{filename};{encoded_data}")
        print(f"📤 Arquivo '{filename}' enviado. Aguardando resposta...\n")

        # Aguarda a resposta do servidor por até 20 segundos
        wait = 0
        while upload_time and wait < 20:
            time.sleep(1)
            wait += 1

        # Caso não haja resposta dentro do tempo limite
        if upload_time:
            print("⚠️ Tempo limite excedido (20s).\n")
            upload_time = None
            pending_filename = None

# Permite que o programa seja interrompido com Ctrl+C
except KeyboardInterrupt:
    print("\n🛑 Cliente interrompido.")

# Finaliza o loop MQTT antes de encerrar
client.loop_stop()
