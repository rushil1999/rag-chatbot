import time
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.service.logging import logging
import os
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

async def log_request(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    logging.info("Request Log: {request.method} {request.url.path} took {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response


async def authenticate_request(request: Request, call_next):
  if request.method == "OPTIONS":
    return await call_next(request)
  required_user_token = f'Bearer {os.getenv("USER_TOKEN")}'
  headers = dict(request.scope['headers'])
  request_token = request.headers.get('authorization')
  if request_token != required_user_token:
    logging.info(f"Request Log: {request.method} {request.url.path} Unauthorized")
    return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized"}
        )
  response = await call_next(request)
  return response