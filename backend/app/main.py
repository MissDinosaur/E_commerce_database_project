from fastapi import FastAPI
from app.routes import auth, products, transactions, fraud, cursor
import uvicorn

app = FastAPI(title="Fraud Detection API")

# Include API routes
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(fraud.router, prefix="/api")
app.include_router(cursor.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Fraud Detection API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
