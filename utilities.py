from .enums import SignalQuality

QUALITY_BAND = (SignalQuality.Excellent, SignalQuality.Good, SignalQuality.Low, SignalQuality.Poor)
THREE_G_SIGNAL_BAND = (-89, -95, -101, -110)
FOUR_G_SIGNAL_BAND = (-65, -75, -95, -96)
WIFI_SIGNAL_BAND = (-40, -55, -70, -2000) # anything lower than 70 is poor

def signalQuality(CommsType: str, signalQualityDbm: int) -> str:
    if signalQualityDbm == 0:
        return SignalQuality.Unknown.value
    
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

    return SignalQuality.NoSignal.value

    