# Projeto de Redes 1 – Servidor HTTP e MQTT com Mosquitto

Este projeto demonstra dois modos de comunicação em redes:  
- Um **servidor HTTP** que serve imagens para um cliente.
- Um **sistema baseado em MQTT**, com um servidor que processa mensagens de múltiplos clientes através do **Mosquitto Broker**.

---

## 📁 Estrutura do Projeto

```
Servidor HTTP/
├── imagens/         # imagens (img1.jpg até img10.jpg)
├── site/
│   ├── index.html
│   └── style.css
├── servidor.py      # Código do servidor HTTP ou MQTT
└── client.py        # Código do cliente HTTP ou MQTT
```

---

## 🌐 Modo 1: Servidor HTTP de Imagens

### ✅ Requisitos
- Python 3 instalado → verifique com:
  ```
  python --version
  ```
-biblioteca requests-pode ser instalado com um pip install

### 🚀 Como Executar

#### 1. Iniciar o Servidor HTTP
No terminal, dentro da pasta do `servidor.py`:
```
python servidor.py
```

O servidor:
- Roda na porta **8000**
- Gera uma **interface web com miniaturas das imagens**
- Serve as imagens via protocolo **HTTP**

#### 2. Acessar a Galeria (opcional)
Abra o navegador em:
```
http://localhost:8000
```

Você verá a galeria de imagens da pasta `imagens/`.

#### 3. Executar o Cliente
Em outro terminal:
```
python client.py
```

O cliente:
- Lista as imagens disponíveis
- Solicita o nome da imagem (ex: `img3.jpg`)
- Baixa a imagem e exibe:
  - Tempo de download
  - Tamanho do arquivo
  - Velocidade de transferência

#### 4. Uso em Rede (ex: com Radmin VPN)
No `client.py`, altere a linha:
```python
server_ip = "SEU_IP_AQUI"
```

Coloque o IP da máquina onde o servidor está rodando.

---

### ⚠ Erros Comuns

| Código | Significado                              |
|--------|------------------------------------------|
| ❌ 404 | Imagem não encontrada                    |
| ⚠ 400 | Nome inválido ou erro de digitação        |
| 🚨 500 | Erro interno no servidor                 |

---

## 📡 Modo 2: Comunicação via MQTT com Mosquitto

### ✅ Instalar o Mosquitto Broker
Baixe e instale:
👉 [mosquitto.org/download](https://mosquitto.org/download)

### ⚙ Configurar o `mosquitto.conf`

Adicione ao final do arquivo:

```
listener 1883 0.0.0.0
listener 9001
protocol websockets
allow_anonymous true
```

Explicação:
- `listener 1883`: escuta conexões na porta padrão do MQTT
- `allow_anonymous true`: permite conexões sem autenticação (útil para testes locais)

---

### 🧰 Instalar as Dependências Python

No terminal:
```
pip install flask paho-mqtt
```

---

### 🚀 Como Executar

#### 1. Iniciar o Broker Mosquitto

No diretório do `mosquitto.exe`:
```
mosquitto.exe -c mosquitto.conf
```

#### Instalar Flask no cliente se for rodar server web. pip install flask

#### 2. Iniciar o Servidor MQTT
Em outro terminal:
```
python servidor.py
```

O servidor:
- Conecta ao broker MQTT
- Escuta os tópicos `cliente_ID/envio`
- Processa as mensagens
- Responde no tópico `cliente_ID/retorno`

#### 3. Iniciar um ou mais Clientes MQTT

Cada cliente deve usar um **ID único**. Exemplo:

```
python client.py cliente_A
python client.py cliente_B
```

Cada cliente:
- Publica no tópico `cliente_X/envio`
- Recebe no tópico `cliente_X/retorno`

---

### 📤 Enviar Arquivo via Cliente MQTT

Durante a execução, o cliente solicitará o **caminho completo** de um arquivo `.txt`. Exemplo:

```
C:\Users\Usuario\Desktop\texto.txt
```

O cliente:
- Lê o conteúdo do arquivo
- Envia para o servidor
- Aguarda resposta no tópico `cliente_ID/retorno`

---

## 📌 Observações Finais

- O modo HTTP é ideal para visualizar e baixar imagens via navegador ou terminal.
- O modo MQTT simula um ambiente de mensagens com múltiplos clientes, usando publicação/assinatura.
- Pode-se rodar os dois modos em paralelo (em diferentes portas/processos).

---

## 👨‍💻 Autoria

Este projeto foi desenvolvido por Miguel,Hugo, Paulo e Sérgio como parte da disciplina **Redes de Computadores 1, no período 2025.1, ministrada pelo professor Hemir Santiago**.

---
