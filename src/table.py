from dataclasses import dataclass
from field import MysqlField

@dataclass
class MysqlTable:
    name: str
    comment: str
    fields: list[MysqlField]