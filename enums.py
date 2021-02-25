from enum import Enum, unique

class BaseEnum(Enum):
    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self.value) == str(other)

    def __hash__(self):
        return object.__hash__(str(self.value))

@unique
class Groups(BaseEnum):
    Phases = 'phases'

@unique
class Energy(BaseEnum):
    Killowatts = 'kW'
    KillowattHours = 'kWh'
    PowerFactor = '+pf'
    Joules = 'J'

@unique
class SignalQuality(BaseEnum):
    Unknown = 'Unknown'
    Excellent = 'Excellent'
    Good = 'Good'
    Low = 'Low'
    Poor = 'Poor'
    NoSignal = 'No Signal'

@unique
class Granularity(BaseEnum):
    FiveMinute = '5m'
    FifteenMinute = '15m'
    HalfHourly = '30m'
    Hourly = 'hour'
    Daily = 'day'
    Weekly = 'week'
    Monthly = 'month'
