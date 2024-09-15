from fastapi import Request

from app.clients.auth_client import AuthClient


class AuthMiddleware:
    def __init__(self, auth_client: AuthClient):
        self.auth_client = auth_client

    async def dispatch(self, request: Request):
        token = request.headers.get("Authorization")
        print(token)
        #self.auth_client.get_authenticated_user()