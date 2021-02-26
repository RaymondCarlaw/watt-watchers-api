from dataclasses import dataclass, field, InitVar, fields
import marshmallow
import inspect
from marshmallow_dataclass import class_schema
from typing import Optional, List, Dict, Union, Tuple, Any
from .enums import Energy
from .utilities import SignalQuality
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
    
    @marshmallow.pre_load
    def pre_load(self, data, **kwargs):
        if 'client' in self.context:
            data['_client'] = self.context['client']

        if 'unit' not in self.context:
            return data

        data['unit'] = str(self.context['unit'])
        keys = [*data.keys()]
        if self.context['unit'] == Energy.Killowatts:
            for k in keys:
                if k.endswith('Kw'):
                    newK = 'e' + k[1:len(k) - 2]
                    data[newK] = data[k]
        elif self.context['unit'] == Energy.KillowattHours:
            for k in keys:
                if k.endswith('Kwh'):
                    newK = 'e' + k[1:len(k) - 3]
                    data[newK] = data[k]
        
        return data

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

        return SignalQuality(commsType, self.SignalQualityDbm)

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
    
    def __post_init__(self):
        self._dirtyFields = {}

    def __setattr__(self, name, value):
        if '_' not in name and name != 'Id' and hasattr(self, '_dirtyFields'):
            object.__getattribute__(self, '_dirtyFields')[name] = value
            
        object.__setattr__(self, name, value)

    class Meta:
        unknown = marshmallow.EXCLUDE

ChannelAttributeSchema = class_schema(ChannelAttribute, base_schema=BaseSchema)


@dataclass
class ChannelGrouping:
    Included: List[str] = field(default_factory=list)

    class Meta:
        unknown = marshmallow.EXCLUDE

ChannelGroupingSchema = class_schema(ChannelGrouping, base_schema=BaseSchema)


@dataclass
class PhaseConfiguration:
    Count: int = None
    Grouping: List[ChannelGrouping] = field(default_factory=list)
    
    def __post_init__(self):
        self._dirtyFields = {}

    def __setattr__(self, name, value):
        if '_' not in name and name != 'Id' and hasattr(self, '_dirtyFields'):
            object.__getattribute__(self, '_dirtyFields')[name] = value
            
        object.__setattr__(self, name, value)

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

    def __post_init__(self):
        self._dirtyFields = {}

    def __setattr__(self, name, value):
        if '_' not in name and name != 'Id' and hasattr(self, '_dirtyFields'):
            object.__getattribute__(self, '_dirtyFields')[name] = value
            
        object.__setattr__(self, name, value)

    class Meta:
        unknown = marshmallow.EXCLUDE

SwitchAttributeSchema = class_schema(SwitchAttribute, base_schema=BaseSchema)


@dataclass
class ShortData:
    Timestamp: datetime = None
    Duration: int = None
    Frequency: float = None
    Unit: str = None
    GroupedBy: Optional[str] = None
    Real: List[float] = field(metadata=dict(data_key='eReal'), default=None)
    Reactive: List[float] = field(metadata=dict(data_key='eReactive'), default=None)
    VoltageRMS: List[float] = field(metadata=dict(data_key='vRMS'), default=None)
    CurrentRMS: List[float] = field(metadata=dict(data_key='iRMS'), default=None)

    class Meta:
        unknown = marshmallow.EXCLUDE

ShortDataSchema = class_schema(ShortData, base_schema=BaseSchema)


@dataclass
class LongData:
    Timestamp: datetime = None
    Duration: int = None
    Unit: str = None
    Real: List[int] = field(metadata=dict(data_key='eReal'), default=None)
    RealNegative: List[float] = field(metadata=dict(data_key='eRealNegative'), default=None)
    RealPositive: List[float] = field(metadata=dict(data_key='eRealPositive'), default=None)
    Reactive: List[float] = field(metadata=dict(data_key='eReactive'), default=None)
    ReactiveNegative: List[float] = field(metadata=dict(data_key='eReactiveNegative'), default=None)
    ReactivePositive: List[float] = field(metadata=dict(data_key='eReactivePositive'), default=None)
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

    _client: Optional[Any] = None

    _dirtyFields = {}
    _isPartial = False

    def __post_init__(self, *args, **kwargs):
        self._isPartial = self.Model == None

    def update(self):
        if self.Phases._dirtyFields != {}:
            self._dirtyFields['phases'] = PhaseConfigurationSchema().dump(self.Phases)
        dirtyChannels = []
        for c in self.Channels:
            if c._dirtyFields != {}:
                dirtyChannels.append(c)
        
        dirtySwitches = []
        for s in self.Switches:
            if s._dirtyFields != {}:
                dirtySwitches.append(s)
        
        if dirtyChannels:
            schema = ChannelAttributeSchema()
            self._dirtyFields['channels'] = []
            for c in dirtyChannels:
                dc = schema.dump(c)
                del dc['categoryLabel']; del dc['pending']
                self._dirtyFields['channels'].append(dc)

        if dirtySwitches:
            schema = SwitchAttributeSchema()
            self._dirtyFields['switches'] = [schema.dump(s) for s in dirtySwitches]

        self._client.updateDevice(self.Id, self._dirtyFields)
        if 'phases' in self._dirtyFields:
            self.Phases._dirtyFields = {}
        
        for c in dirtyChannels:
            c._dirtyFields = {}
        
        for s in dirtySwitches:
            c._dirtyFields = {}

        self._dirtyFields = {}

    def __setattr__(self, name, value):
        if '_' not in name and name != 'Id':
            object.__getattribute__(self, '_dirtyFields')[name] = value
            
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):

        if name != 'Id' and '_' not in name and object.__getattribute__(self, '_isPartial'):
            device = self._client.device(self.Id)
            members = fields(Device)
            for dname in [n.name for n in members if '_' not in n.name]:
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