import httpx
from fastapi import Request, HTTPException

from app.config.bindings import inject
from app.exceptions.service_not_exists_exception import ServiceNotExistsException
from app.routers.router_wrapper import RouterWrapper


class ProxyRouter(RouterWrapper):

    # There is really nothing to inject here since the proxy service currently doesn't need to interact with anything,
    # it just routes requests. Though you never really know, so the basic database connector is included in this
    # project.
    @inject
    def __init__(self):
        super().__init__(prefix=f"")
        # This defines the mapping that the proxy uses, where the first string is the prefix client should use and the
        # second is the service that will be called (must coincide with name of docker service or ip if needed).
        self.service_mapping = {
            "reed": "magnetic-reed-listener",
            "core": "project-core"
        }


    async def _proxy(self, request: Request, input_service: str, path: str):
        output_service = self.service_mapping.get(input_service)
        if output_service is None:
            raise ServiceNotExistsException("Routing failed: specified prefix isn't mapped to a service")

        url = f"http://{output_service}:8000/{path}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers=request.headers,
                    content=await request.body()
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                # Propagate return error from services
                raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)
        return response


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
