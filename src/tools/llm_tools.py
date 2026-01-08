import os
import re
import json
from crewai import LLM

class GroqLLMFactory:
    @staticmethod
    def create():
        groq_key = os.getenv("GROQ_API_KEY")

        if not groq_key or not groq_key.startswith("gsk_"):
            return None

        return LLM(
            model="groq/llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=512,
            api_key=groq_key,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
        )


class OrderExtractor:
    def __init__(self, llm=None):
        self.llm = llm

    def extract(self, message: str) -> dict:
        if self.llm:
            result = self._extract_with_llm(message)
            if result:
                return result
        return self._extract_fallback(message)

    def _extract_with_llm(self, message: str):
        prompt = f"""
Extrae un pedido en JSON estricto.

Mensaje:
"{message}"

Productos:
- Pizza Margarita
- Pizza Pepperoni
- Ensalada César
- Hamburguesa Clásica
- Coca-Cola
- Agua Mineral

Formato:
{{
  "items": [{{"name": "Producto", "quantity": 1}}],
  "requested_time": "HH:MM PM" | "ASAP",
  "notes": ""
}}
"""
        try:
            response = self.llm.call(prompt)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            return json.loads(match.group()) if match else None
        except Exception:
            return None

    def _extract_fallback(self, message: str):
        message = message.lower()
        items = []

        patterns = [
            (r'(\d+)\s*pizzas?\s*margarita', 'Pizza Margarita'),
            (r'(\d+)\s*hamburguesas?', 'Hamburguesa Clásica'),
            (r'(\d+)\s*coca', 'Coca-Cola'),
        ]

        for pattern, name in patterns:
            m = re.search(pattern, message)
            if m:
                items.append({
                    "name": name,
                    "quantity": int(m.group(1))
                })

        return {
            "items": items or [{"name": "Pizza Margarita", "quantity": 1}],
            "requested_time": "ASAP",
            "notes": ""
        }
