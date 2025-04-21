from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
import os
import sys

app = Flask(__name__)

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["henryleo"]
mensagens = db["mensagens"]


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    msg = data.get("message", "")
    sender = data.get("sender", "")

    print(f"📨 Mensagem de {sender}: {msg}")

    resposta = gerar_resposta_ia([
        {
            "role": "system",
            "content": (
                "Você é um atendente virtual educado e direto da empresa LeoTech.\n"
                "Converse com o cliente como se estivesse em um chat contínuo e amigável.\n"
                "A LeoTech vende e faz manutenção de computadores e acessórios.\n"
                "Atendimento: segunda a sexta, das 9h às 18h.\n"
                "Pagamentos aceitos: Pix, cartão de crédito e débito.\n"
            )
        },
        {"role": "user", "content": msg}
    ])

    mensagens.insert_one({"numero": sender, "pergunta": msg, "resposta": resposta})
    enviar_resposta_whatsapp(sender, resposta)

    return jsonify({"status": "mensagem processada com sucesso"})

def gerar_resposta_ia(mensagens):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": mensagens
            }
        )
        data = response.json()

        if "choices" not in data or not data["choices"]:
            print("⚠️ Resposta inesperada da OpenRouter:", data)
            return "Desculpe, a IA não retornou uma resposta válida."

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ Erro com a OpenRouter: {e}")
        return "Desculpe, houve um problema técnico. Tente novamente."


def enviar_resposta_whatsapp(phone, text):
    try:
        requests.post(
            f"{os.getenv('ZAPI_URL')}/send-message",
            headers={"apikey": os.getenv("ZAPI_KEY")},
            json={"phone": phone, "message": text}
        )
        print("✅ Mensagem enviada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao enviar WhatsApp: {e}")

def modo_teste_local():
    print("🧪 MODO DE TESTE LOCAL ATIVO")
    print("Digite 'sair' para encerrar.\n")

    historico = [
        {
            "role": "system",
            "content": (
                "Você é um atendente virtual educado, amigável e direto da empresa LeoTech.\n"
                "Sempre converse com o cliente de forma natural, como num chat contínuo.\n"
                "Nunca diga que você é uma IA.\n"
                "A LeoTech vende e faz manutenção de computadores e acessórios.\n"
                "Horário: segunda a sexta, das 9h às 18h.\n"
                "Pagamentos aceitos: Pix, cartão de crédito e débito.\n"
                "Esteja sempre pronto para responder a próxima pergunta.\n"
            )
        }
    ]

    while True:
        try:
            sys.stdout.flush()
            msg = input("Você: ").strip()

            if msg.lower() == "sair":
                print("Encerrando chat. Até logo!")
                break

            if not msg:
                continue  # Ignora mensagens vazias

            historico.append({"role": "user", "content": msg})
            resposta = gerar_resposta_ia(historico)
            historico.append({"role": "assistant", "content": resposta})

            print(f"Bot: {resposta}\n", flush=True)

            mensagens.insert_one({
                "numero": "teste_local",
                "pergunta": msg,
                "resposta": resposta
            })

        except KeyboardInterrupt:
            print("\n👋 Chat encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            continue

# Executa o modo local ou servidor
if __name__ == "__main__":
    if os.getenv("MODO_TESTE") == "sim":
        modo_teste_local()
    else:
        app.run(port=3000, debug=True)
