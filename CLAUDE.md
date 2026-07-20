# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`entity_gen` is a Python code generator. It reads MySQL table definitions from `def/*.meta.json` and, via Jinja2 templates, generates C++ entity/repository code (mysqlx / MySQL X DevAPI with `nlohmann::json`, asio-based async wrappers) into `gen/` and MySQL DDL into `sql/`.

## Environment & Commands

The Python 3.12 virtual environment lives **directly in the project root** (`Scripts/`, `Lib/`, `pyvenv.cfg` are venv files — do not treat `Lib/site-packages` as project code or edit anything there). Only third-party dependency: `jinja2`.

```powershell
# Load def/*.meta.json and (re)generate all C++ files into gen/
Scripts\python.exe src\main.py
```

There are no tests or linters. Imports in `src/` are flat (e.g. `from field import ...`), so run with `src` on the path.

## Architecture

Pipeline: `def/<name>.meta.json` → `loader.load_meta_file` → `list[MysqlTable]` → `generator.generate` → `gen/entity/<name>/Entity_<Class>.h`, `gen/repository/<name>/Repository_<Class>.{h,cpp}`, and → `sql_generator.generate_sql` → `sql/<name>.sql`. Outputs are grouped by the meta file's stem (`<name>`), not by table — all tables in one meta file share one entity dir, one repository dir, and one DDL file. Everything under `gen/` and `sql/` is generated output — change templates/generator, not the generated files.

- `src/field.py` — `FieldType` enum, `MysqlField` dataclass, and `JSON_TYPE_MAP` (meta type string → `FieldType`).
- `src/table.py` — `MysqlTable` dataclass.
- `src/loader.py` — parses a meta.json file into `list[MysqlTable]` (`private_key` → `is_key`, defaults: `nullable=True`, `private_key=False`).
- `src/generator.py` — `FieldType` → C++ type/getter/default maps, `make_env()` (shared Jinja2 environment), and `build_context` (the template-context contract: `table_name`, `class_name`, `group_name`, per-field `name`/`pascal_name`/`cpp_type`/`param_type`/`row_get_type`/`default_value`/`is_key`/`is_string`/`is_json`/`comment`); renders `templates/`.
- `src/sql_generator.py` — `FieldType` → MySQL column type map (`SQL_TYPE_MAP`) and `generate_sql` (renders `tables.sql.j2`; non-key integer columns get `DEFAULT 0`, `nullable=False` → `NOT NULL`).
- `templates/*.j2` — Jinja2 templates (rendered with `trim_blocks`, `lstrip_blocks`, `keep_trailing_newline`). Conventions: `json` fields are read via `get<std::string>` + `nlohmann::json::parse` and written via `.dump()`; primary-key declaration order is the index hierarchy, and key queries are generated per prefix by key count (1 key → `queryBy<K1>`; exactly 2 → `queryBy<K1>` and `queryBy<K1>And<K2>`; ≥3 → only `queryBy<K1>`, deeper levels use the string-`cond` overload); `removeBy` methods follow the same prefix rule (sync only, no async variants); multi-column keys are AND-ed in `update`'s `where`.
- `def/*.meta.json` — table definition inputs. Each file is a JSON array of tables with `table_name`, `comment`, and `columns`; columns have `column_name`, `type` (`uint64`/`int64`/`uint32`/`int32`/`string`/`json`), `nullable`, optional `private_key` (marks primary key columns), and `comment`. Comments in the meta files and generated code are in Chinese.
