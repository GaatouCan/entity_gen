from dataclasses import dataclass
from enum import Enum

class FieldType(Enum):
    INT     = 1
    UINT    = 2
    LONG    = 3
    ULONG   = 4
    STRING  = 5
    JSON    = 6

# JSON 类型到 FieldType 枚举的映射。
JSON_TYPE_MAP = {
    "int32":    FieldType.INT,
    "uint32":   FieldType.UINT,
    "int64":    FieldType.LONG,
    "uint64":   FieldType.ULONG,
    "string":   FieldType.STRING,
    "json":     FieldType.JSON,
}

@dataclass
class MysqlField:
    name: str
    type: FieldType
    is_key: bool
    nullable: bool
    comment: str
