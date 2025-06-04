class PCloudException(Exception):
    """Custom exception for pCloud SDK errors"""

    def __init__(self, message: str, code: int = 5000):
        super().__init__(message)
        self.code = code