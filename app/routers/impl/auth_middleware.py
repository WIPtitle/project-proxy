import re

from urllib.parse import urlparse

from fastapi import Request

from app.clients.auth_client import AuthClient
from app.exceptions.authentication_exception import AuthenticationException
from app.exceptions.authorization_exception import AuthorizationException


class AuthMiddleware:
    def __init__(self, auth_client: AuthClient):
        self.auth_client = auth_client
        self.permission_map = {
            (re.compile(r"^/auth/token$"), "POST"): None,
            (re.compile(r"^/auth/user$"), "GET"): None,
            (re.compile(r"^/auth/permissions$"), "GET"): None,
            (re.compile(r"^/users$"), "GET"): None,
            (re.compile(r"^/users$"), "PUT"): None,
            (re.compile(r"^/users$"), "DELETE"): None,
            (re.compile(r"^/users/first$"), "POST"): None,
            (re.compile(r"^/users$"), "POST"): "USER_MANAGER",
            (re.compile(r"^/disk-usage$"), "GET"): None,
            (re.compile(r"^/camera$"), "GET"): None,
            (re.compile(r"^/camera$"), "POST"): "MODIFY_DEVICES",
            (re.compile(r"^/camera$"), "PUT"): "MODIFY_DEVICES",
            (re.compile(r"^/camera$"), "DELETE"): "MODIFY_DEVICES",
            (re.compile(r"^/camera/generic$"), "GET"): None,
            (re.compile(r"^/camera/[^/]+/stream$"), "GET"): "ACCESS_STREAM_CAMERAS",
            (re.compile(r"^/recording$"), "GET"): "ACCESS_RECORDINGS",
            (re.compile(r"^/recording/download$"), "GET"): "ACCESS_RECORDINGS",
            (re.compile(r"^/recording/stream$"), "GET"): "ACCESS_RECORDINGS",
            (re.compile(r"^/device-group$"), "GET"): None,
            (re.compile(r"^/device-group$"), "POST"): "MODIFY_DEVICES",
            (re.compile(r"^/device-group$"), "PUT"): "MODIFY_DEVICES",
            (re.compile(r"^/device-group$"), "DELETE"): "MODIFY_DEVICES",
            (re.compile(r"^/device-group/\d+/start-listening$"), "POST"): "START_ALARM",
            (re.compile(r"^/device-group/\d+/stop-listening$"), "POST"): "STOP_ALARM",
            (re.compile(r"^/device-group/\d+/devices$"), "GET"): None,
            (re.compile(r"^/device-group/\d+/devices$"), "POST"): "MODIFY_DEVICES",
            (re.compile(r"^/mail-config$"), "GET"): None,
            (re.compile(r"^/mail-config$"), "POST"): "CHANGE_MAIL_CONFIG",
            (re.compile(r"^/audio"), "GET"): None,
            (re.compile(r"^/audio"), "POST"): "CHANGE_ALARM_SOUND",
        }


    async def dispatch(self, request: Request):
        request_url = str(request.url)
        parsed_url = urlparse(request_url)
        path = parsed_url.path
        service_name = path.split('/')[1]
        path_after_service = path[len(service_name) + 1:]
        method = request.method

        token = request.headers.get("Authorization")
        user = await self.auth_client.get_authenticated_user(token)

        # Search inside of map the matching endpoint. Desc ordered because we want the "most matching" endpoint chosen
        # (/service/path should match with /service/path before /service, even if startswith is true for both).
        # Using startswith to check endpoints and letting some margin of error (/service/, /service?param=x and /service should all match)
        required_permission = None
        sorted_endpoints = sorted(self.permission_map.keys(), key=lambda x: len(x[0].pattern), reverse=True)
        for (endpoint_pattern, http_method) in sorted_endpoints:
            if endpoint_pattern.match(path_after_service) and method == http_method:
                required_permission = self.permission_map[(endpoint_pattern, http_method)]
                break

        if required_permission is not None:
            if user is None:
                raise AuthenticationException("Not authenticated")
            elif required_permission not in user.permissions:
                raise AuthorizationException("Not authorized")
