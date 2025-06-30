from typing import Union
from app.api.v1.endpoints import router as endpoints_router
from app.middlewares.http_request import log_request, authenticate_request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(debug=True)

# ✅ FIRST: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://rushil1999.github.io/portfolio",
        "https://rushilshah.github.io"
    ],  # safer than "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ✅ THEN: Add your custom middlewares
app.middleware("http")(authenticate_request)
app.middleware("http")(log_request)

# ✅ Route registration
app.include_router(endpoints_router)


# To start the app, go to root folder, outside of /app
# Run uvicorn app.main:app --reload