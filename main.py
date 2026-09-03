import os
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

app = FastAPI()

# CORS: pozwól tylko Twojemu rozszerzeniu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://twoje-id-rozszerzenia"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

SYSTEM_PROMPT = """Jesteś ekspertem e-commerce. Przeanalizuj podany tekst strony i wyciągnij z niego listę widocznych produktów."""


class Product(BaseModel):
    title: str = Field(description="Nazwa produktu")
    price: Optional[str] = Field(default=None, description="Cena z walutą")
    description: Optional[str] = Field(
        default=None, description="Informacje o produkcie"
    )
    imageUrl: Optional[str] = Field(
        default=None, description="Adres URL zdjęcia produktu"
    )
    link: Optional[str] = Field(default=None, description="Link do produktu")


class ProductList(BaseModel):
    products: List[Product] = Field(description="Lista wykrytych produktów na stronie")


class ParseRequest(BaseModel):
    html: str


class ParseResponse(BaseModel):
    success: bool
    products: List[Product] = []
    error: Optional[str] = None


API_KEY = "sk-3M_GzWIJ0bPkTwsmPv_kOQ"  # ustawiane jako env var na Render


@app.post("/parse", response_model=ParseResponse)
async def parse_products(payload: ParseRequest):
    if not payload.html:
        raise HTTPException(status_code=400, detail="Brak pola 'html'")

    clean_text = " ".join(payload.html.split())[:500000]

    try:
        model = ChatOpenAI(
            model="vertex_ai/gemini-2.5-flash",
            api_key=API_KEY,
            temperature=0,
            base_url="https://llmproxy.ai.orange",
        )

        structured_model = model.with_structured_output(ProductList)

        prompt = f"{SYSTEM_PROMPT}\n\nOto treść strony:\n{clean_text}"
        result: ProductList = await structured_model.ainvoke(prompt)

        return ParseResponse(success=True, products=result.products)

    except Exception as e:
        return ParseResponse(success=False, error=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
