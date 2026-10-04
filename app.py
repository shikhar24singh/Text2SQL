from dotenv import load_dotenv
from google import genai
from inspect_database import get_schema
from pathlib import Path
import sqlite3
import json

database_path = Path(__file__).parent/"data"/"database.sqlite"
db_schema, database_tables = get_schema(database_path)

load_dotenv()
client = genai.Client()
model = "gemini-3.7-flash"

def run_agent_turn(user_message, previous_interaction_id):
    prompt = f"""
Choose the best action for the user's request.

Use schema_lookup for questions about the database structure. Choose count_tables, list_tables, or describe_table as the schema_operation. For describe_table, set table_name to a table from the supplied schema.

Use run_sql for questions that require querying database records. Put one read-only SQLite statement in sql. Use only tables and columns from the supplied schema.

Use clarify when the request is ambiguous or missing information needed to write a correct query. Ask one concise question in clarification_question. Do not provide SQL yet.

When the user answers a clarification question from earlier in this conversation, use that answer together with the earlier request.

Set schema_operation to none and all unused text fields to empty strings when they do not apply.

Database schema:
{db_schema}

User request:
{user_message}
"""
    interaction = client.interactions.create(
        model = model,
        input = prompt,
        previous_interaction_id = previous_interaction_id,
        response_format = {
            "type": "text",
            "mime_type": "application/json",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["schema_lookup", "run_sql", "clarify"]
                    },
                    "schema_operation": {
                        "type": "string",
                        "enum": ["count_tables", "list_tables", "describe_table", "none"]
                    },
                    "table_name": {"type": "string"},
                    "sql": {"type": "string"},
                    "clarification_question": {"type": "string"}
                },
                "required": [
                    "action",
                    "schema_operation",
                    "table_name",
                    "sql",
                    "clarification_question"
                ],
                "additionalProperties": False
            }
        }
    )
    decision = json.loads(interaction.output_text)
    return decision, interaction.id

def answer_schema_lookup(decision):
    operation = decision["schema_operation"]

    if operation == "count_tables":
        return f"There are {len(database_tables)} user-defined tables."

    if operation == "list_tables":
        return "User-defined tables: " + ", ".join(database_tables)

    if operation == "describe_table":
        requested_name = decision["table_name"].casefold()
        table_name = next(
            (name for name in database_tables if name.casefold() == requested_name),
            None
        )
        if table_name is None:
            return "I couldn't match that table name to the database schema."

        details = database_tables[table_name]
        columns = ", ".join(details["columns"])
        relationships = ", ".join(details["relationships"]) or "no declared foreign keys"
        return f"Table: {table_name}\nColumns: {columns}\nRelationships: {relationships}"

    return "I couldn't determine which schema information to look up."

def execute_sql(sql):
    database_uri = f"file:{database_path.as_posix()}?mode=ro"
    connection = sqlite3.connect(database_uri, uri = True)
    try:
        cursor = connection.execute(sql)
        rows = cursor.fetchall()
        return rows
    finally:
        connection.close()

def main():
    print("Ask a question about the database\n")
    previous_id = None

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        decision, previous_id = run_agent_turn(user_input, previous_id)

        if decision["action"] == "schema_lookup":
            print(f"\nAssistant: {answer_schema_lookup(decision)}\n")
        elif decision["action"] == "clarify":
            print(f"\nAssistant: {decision['clarification_question']}\n")
        elif decision["action"] == "run_sql":
            sql = decision["sql"].strip()
            if not sql or "```" in sql:
                print("\nAssistant: Gemini did not return clean SQL. Please try again.\n")
                continue
            print(f"\nSQL: {sql}")
            result = execute_sql(sql)
            print(f"\nAssistant: {result}\n")
        else:
            print("\nAssistant: I couldn't decide how to handle that request. Please rephrase it.\n")

if __name__ == "__main__":
    main()
