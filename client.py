import requests
import json
from time import sleep
from datetime import datetime, timezone as dtTimezone, timedelta
from typing import Optional, List, Dict, Union, Tuple
from . import TIMEOUT, API_ENDPOINT, HEADERS, RETRY
from .exceptions import CommonError
from .enums import Energy, Groups, Granularity
from .utilities import NormaliseTimestamps, CreateQueryWindows
from .models import (
    RateLimits, RateLimitsSchema, Device, DeviceSchema,
    ShortData, ShortDataSchema, LongData, LongDataSchema,
    ModbusData, ModbusDataSchema,
    ChannelCategory, ChannelCategorySchema,
    DeviceModel, DeviceModelSchema)

__all__ = [
    "Client",
    "getRequest"
]

def _parseHeaders(response) -> RateLimits:
    headers = response.headers
    return RateLimitsSchema().load(headers)



def getRequest(
    url: str, 
    session: requests.Session, 
    timeout: Union[int, float, Tuple[int, int]] = 3,
    headers: Dict[str, str] = {},
    retry = 3,
    params = {},
    **kwargs
) -> bytes:
    params = {
        "timeout": timeout,
        "params": params,
        **kwargs, 
    }

    retryCount = 0
    while True:
        try:
            response = session.get(url, **params)
            
            rateLimits = _parseHeaders(response)
            if response.ok:
                return (response.content, rateLimits)
            elif response.status_code == requests.codes.too_many_requests and rateLimits.RemainingPerDay > 0:
                sleep(rateLimits.TotalPerSecondResetCounter + 0.2)
                retryCount += 1
            else:
                try:
                    content = response.json()
                    error = CommonError(content, rateLimits)
                except Exception:
                    response.raise_for_status()
                
                raise error

        except requests.exceptions.Timeout:
            if not retry or retryCount >= retry:
                break

            # linear backoff policy
            sleep((1 + retryCount))
            retryCount += 1


class Client:
    """
    Watt Watchers client for the Version 3 REST API
    """
    
    def __init__(self, 
            apiKey: str,
            timezone: str = None,
            timeout: Union[int, float, Tuple[int, int]] = None,
            retry: int = 3,
            headers: Dict[str, str] = None,
            hooks = None,
            endpoint: str = None
        ):
        self.timezone = timezone
        self.timeout = timeout or TIMEOUT
        self.retry = retry
        # modify headers
        # add hooks / requests changes
        # set default timezone
        self.endpoint = endpoint or API_ENDPOINT

        session = requests.Session()
        self.__session = session
        session.headers = {
            **HEADERS,
            **(headers or {}),
            "Authorization": "Bearer " + apiKey
        }

        if hooks:
            session.hooks = hooks

        self.__deviceSchema = DeviceSchema()
        self.__deviceSchema.context['client'] = self
        self.__shortDataSchema = ShortDataSchema()
        self.__longDataSchema = LongDataSchema()
        self.__modbusDataSchema = ModbusDataSchema()

        self.RateLimits = None
    
    def devices(self, **kwargs) -> List[Device]:
        """
        Retrieves all device ids and wraps them in a Device object.

        return : List[Device] - Device instances with only the Id set
        """

        url = f"{self.endpoint}/devices"
        
        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, **kwargs)
        self.RateLimits = rateLimits

        devices = []
        deviceIds = json.loads(content)
        for deviceId in deviceIds:
            devices.append(Device(deviceId, client=self))

        return devices

    def device(self, deviceId: str, **kwargs) -> Device:
        url = f"{self.endpoint}/devices/{deviceId}"
        
        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, **kwargs)
        self.RateLimits = rateLimits
        
        return self.__deviceSchema.loads(content)

    def updateDevice(self, deviceId: str, updateFields, **kwargs) -> Device:
        pass

    def channelCategories(self, **kwargs) -> List[ChannelCategory]:
        url = f"{self.endpoint}/devices/channel-categories"

        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, **kwargs)
        self.RateLimits = rateLimits

        return ChannelCategorySchema().loads(content, many=True)

    def modelTypess(self, **kwargs) -> List[DeviceModel]:
        url = f"{self.endpoint}/devices/models"

        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, **kwargs)
        self.RateLimits = rateLimits

        return DeviceModelSchema().loads(content, many=True)

    def shortEnergy(self, 
            deviceId:str, 
            fromTs: Union[int, datetime] = None,
            toTs: Union[int, datetime] = None,
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs) -> List[ShortData]:
        """
        Returns short energy data for a specific device. Typically this
        is every 30 seconds, but depends on the 
        shortEnergyReportingInterval setting of the device. Note that
        the duration may change if the shortEnergyReportingInterval on
        the device is changed in the time period being requested.

        if fromTs & toTS are not provided, then the last 12 hours are returned.

        deviceId : str - device id to query
        fromTs : int, datetime - from timestamp as epoch timestamp as int or python datetime class
        toTs : int, datetime - to timestamp epoch timestamp as int or python datetime class

        return : ShortEnergyData - interable/callable class for short energy data.
        """
        url = f"{self.endpoint}/short-energy/{deviceId}"
        maxQueryPeriod = timedelta(hours=12)

        fromTs, toTs = NormaliseTimestamps(fromTs, toTs, maxQueryPeriod)
        params = dict()

        if filter is not None:
            params['filter[group]'] = str(filter)

        self.__shortDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert[energy]'] = str(convert)
            self.__shortDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields[energy]'] = str(fields)

        data = []
        windows = CreateQueryWindows(fromTs, toTs, maxQueryPeriod)
        for period in windows:
            requestParams = {"fromTs": int(period[0].timestamp()), "toTs": int(period[1].timestamp()), **params}
            
            content, rateLimits = getRequest(url, 
                self.__session, self.timeout, 
                retry=self.retry, params=requestParams,
                **kwargs)
            self.RateLimits = rateLimits

            shortData = self.__shortDataSchema.loads(content, many=True)
            data.extend(shortData)

        return data
        

    def firstShortEnergy(self, 
            deviceId: str, 
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs) -> ShortData:

        url = f"{self.endpoint}/short-energy/{deviceId}/first"
        params = dict()

        if filter is not None:
            params['filter'] = str(filter)

        self.__shortDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert'] = str(convert)
            self.__shortDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields'] = str(fields)

        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, params=params,
            **kwargs)
        self.RateLimits = rateLimits

        shortData = self.__shortDataSchema.loads(content)
        return shortData

    def latestShortEnergy(self, 
            deviceId: str, 
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs) -> ShortData:

        url = f"{self.endpoint}/short-energy/{deviceId}/latest"
        params = dict()

        if filter is not None:
            params['filter[group]'] = str(filter)

        self.__shortDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert[energy]'] = str(convert)
            self.__shortDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields[energy]'] = str(fields)

        content, rateLimits = getRequest(url, 
            self.__session, self.timeout, 
            retry=self.retry, params=params,
            **kwargs)
        self.RateLimits = rateLimits

        shortData = self.__shortDataSchema.loads(content)
        return shortData

    def longEnergy(self, 
            deviceId: str, 
            fromTs: Union[int, datetime] = None,
            toTs: Union[int, datetime] = None,
            granularity: Union[str, Granularity] = Granularity.FifteenMinute,
            timezone: str = None,
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs) -> List[LongData]:

        maxQueryTimeMap = {
            Granularity.FiveMinute: (timedelta(days=7), timedelta(days=1)),
            Granularity.FifteenMinute: (timedelta(days=14), timedelta(days=1)),
            Granularity.HalfHourly: (timedelta(days=31), timedelta(days=1)),
            Granularity.Hourly: (timedelta(days=90), timedelta(days=1)),
            Granularity.Daily: (timedelta(days=360*3), timedelta(days=30)), # 3 years
            Granularity.Weekly: (timedelta(days=360*5), timedelta(days=90)), # 5 years
            Granularity.Monthly: (timedelta(days=360*10), timedelta(days=365)) # 10 years... approximately
        }

        if granularity not in maxQueryTimeMap:
            raise ValueError(granularity)
        
        maxQueryPeriod = maxQueryTimeMap[granularity][0]
        extendPeriod = maxQueryTimeMap[granularity][1]
        url = f"{self.endpoint}/long-energy/{deviceId}"

        params = {"granularity": str(granularity), "timezone": self.timezone}
        fromTs, toTs = NormaliseTimestamps(fromTs, toTs, extendPeriod)

        if filter is not None:
            params['filter[group]'] = str(filter)

        self.__longDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert[energy]'] = str(convert)
            self.__longDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields[energy]'] = str(fields)

        data = []; periods = []
        windows = CreateQueryWindows(fromTs, toTs, maxQueryPeriod)
        
        # if period is longer than 12 hours then batch calls
        for period in windows:
            requestParams = {"fromTs": int(period[0].timestamp()), "toTs": int(period[1].timestamp()), **params}
            
            content, rateLimits = getRequest(url, 
                self.__session, self.timeout, 
                retry=self.retry, params=requestParams,
                **kwargs)
            self.RateLimits = rateLimits
            
            longData = self.__longDataSchema.loads(content, many=True)
            data.extend(longData)

        return data

    def firstLongEnergy(self, 
            deviceId: str, 
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs):
        url = f"{self.endpoint}/long-energy/{deviceId}/first"
        params = {}

        if filter is not None:
            params['filter'] = str(filter)

        self.__longDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert'] = str(convert)
            self.__longDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields'] = str(fields)

        content, rateLimits = getRequest(url, 
                self.__session, self.timeout, 
                retry=self.retry, params=params,
                **kwargs)
        self.RateLimits = rateLimits

        return self.__longDataSchema.loads(content)

    def latestLongEnergy(self, 
            deviceId: str, 
            filter: Union[str, Groups] = None,
            convert: Union[str, Energy] = None,
            fields: Union[str, Energy] = None,
            **kwargs):

        url = f"{self.endpoint}/long-energy/{deviceId}/latest"
        params = {}

        if filter is not None:
            params['filter'] = str(filter)

        self.__longDataSchema.context['unit'] = Energy.Joules
        if convert is not None:
            params['convert'] = str(convert)
            self.__longDataSchema.context['unit'] = str(convert)

        if fields is not None:
            params['fields'] = str(fields)

        content, rateLimits = getRequest(url, 
                self.__session, self.timeout, 
                retry=self.retry, params=params,
                **kwargs)
        self.RateLimits = rateLimits

        return self.__longDataSchema.loads(content)


    def modbus(self, 
            deviceId: str, 
            fromTs: Union[int, datetime] = None,
            toTs: Union[int, datetime] = None,
            **kwargs):
        url = f"{self.endpoint}/modbus/{deviceId}"
        maxQueryPeriod = timedelta(days=7)

        fromTs, toTs = NormaliseTimestamps(fromTs, toTs, maxQueryPeriod)

        data = []
        windows = CreateQueryWindows(fromTs, toTs, maxQueryPeriod)
        for period in windows:
            requestParams = {"fromTs": int(period[0].timestamp()), "toTs": int(period[1].timestamp())}
            content, rateLimits = getRequest(url, 
                self.__session, self.timeout, 
                retry=self.retry, params=requestParams,
                **kwargs)
            self.RateLimits = rateLimits

            data.extend(self.__modbusDataSchema.loads(content, many=True))

        return data




