# Text2SQL

A learning project that turns natural-language questions about a SQLite database into SQL. It uses Gemini to choose whether to answer a database-schema question, ask for clarification, or query records.

## How it works

```text
User question
    ↓
Gemini receives the question and inspected database schema
    ↓
Choose an action: schema lookup, clarification, or SQL query
    ↓
For SQL: execute against SQLite in read-only mode
    ↓
If SQLite rejects the query: ask Gemini for one correction and try once
```

The app inspects the database schema at startup. It does not hard-code the soccer database's table or column names into the schema lookup behavior.

## Requirements

- Python
- A Gemini API key
- The SQLite database at `data/database.sqlite`

Install the Python packages in the project's virtual environment:

```powershell
python -m pip install google-genai python-dotenv
```

Create a `.env` file in the project folder and add your key:

```text
GEMINI_API_KEY=your_api_key_here
```

Keep `.env` and the database file out of Git. Do not put your API key in source code or commit it.

## Run the app

From the project folder, activate your virtual environment if needed, then run:

```powershell
python app.py
```

Type a question at `You:`. Enter `exit` or `quit` to stop. Enter `/reset` to clear the current clarification and Gemini conversation context.

## Current capabilities

- Lists the database's user-defined tables and describes tables using inspected columns and declared foreign keys.
- Asks a follow-up question when Gemini considers a request ambiguous, then combines the answer with the original request.
- Requests structured JSON from Gemini so the app can handle schema lookups, clarifications, and SQL generation as distinct actions.
- Opens SQLite in read-only mode before running generated SQL.
- Makes one repair attempt when SQLite raises an error for generated SQL.

## Current limitations

This is a learning project, not a production-ready database agent. Read-only connection mode prevents database writes, but the app does not yet have a separate SQL parser, query timeout, or result-size limit. The repair attempt handles SQLite query errors; a Gemini API error during that repair call is not yet handled gracefully. Query results are printed as raw Python rows, and the app does not verify that a successful query answered the user's intent correctly.

The soccer database includes match, player, team, league, and attribute data. Some event details, such as goals, are stored as XML inside database columns, so they may need special parsing before natural-language questions about those details can be answered accurately.

## Project files

- `app.py` — conversation loop, Gemini actions, clarification state, SQL execution, and one-time repair attempt.
- `inspect_database.py` — reads SQLite tables, columns, and declared foreign-key relationships.
- `data/database.sqlite` — local database used by the app; keep this file out of Git.
