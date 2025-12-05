from uprotobuf import *


@registerMessage
class TemperaturemessageMessage(Message):
    _proto_fields=[
        dict(name='id', type=WireType.Length, subType=LengthSubType.String, fieldType=FieldType.Optional, id=1),
        dict(name='temp', type=WireType.Bit32, subType=FixedSubType.Float, fieldType=FieldType.Optional, id=2),
        dict(name='time', type=WireType.Varint, subType=VarintSubType.UInt32, fieldType=FieldType.Optional, id=3),
    ]
