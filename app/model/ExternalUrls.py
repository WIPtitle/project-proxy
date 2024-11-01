from sqlmodel import SQLModel


class ExternalUrls(SQLModel):
    backend: str
    frontend: str
    ntfy: str

    def __init__(self, backend: str, frontend: str, ntfy: str):
        self.backend = backend
        self.frontend = frontend
        self.ntfy = ntfy
