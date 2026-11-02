from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import ProductInput, ProductOutput
from app.llm import generate_product_card

load_dotenv()

app = FastAPI(
    title="AI-помощник для товарных описаний",
    description="Генерирует черновик карточки товара на основе данных о КИП",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/api/generate", response_model=ProductOutput)
async def generate(product: ProductInput):
    """
    Принимает данные о товаре в JSON и возвращает черновик карточки.

    Если каких-то полей не хватает, они будут перечислены в `missing_fields`,
    а в характеристиках будет указано «данных нет».
    """
    if not product.specs.model_dump(exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Отсутствуют все технические характеристики",
                "hint": (
                    "Заполните хотя бы одно поле в specs для генерации "
                    "карточки."
                ),
            },
        )

    try:
        return generate_product_card(product)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка: {error}",
        )
