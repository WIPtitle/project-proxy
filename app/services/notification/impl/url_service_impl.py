import os

from app.model.ExternalUrls import ExternalUrls
from app.services.notification.url_service import UrlService
from app.utils.read_credentials import read_credentials


class UrlServiceImpl(UrlService):
    def __init__(self):
        self.lt_credentials = read_credentials(os.getenv('LT_CREDENTIALS_FILE'))


    def get_external_urls(self) -> ExternalUrls:
        return ExternalUrls(
            backend=self.lt_credentials['URL_BACKEND'],
            frontend=self.lt_credentials['URL_FRONTEND'],
            ntfy=self.lt_credentials['URL_NTFY']
        )