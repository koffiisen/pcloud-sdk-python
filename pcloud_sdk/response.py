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

    def _parse_json(self):
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

        return self.response_data

    def _parse_response(self) -> Dict[str, Any]:
        """Parse response data, excluding 'result' field"""
        result = {}
        for key, value in self.response_data.items():
            if key != "result":
                result[key] = value
        return result
