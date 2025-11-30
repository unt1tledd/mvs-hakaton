from config import OPEN_ROUTER_API
import requests

OPEN_ROUTER_URL = "https://openrouter.io/api/v1"
MODEL = "meta-llama/llama-3.3-70b-instruct"

def build_prompt(question: str, data:str):
    context = ""
    if data:
        context = f"Данные для анализа: {data}"

    return context + f"Вопрос:{question}"
def ask_llm(prompt: str):
    pass



