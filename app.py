from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
import openai
import requests
import os

# Carrega variáveis do .env
load_dotenv()

# Inicializa Flask
app = Flask(__name__)

# Configura a OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Conecta ao MongoDB Atlas
client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot"]
mensagens = db["mensagens"]

# Webhook do WhatsApp
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    msg = data.get("message", "")
    sender = data.get("sender", "")

    print(f"📨 Mensagem de {sender}: {msg}")

    # Gera resposta com IA
    resposta = gerar_resposta_ia(msg)

    # Salva no banco
    mensagens.insert_one({"numero": sender, "pergunta": msg, "resposta": resposta})

    # Envia mensagem de volta pelo WhatsApp
    enviar_resposta_whatsapp(sender, resposta)

    return jsonify({"status": "mensagem processada com sucesso"})

# Função que usa a OpenAI para gerar resposta
def gerar_resposta_ia(pergunta):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": pergunta}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Erro com a OpenAI:", e)
        return "Desculpe, não consegui entender. Pode reformular?"

# Função que envia mensagem de volta via Z-API
def enviar_resposta_whatsapp(phone, text):
    try:
        requests.post(
            f"{os.getenv('ZAPI_URL')}/send-message",
            headers={"apikey": os.getenv("ZAPI_KEY")},
            json={"phone": phone, "message": text}
        )
        print("✅ Mensagem enviada com sucesso.")
    except Exception as e:
        print("❌ Erro ao enviar mensagem:", e)

# Inicia o servidor
if __name__ == "__main__":
    app.run(port=3000, debug=True)
