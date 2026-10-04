# Text to SQL with a Clarification Engine

A learning project for turning natural-language questions into safe, useful SQL. The current work focuses on inspecting the database schema; clarification, SQL generation, and safe query execution are planned steps.

## Current project state

- `inspect_database.py` reads the SQLite database at `data/database.sqlite`.
- It lists each table, its columns, and declared foreign-key relationships.
- The database contains football data, including matches, teams, players, leagues, and player/team attributes.
- The project does not yet include a text-to-SQL app or a model provider.

The database file is local project data and is excluded from Git. Make sure `data/database.sqlite` exists before running the script.

## Run the schema inspector

Requires Python 3.10 or newer and uses only the Python standard library.

```powershell
python inspect_database.py
```

The script prints a schema summary to the terminal. The database path is defined relative to the script, so you can run the command from the project directory.

## Planned workflow

```text
Question → Understand intent → Clarify missing details → Draft SQL
         → Check SQL safety → Execute read-only → Explain results
```

A fluent query can still answer the wrong question. For example, “Which team is best?” could refer to wins, goals, or a particular season. The system should ask for the missing criteria rather than silently guessing.

## Learning roadmap

1. **Schema grounding:** improve schema inspection and identify useful tables and relationships.
2. **Clarification state:** represent what is known, what is ambiguous, and what must be asked.
3. **SQL generation:** add a model adapter after choosing a provider; provide only relevant schema and conversation context.
4. **Safety:** validate generated SQL, then execute it with read-only database access and result limits.
5. **Evaluation:** compare generated queries with expected behavior, including ambiguous and unsafe requests.

## Concepts

- **Schema grounding:** use real table and column names rather than letting a model invent them.
- **Clarification:** ask a focused question when important details are missing or ambiguous.
- **Separation of concerns:** keep conversation handling, model calls, SQL checks, and database access in distinct components.
- **Read-only execution:** treat generated SQL as untrusted input and enforce read-only access in the database layer.
