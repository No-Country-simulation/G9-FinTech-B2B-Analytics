from fastapi import FastAPI

app = FastAPI(title="PriceScope API")

@app.get("/")
def home():
    return {"mensaje": "PriceScope API funcionando"}