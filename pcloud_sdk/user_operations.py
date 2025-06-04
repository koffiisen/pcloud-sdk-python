from typing import Dict, Any

from pcloud_sdk.app import App
from pcloud_sdk.request import Request


class User:
    """User class for user information"""

    def __init__(self, app: App):
        self.request = Request(app)
        self.user_info = self.request.get("userinfo")

    def get_user_info(self) -> Dict[str, Any]:
        """Get full user info"""
        return self.user_info

    def get_user_id(self) -> int:
        """Get user ID"""
        return int(self.user_info['userid'])

    def get_user_email(self) -> str:
        """Get user email"""
        return str(self.user_info['email'])

    def get_used_quota(self) -> int:
        """Get used quota in bytes"""
        return int(self.user_info['usedquota'])

    def get_quota(self) -> int:
        """Get total quota in bytes"""
        return int(self.user_info['quota'])

    def get_public_link_quota(self) -> int:
        """Get public link quota"""
        return int(self.user_info['publiclinkquota'])
