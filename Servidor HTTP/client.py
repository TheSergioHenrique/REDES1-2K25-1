import requests  # Biblioteca para realizar requisições HTTP de forma simples
import time      # Biblioteca para medir o tempo de execução (desempenho da requisição)

# ==========================
# CONFIGURAÇÕES INICIAIS
# ==========================

# Endereço IP do servidor que irá fornecer as imagens via protocolo HTTP
# Pode ser um IP local ou o IP virtual atribuído via VPN (ex: Radmin VPN)
server_ip = "26.93.244.10"

# Montagem da URL base do servidor, utilizando a porta 8000 (padrão em muitos testes com servidores locais Python)
server_url = f"http://{server_ip}:8000"

# Lista simulada de imagens disponíveis no servidor (nomes dos arquivos JPEG)
imagens_disponiveis = [f"img{i}.jpg" for i in range(1, 11)]

# Exibição no terminal das imagens disponíveis para download
print("\nImagens disponíveis no servidor:")
for img in imagens_disponiveis:
    print(f"- {img}")

# ==========================
# INTERAÇÃO COM O USUÁRIO
# ==========================

# Solicitação de entrada do usuário para escolher uma imagem para baixar
imagem_solicitada = input("\nDigite o nome da imagem que deseja baixar: ")

# ==========================
# ENVIO DA REQUISIÇÃO HTTP
# ==========================

# Captura do tempo de início para medir o tempo total da operação de download
start_time = time.time()

# Envio de uma requisição HTTP GET para o servidor solicitando a imagem desejada
# A URL completa tem o formato: http://<ip>:8000/<nome_da_imagem>
resposta = requests.get(f"{server_url}/{imagem_solicitada}")

# Cálculo da duração da requisição em segundos
duration = time.time() - start_time

# ==========================
# ANÁLISE DA RESPOSTA HTTP
# ==========================

# Se a resposta for bem-sucedida (HTTP 200 OK)
if resposta.status_code == 200:
    # Cálculo do tamanho da imagem em kilobytes (KB)
    tamanho_kb = len(resposta.content) / 1024

    # Cálculo da velocidade de download em KB/s
    velocidade = tamanho_kb / duration if duration > 0 else 0

    # Salvamento do conteúdo da imagem recebida no disco (modo binário)
    with open(imagem_solicitada, "wb") as file:
        file.write(resposta.content)

    # Feedback para o usuário com detalhes da transferência
    print(f"\n✅ {resposta.status_code} OK - Imagem '{imagem_solicitada}' baixada com sucesso!")
    print(f"📅 Tempo: {duration:.3f}s — Tamanho: {tamanho_kb:.2f} KB — Velocidade: {velocidade:.2f} KB/s")

# Caso o recurso (imagem) não exista no servidor — erro 404 Not Found
elif resposta.status_code == 404:
    print(f"\n❌ {resposta.status_code} Not Found - Imagem não encontrada no servidor.")

# Caso ocorra um erro interno no servidor — erros da faixa 5xx
elif resposta.status_code >= 500:
    print(f"\n🚨 {resposta.status_code} Server Error - Problema no servidor.")

# Outros erros de cliente — erros da faixa 4xx
elif resposta.status_code >= 400:
    print(f"\n⚠️ {resposta.status_code} Client Error - Requisição inválida.")

# Caso retorne algum outro código HTTP não previsto explicitamente
else:
    print(f"\nℹ️ {resposta.status_code} Código HTTP inesperado.")
