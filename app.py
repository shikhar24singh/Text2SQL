from dotenv import load_dotenv
from google import genai
from google.genai import errors
from inspect_database import get_schema
from pathlib import Path
import sqlite3
import json

database_path = Path(__file__).parent/"data"/"database.sqlite"
db_schema, database_tables = get_schema(database_path)

load_dotenv()
client = genai.Client()
model = "gemini-3.1-flash-lite"

def run_agent_turn(user_message, previous_interaction_id):
    prompt = f"""
Choose the best action for the user's request.

Use schema_lookup for questions about the database structure. Choose count_tables, list_tables, or describe_table as the schema_operation. For describe_table, set table_name to a table from the supplied schema.

Use run_sql for questions that require querying database records. Put one read-only SQLite statement in sql. Use only tables and columns from the supplied schema.

If the user request includes a failed SQL statement and a SQLite error, use the schema and original request to correct the SQL. Return the action run_sql with the corrected statement. Do not ask the user to fix the SQL.

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
    pending_request = None
    previous_id = None

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        if user_input.lower() == "/reset":
            pending_request = None
            previous_id = None
            print("\nAssistant: Conversation reset.\n")
            continue

        if pending_request is not None:
            message_for_gemini = (
                f"Original request: {pending_request}\n"
                f"Clarification answer: {user_input}"
            )
        else:
            message_for_gemini = user_input

        try:
            decision, previous_id = run_agent_turn(message_for_gemini, previous_id)

        except errors.APIError as error:
            print(
                f"\nAssistant: Gemini couldn't process that request.\n"
                f"(error{error.code}). Rephrase it or use /reset.\n"
            )
            continue

        if decision["action"] == "schema_lookup":
            print(f"\nAssistant: {answer_schema_lookup(decision)}\n")
            pending_request = None
        elif decision["action"] == "clarify":
            if pending_request is None:
                pending_request = user_input
            print(f"\nAssistant: {decision['clarification_question']}\n")
        elif decision["action"] == "run_sql":
            sql = decision["sql"].strip()
            if not sql or "```" in sql:
                print("\nAssistant: Gemini did not return clean SQL. Please try again.\n")
                continue
            print(f"\nSQL: {sql}")
            try:
                result = execute_sql(sql)
            except sqlite3.Error as error:
                repair_request = (
                    f"Original request: {message_for_gemini}\n"
                    f"Failed SQL: {sql}\n"
                    f"SQLite error: {error}"
                )

                repair_decision, previous_id = run_agent_turn(
                    repair_request,
                    previous_id
                )

                if repair_decision["action"] != "run_sql":
                    print("\nAssistant: I couldn't repair that query. Please rephrase your request.\n")
                    continue

                repaired_sql = repair_decision["sql"].strip()
                if not repaired_sql or "```" in repaired_sql:
                    print("\nAssistant: Gemini didn't return clean SQL for the repair.\n")
                    continue

                print(f"\nRepaired SQL: {repaired_sql}")

                try:
                    repaired_result = execute_sql(repaired_sql)
                except sqlite3.Error as repair_error:
                    print(f"\nAssistant: The repaired query also failed: {repair_error}\n")
                    continue

                print(f"\nAssistant: {repaired_result}\n")
                pending_request = None
                continue
            print(f"\nAssistant: {result}\n")
            pending_request = None
        else:
            print("\nAssistant: I couldn't decide how to handle that request. Please rephrase it.\n")

if __name__ == "__main__":
    main()
