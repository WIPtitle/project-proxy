from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.clients.auth_client import AuthClient
from app.config.handlers import get_exception_handlers
from app.exceptions.authentication_exception import AuthenticationException
from app.exceptions.authorization_exception import AuthorizationException
from app.routers.impl.auth_middleware import AuthMiddleware
from app.routers.impl.proxy_router import ProxyRouter
from app.routers.router_wrapper import RouterWrapper

exception_handlers = get_exception_handlers()
routers: List[RouterWrapper] = [
    ProxyRouter()
]

app = FastAPI()
middleware = AuthMiddleware(AuthClient())


@app.middleware("http")
async def check_authorization(request: Request, call_next):
    try:
        await middleware.dispatch(request)
        response = await call_next(request)
    except AuthorizationException as e:
        response = JSONResponse({"detail": str(e.message)}, status_code=403)
    except AuthenticationException as e:
        response = JSONResponse({"detail": str(e.message)}, status_code=401)
    return response


origins = [
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for exc, handler in exception_handlers:
    app.add_exception_handler(exc, handler)

for router in routers:
    app.include_router(router.get_fastapi_router())
