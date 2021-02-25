from dataclasses import dataclass, field, InitVar
import marshmallow
from marshmallow_dataclass import class_schema
from typing import Optional, List, Dict, Union, Tuple
from .enums import SignalQuality
from .utilities import signalQuality
from datetime import datetime

class TimeStamp(marshmallow.fields.DateTime):
    """
    Class extends marshmallow standard DateTime with "timestamp" format.
    """

    SERIALIZATION_FUNCS = \
        marshmallow.fields.DateTime.SERIALIZATION_FUNCS.copy()
    DESERIALIZATION_FUNCS = \
        marshmallow.fields.DateTime.DESERIALIZATION_FUNCS.copy()

    SERIALIZATION_FUNCS['timestamp'] = lambda x: int(x.timestamp()) * 1000
    DESERIALIZATION_FUNCS['timestamp'] = datetime.fromtimestamp

    DEFAULT_FORMAT = "timestamp"

# api models
class BaseSchema(marshmallow.Schema):
    TYPE_MAPPING = {datetime: TimeStamp}
    
    def on_bind_field(self, field_name, field_obj):
        name = field_obj.data_key or field_name
        field_obj.data_key = name[0].lower() + name[1:]


@dataclass
class RateLimits:
    TotalPerDay: int = field(metadata=dict(data_key='X-RateLimit-TpdLimit'), default=None)
    RemainingPerDay: int = field(metadata=dict(data_key='X-RateLimit-TpdRemaining'), default=None)
    TotalPerDayResetCounter: int = field(metadata=dict(data_key='X-RateLimit-TpdReset'), default=None)
    TotalPerSecond: int = field(metadata=dict(data_key='X-RateLimit-TpsLimit'), default=None)
    RemainingPerSecond: int = field(metadata=dict(data_key='X-RateLimit-TpsRemaining'), default=None)
    TotalPerSecondResetCounter: float = field(metadata=dict(data_key='X-RateLimit-TpsReset'), default=None)
    RetryAfter: Optional[int] = field(metadata=dict(data_key='Retry-After'), default=None)

    class Meta:
        unknown = marshmallow.EXCLUDE

RateLimitsSchema = class_schema(RateLimits)


@dataclass
class ChannelCategory:
    Id: int
    Label: str
    Description: str

    class Meta:
        unknown = marshmallow.EXCLUDE

ChannelCategorySchema = class_schema(ChannelCategory, base_schema=BaseSchema)


@dataclass
class DeviceModel:
    Code: str = None
    DisplayName: str = None
    ChannelsCount: int = None
    SwitchesCount: int = None
    Communications: str = None

    class Meta:
        unknown = marshmallow.EXCLUDE

DeviceModelSchema = class_schema(DeviceModel, base_schema=BaseSchema)


@dataclass
class DevicePending:
    ShortEnergyReportingInterval: int = None
    CtRating: int = None
    State: str = None


@dataclass
class DeviceComms:
    Type: str = None
    LastHeardAt: datetime = None
    SignalQualityDbm: int = None
    networkId: str = None
    APN: Optional[str] = field(metadata=dict(data_key='apn'), default=None)
    SimId: Optional[str] = None
    IMSI: Optional[str] = field(metadata=dict(data_key='imsi'), default=None)

    @property
    def SignalQuality(self) -> str:
        if self.Type == 'wifi':
            commsType = 'wifi'
        elif self.Type == 'cellular':
            commsType = '4G' # need to guess at this stage
        else:
            return None

        return signalQuality(commsType, self.SignalQualityDbm)

    class Meta:
        unknown = marshmallow.EXCLUDE

DeviceCommsSchema = class_schema(DeviceComms, base_schema=BaseSchema)


@dataclass
class ChannelAttribute:
    Id: str = None
    CtRating: int = None
    Label: str = None
    CategoryId: int = None
    CategoryLabel: str = None
    pending: DevicePending = field(default=DevicePending)
    
    class Meta:
        unknown = marshmallow.EXCLUDE

ChannelAttributeSchema = class_schema(ChannelAttribute, base_schema=BaseSchema)


@dataclass
class ChannelGrouping:
    Included: List[str] = field(default_factory=list)

ChannelGroupingSchema = class_schema(ChannelGrouping, base_schema=BaseSchema)


@dataclass
class PhaseConfiguration:
    Count: int = None
    Grouping: List[ChannelGrouping] = field(default_factory=list)

    class Meta:
        unknown = marshmallow.EXCLUDE

PhaseConfigurationSchema = class_schema(PhaseConfiguration, base_schema=BaseSchema)


@dataclass
class SwitchAttribute:
    Id: str = None
    State: str = None
    Label: str = None
    ContactorType: str = None
    ClosedStateLabel: str = None
    OpenStateLabel: str = None
    Pending: DevicePending = field(default=DevicePending)

    class Meta:
        unknown = marshmallow.EXCLUDE

SwitchAttributeSchema = class_schema(SwitchAttribute, base_schema=BaseSchema)


@dataclass
class ShortData:
    Timestamp: datetime = None
    Duration: int = None
    Frequency: float = None
    GroupedBy: Optional[str] = None
    EnergyReal: List[int] = field(metadata=dict(data_key='eReal'), default=None)
    EnergyReactive: List[int] = field(metadata=dict(data_key='eReactive'), default=None)
    VoltageRMS: List[float] = field(metadata=dict(data_key='vRMS'), default=None)
    CurrentRMS: List[float] = field(metadata=dict(data_key='iRMS'), default=None)

    class Meta:
        unknown = marshmallow.EXCLUDE

ShortDataSchema = class_schema(ShortData, base_schema=BaseSchema)


@dataclass
class LongData:
    Timestamp: datetime = None
    Duration: int = None
    EnergyReal: List[int] = field(metadata=dict(data_key='eReal'), default=None)
    EnergyRealNegative: List[int] = field(metadata=dict(data_key='eRealNegative'), default=None)
    EnergyRealPositive: List[int] = field(metadata=dict(data_key='eRealPositive'), default=None)
    EnergyReactive: List[int] = field(metadata=dict(data_key='eReactive'), default=None)
    EnergyReactiveNegative: List[int] = field(metadata=dict(data_key='eReactiveNegative'), default=None)
    EnergyReactivePositive: List[int] = field(metadata=dict(data_key='eReactivePositive'), default=None)
    VoltageRMSMin: List[float] = field(metadata=dict(data_key='vRMSMin'), default=None)
    VoltageRMSMax: List[float] = field(metadata=dict(data_key='vRMSMax'), default=None)
    CurrentRMSMin: List[float] = field(metadata=dict(data_key='iRMSMin'), default=None)
    CurrentRMSMax: List[float] = field(metadata=dict(data_key='iRMSMax'), default=None)

    class Meta:
        unknown = marshmallow.EXCLUDE

LongDataSchema = class_schema(LongData, base_schema=BaseSchema)


@dataclass
class ModbusData:
    _Ia: float = None
    _Ib: float = None
    _Ic: float = None
    _PFa: float = None
    _PFb: float = None
    _PFc: float = None
    _Uan: float = None
    _Ubn: float = None
    _Ucn: float = None
    kVAh: int = None
    kWh_Exp: int = None
    kWh_Imp: int = None
    kWh_Net: int = None
    kWh_Tot: int = None
    kvarh_Q1: int = None
    kvarh_Q2: int = None
    kvarh_Q3: int = None
    kvarh_Q4: int = None
    kvarh_Exp: int = None
    kvarh_Imp: int = None
    kvarh_Net: int = None
    kvarh_Tot: int = None
    Model: str = None
    Timestamp: datetime = None

    class Meta:
        unknown = marshmallow.EXCLUDE

ModbusDataSchema = class_schema(ModbusData, base_schema=BaseSchema)


@dataclass
class Device:
    Id: str
    Label: str = None
    Timezone: str = None
    Model: str = None
    FirmwareVersion: str = None
    LatestStatus: int = None 
    ShortEnergyReportingInterval: int = None
    Pending: DevicePending = field(default=DevicePending)
    Comms: DeviceComms = field(default=DeviceComms)
    Channels: List[ChannelAttribute] = field(default_factory=list)
    Phases: PhaseConfiguration = field(default=PhaseConfiguration)
    Switches: List[SwitchAttribute] = field(default_factory=list)

    client: InitVar[object] = None

    _dirtyFields = {}
    _isPartial = False

    def __post_init__(self, client = None, *args, **kwargs):
        self.__client = client
        self._isPartial = self.Model == None

    def update(self):
        self.__client.updateDevice(self.Id, self.dirtyFields)

    def __setattr__(self, name, value):
        if '_' not in name and name != 'Id':
            object.__getattribute__(self, '_dirtyFields')[name] = value
            
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):

        if name != 'Id' and '_' not in name and object.__getattribute__(self, '_isPartial'):
            device = self.__client.device(self.Id)
            for dname in [n for n in dir(device) if '_' not in n]:
                setattr(self, dname, getattr(device, dname))
            self._isPartial = False
            self._dirtyFields = {}
        
        return object.__getattribute__(self, name)

    def __str__(self):
        return '<Device(Id:{device_id})>'.format(device_id=self.Id)

    def __repr__(self):
        return '<Device(Id:{device_id})>'.format(device_id=self.Id)

    class Meta:
        unknown = marshmallow.EXCLUDE

DeviceSchema = class_schema(Device, base_schema=BaseSchema)