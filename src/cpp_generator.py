import platform
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from field import FieldType
from table import MysqlTable
from version import VERSION

# 模板目录：项目根目录下的 templates/
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

# FieldType 到 C++ 成员类型的映射。
CPP_TYPE_MAP = {
    FieldType.INT: "int32_t",
    FieldType.UINT: "uint32_t",
    FieldType.LONG: "int64_t",
    FieldType.ULONG: "uint64_t",
    FieldType.STRING: "std::string",
    FieldType.JSON: "nlohmann::json",
}

# mysqlx::Row 读取时使用的 C++ 类型映射。
# json 无条目：模板中通过 is_json 特殊处理（get<std::string> + nlohmann::json::parse）。
ROW_GET_TYPE_MAP = {
    FieldType.INT: "int32_t",
    FieldType.UINT: "uint32_t",
    FieldType.LONG: "int64_t",
    FieldType.ULONG: "uint64_t",
    FieldType.STRING: "std::string",
}

# C++ 成员默认值映射；字符串和 json 使用默认构造。
CPP_DEFAULT_VALUE_MAP = {
    FieldType.INT: " = 0",
    FieldType.UINT: " = 0",
    FieldType.LONG: " = 0",
    FieldType.ULONG: " = 0",
    FieldType.STRING: "",
    FieldType.JSON: "",
}


def make_env() -> Environment:
    """创建渲染 templates/ 的 Jinja2 环境。"""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def pascal_case(name: str) -> str:
    """snake_case 转 PascalCase，如 offline_entry -> OfflineEntry。"""
    return "".join(part.capitalize() for part in name.split("_"))


def build_cpp_context(table: MysqlTable, group_name: str) -> dict:
    """由 MysqlTable 构建模板渲染上下文。group_name 为 meta 文件的无后缀名，即输出子目录名。"""
    fields = []
    for f in table.fields:
        is_string = f.type == FieldType.STRING
        fields.append({
            "name": f.name,
            "pascal_name": pascal_case(f.name),
            "cpp_type": CPP_TYPE_MAP[f.type],
            "param_type": "const std::string&" if is_string else CPP_TYPE_MAP[f.type],
            "row_get_type": ROW_GET_TYPE_MAP.get(f.type),
            "default_value": CPP_DEFAULT_VALUE_MAP[f.type],
            "is_key": f.is_key,
            "is_string": is_string,
            "is_json": f.type == FieldType.JSON,
            "comment": f.comment,
        })
    # 主键声明顺序即索引层级，按前缀生成 queryBy / removeBy 方法：
    # 1 个主键 -> <K1>；
    # 2 个主键 -> <K1> 和 <K1>And<K2>；
    # >=3 个主键 -> 只保留 <K1>，其余层级鼓励使用字符串 cond。
    key_fields = [f for f in fields if f["is_key"]]
    if len(key_fields) == 2:
        prefixes = [key_fields[:1], key_fields[:2]]
    elif key_fields:
        prefixes = [key_fields[:1]]
    else:
        prefixes = []
    key_queries = [
        {
            "method_suffix": "And".join(f["pascal_name"] for f in prefix),
            "params": prefix,
        }
        for prefix in prefixes
    ]

    return {
        "table_name": table.name,
        "class_name": pascal_case(table.name),
        "group_name": group_name,
        "fields": fields,
        "key_queries": key_queries,
        "python_version": platform.python_version(),
        "script_version": VERSION,
    }


def generate_cpp(tables: list[MysqlTable], out_dir: Path, group_name: str) -> list[Path]:
    """按模板生成每张表的 Entity 头文件与 Repository 头/实现文件，返回生成的文件列表。

    同一个 meta.json 里的表输出到同一目录：gen/{entity,repository}/<group_name>/。
    """
    env = make_env()

    generated: list[Path] = []
    for table in tables:
        ctx = build_cpp_context(table, group_name)
        cls = ctx["class_name"]
        outputs = [
            ("entity.h.j2", out_dir / "entity" / group_name / f"Entity_{cls}.h"),
            ("repository.h.j2", out_dir / "repository" / group_name / f"Repository_{cls}.h"),
            ("repository.cpp.j2", out_dir / "repository" / group_name / f"Repository_{cls}.cpp"),
        ]
        for template_name, out_path in outputs:
            text = env.get_template(template_name).render(**ctx)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            generated.append(out_path)
    return generated
