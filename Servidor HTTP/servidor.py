from http.server import BaseHTTPRequestHandler, HTTPServer  # Classes nativas para criar um servidor HTTP básico em Python
import os     # Para manipulação de caminhos de arquivos
import time   # Para medir o tempo de resposta (tempo de leitura dos arquivos)

# ===============================
# CONFIGURAÇÃO BÁSICA DO SERVIDOR
# ===============================

# O servidor irá escutar em todas as interfaces de rede disponíveis (0.0.0.0)
host = "0.0.0.0"

# Porta padrão usada para receber conexões HTTP
port = 8000

# Pasta onde estão armazenados os arquivos HTML e CSS
base_folder = "site"

# Pasta que contém as imagens que o servidor pode servir
image_folder = "imagens"

# =====================================
# CLASSE QUE DEFINE O COMPORTAMENTO HTTP
# =====================================

class MeuServidor(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Método que trata requisições HTTP do tipo GET.
        Esse método é automaticamente invocado sempre que um cliente faz um GET ao servidor.
        """

        # ====================================
        # CASO A REQUISIÇÃO SEJA PELA HOME PAGE
        # ====================================
        if self.path == "/" or self.path == "/index.html":
            file_path = os.path.join(base_folder, "index.html")  # Caminho do HTML principal

            # Envia cabeçalho HTTP de sucesso (status 200)
            self.send_response(200)
            self.send_header("Content-type", "text/html")  # Tipo de conteúdo: HTML
            self.end_headers()

            # Lista as imagens disponíveis na pasta
            imagens = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.png', '.jpeg'))]

            # Lê o conteúdo HTML do arquivo index
            html = open(file_path, "r", encoding="utf-8").read()

            # Gera dinamicamente blocos HTML com cada imagem disponível
            imagens_html = "".join(
                f'<div class="img-box"><a href="/{img}" target="_blank"><img src="/{img}" alt="{img}"></a></div>'
                for img in imagens
            )

            # Substitui o placeholder {{IMAGENS}} no HTML pelas imagens encontradas
            self.wfile.write(html.replace("{{IMAGENS}}", imagens_html).encode())
            return
        
        # ====================================
        # CASO O CLIENTE SOLICITE UM ARQUIVO CSS
        # ====================================
        elif self.path.endswith(".css"):
            file_path = os.path.join(base_folder, self.path.lstrip("/"))  # Caminho completo do CSS

            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-type", "text/css")  # Tipo de conteúdo: CSS
                self.end_headers()

                with open(file_path, "rb") as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404, "Arquivo CSS não encontrado.")  # Se o CSS não existir
            return
        
        # ====================================
        # CASO O CLIENTE SOLICITE UMA IMAGEM
        # ====================================

        image_name = self.path.lstrip("/")  # Remove a "/" do início do path
        image_path = os.path.join(image_folder, image_name)  # Caminho do arquivo da imagem

        # Verifica se o arquivo existe
        if os.path.exists(image_path) and os.path.isfile(image_path):
            start_time = time.time()  # Início da medição de tempo

            file_size = os.path.getsize(image_path) / 1024  # Tamanho do arquivo em KB

            # Lê o conteúdo da imagem
            with open(image_path, "rb") as file:
                data = file.read()

            duration = time.time() - start_time  # Duração da leitura
            speed = file_size / duration if duration > 0 else 0  # Cálculo da velocidade

            # Envia cabeçalhos HTTP
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")  # Tipo de conteúdo: imagem
            self.end_headers()

            self.wfile.write(data)  # Envia o conteúdo da imagem para o cliente

            print(f"📤 Servido '{image_name}' em {duration:.3f}s — Velocidade: {speed:.2f} KB/s")
        
        # ====================================
        # CASO O ARQUIVO SOLICITADO NÃO EXISTA
        # ====================================
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>404 - Imagem nao encontrada</h1>")

# ====================================
# INICIALIZAÇÃO DO SERVIDOR HTTP
# ====================================
server = HTTPServer((host, port), MeuServidor)
print(f"Servidor rodando em {host}:{port}")
server.serve_forever()  # Mantém o servidor ativo indefinidamente
