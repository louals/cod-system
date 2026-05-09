from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import products, orders, auth
from config import settings
import traceback
import sys

app = FastAPI(
    title=settings.app_name,
    description="A premium API for Cash on Delivery E-commerce with User tracking",
    version="1.0.0",
    debug=settings.debug
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diagnostic Middleware to catch and print hidden errors
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print("\n" + "="*50)
        print("--- INTERNAL SERVER ERROR DIAGNOSTIC ---")
        print(f"Error: {str(e)}")
        print(f"Path: {request.url.path}")
        print("Traceback:")
        traceback.print_exc(file=sys.stdout)
        print("="*50 + "\n")
        raise e

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "status": "online",
        "docs": "/docs"
    }

# Include Routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
