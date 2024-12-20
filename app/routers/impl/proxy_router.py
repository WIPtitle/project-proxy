import os

import httpx
from fastapi import Request, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.config.bindings import inject
from app.exceptions.service_not_exists_exception import ServiceNotExistsException
from app.routers.router_wrapper import RouterWrapper


class ProxyRouter(RouterWrapper):
    @inject
    def __init__(self):
        super().__init__(prefix=f"")
        # This defines the mapping that the proxy uses, where the first string is the prefix client should use and the
        # second is the service that will be called (must coincide with name of docker service or ip if needed).
        self.service_mapping = {
            "devices-manager-service": os.getenv('DEVICES_MANAGER_HOSTNAME'),
            "auth-service": os.getenv('AUTH_HOSTNAME'),
            "notifications-service": os.getenv('NOTIFICATIONS_MANAGER_HOSTNAME'),
            "audio-service": os.getenv('LOCAL_AUDIO_MANAGER_HOSTNAME')
        }


    async def _proxy(self, request: Request, input_service: str, path: str):
        output_service = self.service_mapping.get(input_service)
        if output_service is None:
            raise ServiceNotExistsException("Routing failed: specified prefix isn't mapped to a service")

        query_params = {k: v for k, v in request.query_params.items() if k != "auth_token"}
        url = f"http://{output_service}:8000/{path}"
        if query_params:
            url = f"{url}?{httpx.QueryParams(query_params)}"

        print(f"Routing request to {url}")
        try:
            # 'bit of an ugly hack, but I don't think there will be any other stream methods so cope with it, I'm tired
            if "stream" in url and request.method == "GET" and output_service == os.getenv('DEVICES_MANAGER_HOSTNAME'):
                print("Stream request in proxy detected, using stream method")

                async def stream_proxy_frames():
                    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                        async with client.stream("GET", url) as response:
                            async for chunk in response.aiter_bytes():
                                yield chunk
                                if await request.is_disconnected():
                                    break

                media_type = "application/octet-stream"
                if "device-group" in url:
                    media_type = "text/event-stream"
                elif "camera" in url:
                    media_type = "text/event-stream"
                elif "recording" in url:
                    media_type = "video/webm"

                return StreamingResponse(stream_proxy_frames(), media_type=media_type)

            else:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.request(
                        method=request.method,
                        url=url,
                        headers=request.headers,
                        content=await request.body()
                    )
                    response.raise_for_status()
                return Response(content=response.content, status_code=response.status_code,
                                headers=dict(response.headers))
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


    def _define_routes(self):
        # Here HTTP methods are separated instead of passing all of them to "methods" to avoid the FastAPI warning
        # UserWarning: Duplicate Operation ID. This shouldn't affect anything, really.

        @self.router.api_route("/{input_service}/{path:path}", methods=["GET"], operation_id="proxy_get")
        async def proxy_get(request: Request, input_service: str, path: str):
            return await self._proxy(request, input_service, path)

        @self.router.api_route("/{input_service}/{path:path}", methods=["POST"], operation_id="proxy_post")
        async def proxy_post(request: Request, input_service: str, path: str):
            return await self._proxy(request, input_service, path)

        @self.router.api_route("/{input_service}/{path:path}", methods=["PUT"], operation_id="proxy_put")
        async def proxy_put(request: Request, input_service: str, path: str):
            return await self._proxy(request, input_service, path)

        @self.router.api_route("/{input_service}/{path:path}", methods=["DELETE"], operation_id="proxy_delete")
        async def proxy_delete(request: Request, input_service: str, path: str):
            return await self._proxy(request, input_service, path)
