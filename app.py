from chatbot_engine import gerar_resposta
from prompts import get_prompt
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot"]
mensagens = db["mensagens"]

def modo_terminal():
    print("🧪 Chat LeoTech (modo local)")
    print("Digite 'sair' para encerrar.\n")

    historico = [get_prompt()]

    while True:
        try:
            user_msg = input("Você: ").strip()
            if user_msg.lower() == "sair":
                print("Encerrando...")
                break

            historico.append({"role": "user", "content": user_msg})
            resposta = gerar_resposta(historico)
            print(f"Bot: {resposta}\n")
            historico.append({"role": "assistant", "content": resposta})

            mensagens.insert_one({
                "numero": "teste_local",
                "pergunta": user_msg,
                "resposta": resposta
            })

        except Exception as e:
            print(f"[ERRO]: {e}")

if __name__ == "__main__":
    modo_terminal()
