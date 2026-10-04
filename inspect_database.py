import sqlite3
from pathlib import Path

database_path = Path(__file__).parent/"data"/"database.sqlite"

def get_schema(database_path: Path) -> tuple[str, dict[str, dict[str, list[str]]]]:
    schema_lines = []
    tables = {}

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()

        for (table_name, ) in rows:
            column_name = connection.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall()
            column_names = [column[1] for column in column_name]
            column_text = ', '.join(column_names)
            foreign_key = connection.execute(
                f"PRAGMA foreign_key_list('{table_name}')"
            ).fetchall()
            relationships = [
                f"{fk[3]} -> {fk[2]}.{fk[4]}"
                for fk in foreign_key
            ]
            relationships_text = ", ".join(relationships) if relationships else "no declared foreign keys"
            tables[table_name] = {
                "columns": column_names,
                "relationships": relationships,
            }
            schema_lines.append(
                f"Table: {table_name}\n"
                f"Columns: {column_text}\n"
                f"Relationships: {relationships_text}"
                )

    schema_description = '\n'.join(schema_lines)
    return schema_description, tables

if __name__ == "__main__":
    schema_description, tables = get_schema(database_path)
    print(schema_description)
    print(f"\nUser-defined tables: {len(tables)}")
