import os
from dotenv import load_dotenv
import json
from groq import Groq
from app.schemas import ProductInput, ProductOutput


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


EXPECTED_SPEC_KEYS = [
    "диапазон измерений",
    "класс точности",
    "присоединение",
    "диаметр корпуса",
    "питание",
    "интерфейсы",
    "тип корпуса",
]

SYSTEM_PROMPT = """Ты — копирайтер B2B-магазина контрольно-измерительных 
приборов.
Твоя задача — написать текст карточки товара строго по входным данным.

ЖЁСТКИЕ ПРАВИЛА (нарушение = брак):
1. Используй только те факты, которые явно есть в полях "Название",
   "Производитель", "Характеристики" и "Описание".
2. Запрещено добавлять что-либо, чего нет во входных данных:
   материал корпуса, устойчивость к средам/вибрациям/коррозии,
   отрасли применения, калибровку, монтаж, интеграцию с системами,
   шкалу, стрелку, цифры на циферблате, срок службы, стандарты.
3. Если характеристика отсутствует — не упоминай её вообще.
   Не пиши "данных нет" в тексте описания — просто опускай.
4. Не интерпретируй значения: пиши "класс точности 1,5", а не "1,5 %",
   если процента нет во входе.

ТРЕБОВАНИЯ К ПОЛЯМ:
- seo_title: до 70 символов. Включи название, производителя и 1–2
  ключевые характеристики из входа.
- seo_description: 800–1200 символов. Живой связный текст. Если реальных
  данных мало — развёрнуто опиши назначение прибора словами из поля
  "Описание", но без новых фактов.
- search_queries: 3–5 реалистичных поисковых фраз, под которые логично
  оптимизировать страницу. Только по фактам из входа.
- commercial_block: 2–4 предложения. Кому подходит прибор и какие задачи
  решает — на основе назначения из поля "Описание", без выдуманных отраслей.

Верни строго JSON:
{
  "seo_title": "до 70 символов",
  "seo_description": "800-1200 символов",
  "search_queries": ["3-5 запросов"],
  "commercial_block": "2-4 предложения: кому и зачем"
}"""


def generate_product_card(product: ProductInput) -> ProductOutput:
    """Запрашивает у Groq текст карточки, собирает характеристики и пропуски."""
    specs = product.specs.model_dump(exclude_none=True, by_alias=True)

    user_prompt = (
        f"Название: {product.name}\n"
        f"Производитель: {product.manufacturer}\n"
        f"Характеристики: {json.dumps(specs, ensure_ascii=False)}\n"
        f"Описание: {product.description or 'нет'}\n\n"
        f"Сделай карточку."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        generated = json.loads(response.choices[0].message.content)
    except Exception as error:
        raise RuntimeError(f"Ошибка Groq API: {error}")

    key_specs = {}
    for spec_name in EXPECTED_SPEC_KEYS:
        key_specs[spec_name] = specs.get(spec_name, "данных нет")
    for spec_name, spec_value in specs.items():
        if spec_name not in key_specs:
            key_specs[spec_name] = spec_value

    missing_fields = [
        spec_name for spec_name in EXPECTED_SPEC_KEYS
        if spec_name not in specs
    ]
    if not product.description:
        missing_fields.append("description")

    return ProductOutput(
        seo_title=generated.get("seo_title", ""),
        seo_description=generated.get("seo_description", ""),
        key_specs=key_specs,
        search_queries=generated.get("search_queries", []),
        commercial_block=generated.get("commercial_block", ""),
        missing_fields=missing_fields
    )
