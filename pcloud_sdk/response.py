import json
from typing import Dict, Any

from pcloud_sdk.exceptions import PCloudException


class Response:
    """Class to handle API responses"""

    def __init__(self, response_data: Any, status_code: int, content_type: str):
        self.response_data = response_data
        self.status_code = status_code
        self.content_type = content_type
        self._parse_json()

    def _parse_json(self) -> None:
        """Parse JSON response if content type is JSON"""
        if isinstance(self.response_data, str) and "application/json" in self.content_type:
            try:
                self.response_data = json.loads(self.response_data)
            except json.JSONDecodeError:
                pass

    def get(self) -> Dict[str, Any]:
        """Get parsed response data"""
        if self.status_code != 200:
            raise PCloudException(f"HTTP Code = {self.status_code}")

        if isinstance(self.response_data, dict):
            if self.response_data.get('result') == 0:
                return self._parse_response()
            else:
                raise PCloudException(self.response_data.get('error', 'Unknown error'))

        # If self.response_data is not a dict, and status_code was 200,
        # it means it's likely a non-JSON response (e.g. file download) or malformed JSON.
        # The original code `return self.response_data` would violate Dict[str, Any].
        # So, we should raise an exception if this method is called expecting a Dict.
        raise PCloudException(
            f"Response data is not a dictionary, but a dictionary was expected. Type: {type(self.response_data).__name__}"
        )

    def _parse_response(self) -> Dict[str, Any]:
        """Parse response data, excluding 'result' field"""
        result = {}
        for key, value in self.response_data.items():
            if key != "result":
                result[key] = value
        return result
