class Config:
    """Configuration class with API hosts and settings"""

    US_HOST = "https://api.pcloud.com/"
    EU_HOST = "https://eapi.pcloud.com/"
    FILE_PART_SIZE = 10485760  # 10MB chunks

    @staticmethod
    def get_api_host_by_location_id(location_id: int) -> str:
        """Get API host URL based on location ID"""
        if location_id == 2:
            return Config.EU_HOST
        else:
            return Config.US_HOST
