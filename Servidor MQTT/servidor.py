# servidor_mqtt.py
# Este script implementa o lado servidor de uma aplicação baseada em MQTT.
# O servidor recebe arquivos codificados em base64 de clientes,
# converte o conteúdo para letras maiúsculas e devolve o novo arquivo ao respectivo cliente.

import paho.mqtt.client as mqtt  # Biblioteca para comunicação MQTT
import base64                    # Utilizada para codificar e decodificar os dados dos arquivos
import time                      # (Não está sendo usada aqui, mas pode ser útil para medir tempos)

# Configurações de conexão
BROKER = "localhost"             # Endereço do broker MQTT (neste caso, local)
PORT = 1883                      # Porta padrão do protocolo MQTT
TOPIC_BASE = "arquivo/upload/#" # Tópico base que o servidor irá escutar (sinal "#" permite receber de múltiplos clientes)

# Função chamada quando o cliente (servidor) conecta ao broker com sucesso
def on_connect(client, userdata, flags, rc):
    print(f"🔌 Conectado ao broker. Código: {rc}")  # Código de retorno da conexão
    client.subscribe(TOPIC_BASE)                   # Inscreve-se no tópico base
    print(f"📡 Subscrito ao tópico base: {TOPIC_BASE}")

# Função chamada quando o cliente (servidor) se desconecta do broker
def on_disconnect(client, userdata, rc):
    print("📴 Desconectado do broker.")

# Função chamada sempre que uma mensagem chega no tópico inscrito
def on_message(client, userdata, msg):
    print(f"\n📥 Mensagem recebida no tópico: {msg.topic}")

    try:
        # Decodifica o payload da mensagem (espera-se que esteja no formato: "nome_do_arquivo;base64_dos_dados")
        payload = msg.payload.decode()
        filename, file_data = payload.split(";", 1)

        # Decodifica o conteúdo do arquivo, converte para letras maiúsculas
        content = base64.b64decode(file_data).decode().upper()

        # Cria um novo nome para o arquivo processado
        new_filename = f"CAPS_{filename}"

        # Salva o novo conteúdo em um arquivo local
        with open(new_filename, "w") as f:
            f.write(content)

        # Codifica novamente o conteúdo para envio via MQTT
        new_file_data = base64.b64encode(content.encode()).decode()

        # Extrai o ID do cliente a partir do tópico
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 3:
            client_id = topic_parts[2]
            # Define o tópico de resposta baseado no client_id
            download_topic = f"arquivo/download/{client_id}"
            # Publica o novo arquivo no tópico do cliente
            client.publish(download_topic, f"{new_filename};{new_file_data}")
            print(f"📤 Arquivo enviado ao cliente '{client_id}' via {download_topic}")
        else:
            print("⚠️ Tópico malformado. client_id não encontrado.")

    except Exception as e:
        # Captura erros na manipulação da mensagem
        print(f"❌ Erro: {e}")

# Função principal que configura e inicia o servidor MQTT
def main():
    print("🚀 Servidor MQTT iniciando...")

    # Cria um cliente MQTT
    client = mqtt.Client()

    # Define as funções de callback para os eventos MQTT
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Conecta-se ao broker
    client.connect(BROKER, PORT, 60)

    # Entra em loop infinito para manter a escuta de mensagens
    client.loop_forever()

# Execução do script como programa principal
if __name__ == "__main__":
    main()
