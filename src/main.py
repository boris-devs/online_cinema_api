from fastapi import FastAPI

from routes import accounts_router, movies_router
app = FastAPI()


api_prefix = "/api"

app.include_router(accounts_router, prefix=f"{api_prefix}/accounts", tags=["accounts"])
app.include_router(movies_router, prefix=f"{api_prefix}/catalog", tags=["catalog"])