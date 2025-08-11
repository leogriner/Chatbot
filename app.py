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


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == "leotech123":
            return challenge
        return "Token inválido", 403

    elif request.method == "POST":
        try:
            data = request.get_json()
            entry = data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                print("⚠️ Nenhuma mensagem recebida.")
                return jsonify({"status": "sem mensagens"}), 200

            msg = messages[0]["text"]["body"]
            sender = messages[0]["from"]

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

            return jsonify({"status": "mensagem processada com sucesso"}), 200

        except Exception as e:
            print(f"❌ Erro no webhook: {e}")
            return jsonify({"error": str(e)}), 500


def gerar_resposta_ia(mensagens):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat-v3-0324:free",
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
        url = f"https://graph.facebook.com/v19.0/{os.getenv('META_PHONE_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('META_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": text
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        print("📤 Enviando mensagem...")
        print("📨 Conteúdo:", text)
        print("🔁 Resposta da Meta:", response.status_code, response.text)

        if response.status_code != 200:
            print("❌ Erro ao enviar mensagem:", response.text)
        else:
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
