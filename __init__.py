

API_ENDPOINT = "https://api-v3.wattwatchers.com.au"
API_KEY = ''
HEADERS = {
    'Authorization': 'Bearer '+ API_KEY,
    'Content-Type': 'application/json'
}
TIMEOUT = (5, 30)
RETRY = None

from .client import Client, getRequest
from .exceptions import CommonError
from .models import (
    RateLimits, ShortData, 
    LongData, ModbusData, Device)

