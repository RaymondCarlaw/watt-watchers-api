from .models import RateLimits
from typing import Dict


class CommonError(Exception):

    def __init__(self, content: Dict[str, str], rateLimits: RateLimits):
        self.Code: str = content.get('code')
        self.HttpCode: str = content.get('httpCode')
        self.Message: str = content.get('message')
        self.RateLimits: RateLimits = rateLimits

    def __str__(self):
        return f'{self.Code}: {self.Message}'