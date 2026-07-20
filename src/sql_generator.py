from pathlib import Path

from field import FieldType
from cpp_generator import make_env
from table import MysqlTable

# FieldType 到 MySQL 字段类型的映射。
SQL_TYPE_MAP = {
    FieldType.INT: "INT",
    FieldType.UINT: "INT UNSIGNED",
    FieldType.LONG: "BIGINT",
    FieldType.ULONG: "BIGINT UNSIGNED",
    FieldType.STRING: "VARCHAR(255)",
    FieldType.JSON: "JSON",
}

# 整型字段类型：非主键的整型列生成 DEFAULT 0。
INT_FIELD_TYPES = {FieldType.INT, FieldType.UINT, FieldType.LONG, FieldType.ULONG}


def build_sql_context(tables: list[MysqlTable]) -> dict:
    """由 MysqlTable 列表构建 SQL 模板渲染上下文。"""
    table_contexts = []
    for table in tables:
        fields = []
        for f in table.fields:
            fields.append({
                "name": f.name,
                "sql_type": SQL_TYPE_MAP[f.type],
                "not_null": not f.nullable,
                "default_value": " DEFAULT 0" if f.type in INT_FIELD_TYPES and not f.is_key else "",
                "is_key": f.is_key,
                "comment": f.comment,
            })
        table_contexts.append({
            "table_name": table.name,
            "comment": table.comment,
            "fields": fields,
        })
    return {"tables": table_contexts}


def generate_sql(tables: list[MysqlTable], out_path: Path) -> Path:
    """将一组表渲染为一个建表 SQL 文件（对应一个 meta.json）。"""
    env = make_env()
    text = env.get_template("tables.sql.j2").render(**build_sql_context(tables))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path
