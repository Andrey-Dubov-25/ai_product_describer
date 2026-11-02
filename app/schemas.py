from pydantic import BaseModel, Field
from typing import Optional


class ProductSpecs(BaseModel):
    """
    Технические характеристики прибора. Незаполненные поля - 'данных нет'.
    """
    range: Optional[str] = Field(None, alias="диапазон измерений")
    accuracy: Optional[str] = Field(None, alias="класс точности")
    connection: Optional[str] = Field(None, alias="присоединение")
    body_diameter: Optional[str] = Field(None, alias="диаметр корпуса")
    power: Optional[str] = Field(None, alias="питание")
    interfaces: Optional[str] = Field(None, alias="интерфейсы")
    housing_type: Optional[str] = Field(None, alias="тип корпуса")

    model_config = {"populate_by_name": True, "extra": "allow"}


class ProductInput(BaseModel):
    """Входные данные о товаре."""
    name: str
    manufacturer: str
    specs: ProductSpecs
    description: Optional[str] = None


class ProductOutput(BaseModel):
    """Черновик карточки товара, готовый для контент-менеджера."""
    seo_title: str
    seo_description: str
    key_specs: dict
    search_queries: list[str]
    commercial_block: str
    missing_fields: list[str]