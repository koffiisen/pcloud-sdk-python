import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from urllib.parse import urlencode

import requests
import urllib3

from pcloud_sdk.config import Config
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.response import Response

# Désactiver les warnings SSL de façon propre
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from pcloud_sdk.account import Account  # Added import

if TYPE_CHECKING:
    pass  # App import can be removed if not used elsewhere, or replaced if Account is needed for type hinting HttpClient if it changed


class HttpClient:
    """HTTP client with retry logic"""

    def __init__(self, timeout: int = 3600):
        self.session = requests.Session()
        self.timeout = timeout
        self.session.headers.update({"User-Agent": "pCloud Python SDK"})

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Execute HTTP request with retry logic"""
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault(
            "verify", False
        )  # SSL verification disabled like in PHP version

        # Retry logic (up to 4 attempts)
        for attempt in range(4):
            try:
                response = self.session.request(method, url, **kwargs)
                if response.status_code == 200:
                    return Response(
                        response.text,
                        response.status_code,
                        response.headers.get("content-type", ""),
                    )
            except Exception:
                if attempt == 3:
                    raise PCloudException("Connection lost!")
                time.sleep(1)

        raise PCloudException("Connection lost!")


class Request:
    """Request handler for API calls"""

    def __init__(self, account: "Account"):
        self.host = Config.get_api_host_by_location_id(account.location_id)

        # Utiliser le bon paramètre selon le type d'authentification
        access_token = account.access_token
        auth_type = account.auth_type

        if access_token:
            # The existing code used "direct" for username/password authentication (auth parameter)
            # and implicitly OAuth2 for "access_token" parameter.
            # We'll keep this logic. Account.auth_type defaults to "oauth2".
            if auth_type != "oauth2":  # Assuming any other type means direct auth
                self.global_params = {"auth": access_token}
            else:
                self.global_params = {"access_token": access_token}
        else:
            # Pas de token
            self.global_params = {}

        self.http_client = HttpClient(timeout=account.curl_exec_timeout)

    def get(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute GET request"""
        if params is None:
            params = {}

        url = self._prepare_url(method, {**self.global_params, **params})
        response = self.http_client.request("GET", url)
        return response.get()

    def post(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute POST request"""
        if params is None:
            params = {}

        url = self._prepare_url(method, self.global_params)
        response = self.http_client.request("POST", url, data=params)
        return response.get()

    def put(
        self,
        method: str,
        content: Union[str, bytes],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute PUT request (mainly for file uploads)"""
        if params is None:
            params = {}

        # Merge global params with request params
        all_params = {**self.global_params, **params}
        url = self._prepare_url(method, all_params)

        # Debug pour l'upload
        if method == "upload_write":
            print(f"      🌐 PUT URL: {url}")
            print(f"      📦 Content size: {len(content)} bytes")

        headers = {"Content-Type": "application/octet-stream"}
        response = self.http_client.request("PUT", url, data=content, headers=headers)
        return response.get()

    def _prepare_url(self, method: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Prepare URL with method and parameters"""
        url = self.host + method
        if params:
            # Filtrer seulement les paramètres vraiment vides (None, "", etc.)
            # IMPORTANT: Ne pas filtrer 0 car uploadoffset=0 est valide !
            filtered_params = {
                k: v for k, v in params.items() if v is not None and v != ""
            }
            if filtered_params:
                url += "?" + urlencode(filtered_params)
        return url
