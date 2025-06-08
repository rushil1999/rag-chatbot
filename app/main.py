from typing import Union
from app.api.v1.endpoints import router as endpoints_router
from app.middlewares.http_request import log_request, authenticate_request
from fastapi import FastAPI


app = FastAPI(debug=True)
 
# To start the app, go to root folder, outside of /app
# Run uvicorn app.main:app --reload


# Include your router (which contains all endpoints)
app.middleware("http")(authenticate_request)
app.middleware("http")(log_request)
app.include_router(endpoints_router)