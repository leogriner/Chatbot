import requests
import os
from dotenv import load_dotenv
from prompts import get_prompt

load_dotenv()

def gerar_resposta(historico):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": historico
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[ERRO] Falha na OpenRouter: {e}")
        return "Desculpe, não consegui responder. Tente novamente."
