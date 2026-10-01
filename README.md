# Text to SQL with a Clarification Engine

A small learning project for turning a user's question into a safe, useful SQL query. We'll build it in steps and keep the boundaries between components visible.

## The workflow

```text
Question → Understand intent → Clarify missing details → Draft SQL
         → Check SQL safety → Execute read-only → Explain results
```

The clarification step matters because a fluent SQL query can still answer the wrong question. For example, “show me our best customers” could mean highest spend, most orders, or most recent activity. The system should ask before guessing.

## Learning roadmap

1. **Data and schema:** create a tiny SQLite database and inspect its tables and columns.
2. **Clarification state:** represent what we know, what is ambiguous, and what we still need to ask.
3. **SQL generation:** add a model adapter once we choose a provider; pass only the relevant schema and conversation context.
4. **Safety:** validate model output and execute with read-only database access and limits.
5. **Evaluation:** compare generated queries with expected behavior, including ambiguous and unsafe requests.

## Run the first slice

Requires Python 3.10 or newer; it uses only the standard library.

```powershell
python app.py
```

Try `Who is our best customer?`, then answer `spend` or `orders`. The demo creates a tiny local SQLite database on its first run. It currently understands only that example intent; it is a teaching scaffold, not a general natural-language parser.

## Current status

The local SQLite example and clarification workflow are in `app.py`. No model provider or API key has been selected yet. The deterministic rules are intentional: they let us learn and inspect each stage before introducing model behavior.

## Concepts we'll use

- **Schema grounding:** give the model the actual table and column names, rather than asking it to invent them.
- **Clarification:** ask a focused question when required information is missing or has multiple plausible meanings.
- **Separation of concerns:** keep conversation handling, model calls, SQL checks, and database access in separate modules. This makes each part easier to understand and replace.
- **Read-only execution:** generated SQL is untrusted input. The database layer must enforce read-only behavior independently of what the model was told.

## Next step

We'll replace the hand-written intent rules with a model interface, give it the inspected schema, and have it return structured output such as either `clarification_needed` or `sql`. The SQL safety boundary will remain separate from the model.
