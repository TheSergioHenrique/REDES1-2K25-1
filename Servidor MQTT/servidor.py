import paho.mqtt.client as mqtt   # Biblioteca oficial de cliente MQTT em Python
import base64                    # Para codificação/decodificação de dados em base64
import time                      # Para controlar tempo de execução e pausas

# ======================
# CONFIGURAÇÃO DO BROKER
# ======================

BROKER = "localhost"  # Endereço IP do broker (localhost ou IP em rede como Radmin)
PORT = 1883           # Porta padrão MQTT (sem TLS)

# Tópicos utilizados para comunicação
TOPIC_UPLOAD = "arquivo/upload"     # Onde o cliente publica os arquivos
TOPIC_DOWNLOAD = "arquivo/download" # Onde o servidor publica os arquivos processados

# ===========================================
# CALLBACK QUANDO O CLIENTE CONECTA AO BROKER
# ===========================================

def on_connect(client, userdata, flags, rc):
    print(f"\n🔌 Cliente conectado ao broker! Código: {rc}")

    if rc == 0:  # Código 0 indica sucesso
        print(f"🔔 Subscrito ao tópico: {TOPIC_UPLOAD}")
        client.subscribe(TOPIC_UPLOAD)  # Se inscreve para receber arquivos do cliente
    else:
        print("❌ Conexão recusada.")  # Outros códigos indicam falhas

# ============================================
# CALLBACK QUANDO O CLIENTE DESCONECTA DO BROKER
# ============================================

def on_disconnect(client, userdata, rc):
    print(f"📴 Cliente desconectado do broker. Código: {rc}")

# ===========================================
# CALLBACK QUANDO UMA MENSAGEM É RECEBIDA
# ===========================================

def on_message(client, userdata, msg):
    print("\n📥 Mensagem recebida no tópico:", msg.topic)

    try:
        payload = msg.payload.decode()  # Decodifica o conteúdo da mensagem (string)
        print(f"📦 Payload recebido: {payload}")

        # O payload vem no formato "nome_do_arquivo;base64_conteudo"
        filename, file_data = payload.split(";", 1)
        print(f"🗂️ Arquivo: {filename}")

        # Decodifica o conteúdo, converte para maiúsculas (processamento), e prepara novo nome
        content = base64.b64decode(file_data).decode().upper()
        new_filename = f"CAPS_{filename}"  # Nome do novo arquivo (processado)

        # Salva o novo arquivo localmente
        with open(new_filename, "w") as f:
            f.write(content)

        # Codifica novamente para enviar via MQTT
        new_file_data = base64.b64encode(content.encode()).decode()

        # Publica o arquivo processado de volta para o cliente
        client.publish(TOPIC_DOWNLOAD, f"{new_filename};{new_file_data}")
        print(f"📤 Arquivo processado enviado: {new_filename}")

    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")

# ===================================
# FUNÇÃO PRINCIPAL: EXECUTA O SERVIDOR
# ===================================

def main():
    print("🚀 Iniciando servidor MQTT...")

    # Criação do cliente MQTT
    client = mqtt.Client()

    # Define as funções de callback
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    print("🔌 Tentando conectar ao broker...")
    client.connect(BROKER, PORT, 60)  # Conecta ao broker MQTT

    client.loop_start()  # Inicia loop de escuta em paralelo (assíncrono)

    print("🕒 Aguardando mensagens... Pressione Ctrl+C para sair.")
    try:
        while True:
            time.sleep(1)  # Mantém o programa rodando
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")
        client.loop_stop()  # Encerra o loop do cliente MQTT

# ===========================
# EXECUTA O SERVIDOR AO RODAR
# ===========================

if __name__ == "__main__":
    main()
