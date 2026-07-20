import argparse
from pathlib import Path

from loader import load_meta_file
from cpp_generator import generate_cpp
from sql_generator import generate_sql


def process_file(path: Path, cpp_out: Path, sql_out: Path) -> None:
    """处理单个 .meta.json 文件：生成 C++ 与 SQL 输出。"""
    print(f"=== {path.name} ===")
    tables = load_meta_file(str(path))
    # for table in tables:
        # keys = ", ".join(f.name for f in table.fields if f.is_key)
        # print(f"表 {table.name} ({table.comment})，{len(table.fields)} 个字段，主键: {keys}")
    stem = path.name.removesuffix(".meta.json")
    for out_path in generate_cpp(tables, cpp_out, stem):
        print(f"    -> {out_path}")
    sql_path = generate_sql(tables, sql_out / f"{stem}.sql")
    print(f"    -> {sql_path}")


def collect_inputs(input_path: Path) -> list[Path]:
    """input 指向文件则只处理该文件；指向目录则单层遍历其下所有 .meta.json 文件。"""
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted(input_path.glob("*.meta.json"))
    raise SystemExit(f"--input 路径不存在: {input_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="从 .meta.json 表定义生成 C++ 实体/仓储代码与 MySQL DDL。"
    )
    parser.add_argument(
        "--input", required=True, type=Path,
        help="单个 .meta.json 文件，或包含 .meta.json 文件的目录（仅单层遍历）。",
    )
    parser.add_argument(
        "--cpp_output", required=True, type=Path,
        help="C++ 代码输出目录。",
    )
    parser.add_argument(
        "--sql_output", required=True, type=Path,
        help="SQL DDL 输出目录。",
    )
    args = parser.parse_args()

    for path in collect_inputs(args.input):
        process_file(path, args.cpp_output, args.sql_output)


if __name__ == "__main__":
    main()
