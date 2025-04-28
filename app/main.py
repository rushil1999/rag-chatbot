from typing import Union
from app.api.v1.endpoints import router as endpoints_router
from fastapi import FastAPI


app = FastAPI()



# Include your router (which contains all endpoints)
app.include_router(endpoints_router)