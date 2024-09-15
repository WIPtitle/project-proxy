from typing import List

from fastapi import FastAPI, Request

from app.clients.auth_client import AuthClient
from app.config.handlers import get_exception_handlers
from app.routers.impl.auth_middleware import AuthMiddleware
from app.routers.impl.proxy_router import ProxyRouter
from app.routers.router_wrapper import RouterWrapper

exception_handlers = get_exception_handlers()
routers: List[RouterWrapper] = [
    ProxyRouter()
]

app = FastAPI()

for exc, handler in exception_handlers:
    app.add_exception_handler(exc, handler)

for router in routers:
    app.include_router(router.get_fastapi_router())
