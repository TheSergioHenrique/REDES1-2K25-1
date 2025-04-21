# Importa a classe base para criar um manipulador de requisições HTTP e o servidor em si
from http.server import BaseHTTPRequestHandler, HTTPServer

# Importa a biblioteca para trabalhar com caminhos de arquivos (como construir caminhos, verificar existência, etc.)
import os

# Importa a biblioteca para medir o tempo (usado para calcular o tempo de leitura das imagens)
import time

# ===============================
# CONFIGURAÇÃO BÁSICA DO SERVIDOR
# ===============================

# Endereço IP onde o servidor vai escutar. "0.0.0.0" significa que vai aceitar conexões de qualquer IP (rede local, por exemplo).
host = "0.0.0.0"

# Porta em que o servidor vai ficar escutando requisições HTTP
port = 8000

# Descobre o caminho completo (absoluto) da pasta onde está este script Python
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define os caminhos completos para as pastas de HTML/CSS e imagens
base_folder = os.path.join(script_dir, "site")      # Pasta onde está o index.html e style.css
image_folder = os.path.join(script_dir, "imagens")  # Pasta onde estão armazenadas as imagens

# ======================================================
# CLASSE RESPONSÁVEL POR LIDAR COM CADA REQUISIÇÃO HTTP
# ======================================================

class MeuServidor(BaseHTTPRequestHandler):

    # Método executado automaticamente quando o servidor recebe uma requisição HTTP do tipo GET
    def do_GET(self):

        # =====================================================
        # CASO O USUÁRIO PEÇA A PÁGINA PRINCIPAL (HOME / INDEX)
        # =====================================================
        if self.path == "/" or self.path == "/index.html":
            # Caminho completo para o arquivo index.html
            file_path = os.path.join(base_folder, "index.html")

            # Envia um cabeçalho de resposta HTTP 200 (OK) e define o tipo de conteúdo como HTML
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            try:
                # Lista todos os arquivos da pasta de imagens com extensão JPG, PNG ou JPEG
                imagens = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
            except FileNotFoundError:
                # Caso a pasta de imagens não exista, evita erro e define uma lista vazia
                imagens = []

            # Lê o conteúdo do arquivo HTML
            html = open(file_path, "r", encoding="utf-8").read()

            # Para cada imagem encontrada, cria um bloco HTML com a imagem clicável
            imagens_html = "".join(
                f'<div class="img-box"><a href="/{img}" target="_blank"><img src="/{img}" alt="{img}"></a></div>'
                for img in imagens
            )

            # Substitui o marcador {{IMAGENS}} no HTML pelos blocos gerados dinamicamente
            self.wfile.write(html.replace("{{IMAGENS}}", imagens_html).encode())
            return

        # =============================================
        # CASO O USUÁRIO PEÇA UM ARQUIVO CSS (estilo)
        # =============================================
        elif self.path.endswith(".css"):
            # Constrói o caminho completo do CSS solicitado
            file_path = os.path.join(base_folder, self.path.lstrip("/"))

            # Verifica se o arquivo CSS realmente existe
            if os.path.exists(file_path):
                # Envia resposta HTTP com cabeçalho tipo CSS
                self.send_response(200)
                self.send_header("Content-type", "text/css")
                self.end_headers()

                # Abre o arquivo CSS e envia o conteúdo como resposta
                with open(file_path, "rb") as file:
                    self.wfile.write(file.read())
            else:
                # Caso o CSS solicitado não exista, envia erro 404
                self.send_error(404, "Arquivo CSS não encontrado.")
            return

        # ===============================================
        # CASO O USUÁRIO PEÇA UMA IMAGEM ESPECÍFICA
        # ===============================================

        # Remove a barra inicial do caminho (ex: "/img1.jpg" vira "img1.jpg")
        image_name = self.path.lstrip("/")

        # Constrói o caminho completo da imagem solicitada
        image_path = os.path.join(image_folder, image_name)

        # Verifica se o arquivo da imagem existe e é um arquivo comum
        if os.path.exists(image_path) and os.path.isfile(image_path):
            # Marca o tempo de início da leitura do arquivo
            start_time = time.time()

            # Calcula o tamanho do arquivo em kilobytes
            file_size = os.path.getsize(image_path) / 1024

            # Lê todo o conteúdo binário da imagem
            with open(image_path, "rb") as file:
                data = file.read()

            # Calcula o tempo gasto na leitura
            duration = time.time() - start_time

            # Calcula a velocidade de leitura (KB/s)
            speed = file_size / duration if duration > 0 else 0

            # Envia cabeçalhos HTTP informando que o conteúdo é uma imagem
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            # Envia os dados da imagem para o navegador
            self.wfile.write(data)

            # Exibe no terminal do servidor informações úteis (debug/log)
            print(f"📤 Servido '{image_name}' em {duration:.3f}s — Velocidade: {speed:.2f} KB/s")

        # ====================================================
        # CASO O USUÁRIO PEÇA UM ARQUIVO QUE NÃO FOI ENCONTRADO
        # ====================================================
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 - Imagem nao encontrada</h1>")

# ===================================================
# INICIALIZAÇÃO DO SERVIDOR: COMEÇA A ESCUTAR CONEXÕES
# ===================================================

# Cria uma instância do servidor HTTP, indicando o IP, porta e a classe que lida com as requisições
server = HTTPServer((host, port), MeuServidor)

# Mensagem no terminal dizendo que o servidor está no ar
print(f"Servidor rodando em {host}:{port}")

# Inicia o servidor em modo contínuo, aguardando conexões para sempre
server.serve_forever()
