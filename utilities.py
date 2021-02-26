from .enums import SignalQuality as SignalQualityEnum
from datetime import datetime, timedelta, timezone as dtTimezone
from typing import Union

QUALITY_BAND = (SignalQualityEnum.Excellent, SignalQualityEnum.Good, \
    SignalQualityEnum.Low, SignalQualityEnum.Poor)
THREE_G_SIGNAL_BAND = (-89, -95, -101, -110)
FOUR_G_SIGNAL_BAND = (-65, -75, -95, -96)
WIFI_SIGNAL_BAND = (-40, -55, -70, -2000) # anything lower than 70 is poor

def SignalQuality(CommsType: str, signalQualityDbm: int) -> str:
    if signalQualityDbm == 0:
        return str(SignalQualityEnum.Unknown)
    
    if CommsType == '3G':
        band = THREE_G_SIGNAL_BAND
    elif CommsType == '4G':
        band = FOUR_G_SIGNAL_BAND
    elif CommsType == 'wifi':
        band = WIFI_SIGNAL_BAND
    else:
        raise ValueError(CommsType)

    for idx in range(len(QUALITY_BAND)):
        if signalQualityDbm >= band[idx]:
            return QUALITY_BAND[idx].value

    return str(SignalQualityEnum.NoSignal)

def NormaliseTimestamps(fromTs: Union[int, datetime], toTs: Union[int, datetime], extensionPeriod: timedelta):
    if fromTs is None and toTs is None:
        toTs = datetime.now(dtTimezone.utc)
        fromTs = toTs - extensionPeriod

    if toTs is None:
        toTs = datetime.now(dtTimezone.utc)
    else:
        if isinstance(toTs, int):
            toTs = datetime.fromtimestamp(toTs)
        elif not isinstance(toTs, datetime):
            raise TypeError(toTs)

    if fromTs is None:
        fromTs = toTs - extensionPeriod
    else:
        if isinstance(fromTs, int):
            fromTs = datetime.fromtimestamp(fromTs)
        elif not isinstance(fromTs, datetime):
            raise TypeError(fromTs)

    return (fromTs, toTs)

def CreateQueryWindows(fromTs: datetime, toTs: datetime, maxQueryPeriod):
    windows = []
    if (toTs - fromTs) > maxQueryPeriod:
        currentTs = fromTs
        while currentTs + maxQueryPeriod < toTs:
            windows.append((currentTs, currentTs + maxQueryPeriod))
            currentTs += maxQueryPeriod
        
        if currentTs < toTs:
            windows.append((currentTs, toTs))
    else:
        windows = [(fromTs, toTs)]

    return windows

    