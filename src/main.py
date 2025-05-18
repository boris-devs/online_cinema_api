from fastapi import FastAPI

from routes import accounts_router
app = FastAPI()


api_prefix = "/api/"

app.include_router(accounts_router, prefix=f"{api_prefix}/accounts", tags=["accounts"])
