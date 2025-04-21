import base64
import time
import threading
import uuid  # Para gerar client_id único

from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

# ==================================================================
# Configuração geral do sistema
# ==================================================================
BROKER = "26.93.244.10"       # Endereço IP do broker MQTT
PORT = 1883                    # Porta padrão do broker MQTT

# Gera um identificador único para cada instância do cliente web,
# facilitando a comunicação privada entre servidor e cliente.
client_id = f"web_{uuid.uuid4().hex[:6]}"

# Define tópicos MQTT personalizados para upload e download,
# incorporando o client_id para garantir unicidade.
TOPIC_UPLOAD = f"arquivo/upload/{client_id}"
TOPIC_DOWNLOAD = f"arquivo/download/{client_id}"

# ==================================================================
# Inicialização da aplicação Flask e do cliente MQTT
# ==================================================================
app = Flask(__name__)
# Cria instância do cliente MQTT com ID único
mqtt_client = mqtt.Client(client_id=client_id)

# Dicionário global para armazenar resposta recebida pelo MQTT
# Este objeto será atualizado pelo callback on_message.
response_data = {}

# ==================================================================
# Callbacks do MQTT
# ==================================================================
def on_connect(client, userdata, flags, rc):
    """
    Chamado quando o cliente se conecta ao broker.
    Subscrição no tópico de download ocorre aqui.

    :param client: instância do cliente MQTT
    :param userdata: dados definidos pelo usuário (não utilizado)
    :param flags: indicadores de conexão
    :param rc: código de retorno da conexão (0 = sucesso)
    """
    print(f"🟢 Conectado ao broker MQTT como {client_id} com código: {rc}")
    # Subscrição no tópico onde o servidor irá publicar a resposta
    client.subscribe(TOPIC_DOWNLOAD)
    print(f"🔔 Subscrito ao tópico: {TOPIC_DOWNLOAD}")


def on_message(client, userdata, msg):
    """
    Chamado quando uma mensagem é recebida em qualquer tópico subscrito.
    Processa o payload que contém "<filename>;<base64_content>".

    :param msg.topic: tópico que recebeu a mensagem
    :param msg.payload: conteúdo da mensagem em bytes
    """
    print(f"📩 Mensagem recebida no tópico {msg.topic}")
    try:
        # Separa nome do arquivo e conteúdo codificado em base64
        filename, b64 = msg.payload.decode().split(";", 1)
        # Decodifica o conteúdo de volta para texto
        content = base64.b64decode(b64).decode()
        # Atualiza o dicionário global para sinalizar recebimento
        response_data["filename"] = filename
        response_data["content"] = content
        response_data["received"] = True
    except Exception as e:
        # Em caso de erro, imprime no terminal para depuração
        print(f"❌ Erro ao processar mensagem: {e}")

# Atribui as funções de callback ao cliente MQTT
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
# Conecta ao broker e inicia o loop em background
mqtt_client.connect(BROKER, PORT)
mqtt_client.loop_start()

# ==================================================================
# Rotas da aplicação Flask
# ==================================================================
@app.route('/')
def index():
    """
    Rota principal que renderiza a página HTML.
    Passa o client_id para o JavaScript poder referenciar os tópicos.
    """
    return render_template("index.html", client_id=client_id)

@app.route('/upload', methods=['POST'])
def upload():
    """
    Rota que recebe o arquivo do usuário via POST.
    Codifica o conteúdo em base64 e publica no tópico de upload.
    Aguarda a resposta do servidor via MQTT e retorna JSON.
    """
    # Lê o arquivo enviado pelo formulário
    file = request.files['file']
    content = file.read().decode()  # Lê e decodifica para string
    # Codifica o conteúdo em base64 para transmissão segura
    encoded = base64.b64encode(content.encode()).decode()
    # Payload: "nome_do_arquivo;base64_conteudo;client_id"
    payload = f"{file.filename};{encoded};{client_id}"

    # Reinicializa o estado de resposta
    response_data.clear()
    response_data["received"] = False

    print(f"📤 Enviando arquivo: {file.filename} para tópico: {TOPIC_UPLOAD}")
    start_time = time.time()
    # Publica a mensagem MQTT
    mqtt_client.publish(TOPIC_UPLOAD, payload)

    # Espera a resposta até timeout (10 segundos)
    timeout = 10
    while not response_data.get("received") and time.time() - start_time < timeout:
        time.sleep(0.1)

    # Se recebeu resposta, calcula duração e retorna JSON
    if response_data.get("received"):
        duration = round(time.time() - start_time, 2)
        print(f"✅ Resposta recebida em {duration} segundos")
        return jsonify({
            "filename": response_data["filename"],
            "content": response_data["content"],
            "duration": duration
        })
    else:
        # Em caso de timeout, retorna erro 504 (Gateway Timeout)
        return jsonify({"error": "Timeout esperando resposta do servidor MQTT"}), 504

# ==================================================================
# Execução da aplicação
# ==================================================================
if __name__ == '__main__':
    # Inicia o servidor Flask em modo de depuração (debug)
    app.run(debug=True)
