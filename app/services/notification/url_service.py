from abc import ABC, abstractmethod

from app.model.ExternalUrls import ExternalUrls


class UrlService(ABC):
    @abstractmethod
    def get_external_urls(self) -> ExternalUrls:
        pass

