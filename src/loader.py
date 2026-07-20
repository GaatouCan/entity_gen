import json

from field import MysqlField, JSON_TYPE_MAP
from table import MysqlTable


def load_meta_file(path: str) -> list[MysqlTable]:
    """读取一个 meta.json 文件，返回其中定义的所有表。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables: list[MysqlTable] = []
    for table_def in data:
        fields: list[MysqlField] = []
        for col in table_def["columns"]:
            type_name = col["type"]
            if type_name not in JSON_TYPE_MAP:
                raise ValueError(
                    f"表 {table_def['table_name']} 的字段 {col['column_name']} "
                    f"使用了未知类型: {type_name}"
                )
            fields.append(MysqlField(
                name=col["column_name"],
                type=JSON_TYPE_MAP[type_name],
                is_key=col.get("private_key", False),
                nullable=col.get("nullable", True),
                comment=col.get("comment", ""),
            ))
        tables.append(MysqlTable(
            name=table_def["table_name"],
            comment=table_def.get("comment", ""),
            fields=fields,
        ))
    return tables
