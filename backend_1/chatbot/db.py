# ============================================================
# db.py
# ============================================================

import os

from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# DATABASE URL
# ============================================================

DB_URI = os.getenv(
    "LANGGRAPH_DB_URI",
    "postgresql://postgres:rudra@localhost:5432/postgres",
)


if not DB_URI:
    raise RuntimeError(
        "LANGGRAPH_DB_URI is not configured."
    )


# ============================================================
# DATABASE CONNECTION SETTINGS
# ============================================================

CONNECTION_TIMEOUT = 10


# ============================================================
# DISPLAY CONNECTION TARGET
# ============================================================

def get_safe_database_info(uri: str) -> str:

    try:

        # Remove password from displayed URI.
        if "@" in uri:

            return uri.split("@", 1)[1]

        return uri

    except Exception:

        return "hidden"


# ============================================================
# CONNECT TO POSTGRESQL (SHORT-TERM / CHECKPOINTER)
# ============================================================
#
# The checkpointer gets its own dedicated connection. This is
# the SHORT-TERM memory backend, scoped per thread_id.
# ============================================================

print()
print("=" * 60)
print("Connecting to PostgreSQL (checkpointer)...")
print("=" * 60)

print(
    "Database:",
    get_safe_database_info(DB_URI)
)


try:

    connection = psycopg.connect(
        DB_URI,
        autocommit=True,
        row_factory=dict_row,
        connect_timeout=CONNECTION_TIMEOUT,
    )

    print(
        "PostgreSQL TCP connection successful."
    )


except Exception as error:

    print()
    print("=" * 60)
    print("POSTGRESQL CONNECTION FAILED")
    print("=" * 60)

    print(
        "Error:",
        error
    )

    print()
    print(
        "Check that PostgreSQL is running and that:"
    )

    print(
        "  Host: localhost"
    )

    print(
        "  Port: 5432"
    )

    print(
        "  User: postgres"
    )

    print(
        "  Database: postgres"
    )

    print("=" * 60)

    raise RuntimeError(
        "Could not connect to PostgreSQL."
    ) from error


# ============================================================
# VERIFY DATABASE CONNECTION
# ============================================================

try:

    with connection.cursor() as cursor:

        cursor.execute(
            "SELECT 1;"
        )

        result = cursor.fetchone()


    if not result:

        raise RuntimeError(
            "PostgreSQL returned no result."
        )


    print(
        "PostgreSQL query test successful."
    )


except Exception as error:

    print(
        "PostgreSQL query test failed:"
    )

    print(
        error
    )


    try:

        connection.close()

    except Exception:

        pass


    raise RuntimeError(
        "PostgreSQL connection exists, "
        "but database query failed."
    ) from error


# ============================================================
# CREATE LANGGRAPH CHECKPOINTER
# ============================================================

print()
print(
    "Creating LangGraph PostgreSQL checkpointer..."
)


try:

    checkpointer = PostgresSaver(
        connection
    )

    print(
        "LangGraph checkpointer created."
    )


except Exception as error:

    print()
    print(
        "Failed to create LangGraph checkpointer:"
    )

    print(
        error
    )


    try:

        connection.close()

    except Exception:

        pass


    raise RuntimeError(
        "Could not create LangGraph PostgreSQL checkpointer."
    ) from error


# ============================================================
# CREATE / UPDATE LANGGRAPH TABLES (CHECKPOINTER)
# ============================================================

print()
print(
    "Setting up LangGraph checkpoint tables..."
)


try:

    checkpointer.setup()

    print(
        "LangGraph checkpoint tables are ready."
    )


except Exception as error:

    print()
    print("=" * 60)
    print("LANGGRAPH CHECKPOINT SETUP FAILED")
    print("=" * 60)

    print(
        "Error:",
        error
    )

    print("=" * 60)


    try:

        connection.close()

    except Exception:

        pass


    raise RuntimeError(
        "Could not initialize LangGraph checkpoint tables."
    ) from error


# ============================================================
# CONNECT TO POSTGRESQL (LONG-TERM / STORE)
# ============================================================
#
# The long-term store gets its OWN dedicated connection,
# separate from the checkpointer's. They are two different
# LangGraph components (checkpoint tables vs store tables) and
# giving each its own connection avoids them contending over
# the same connection/cursor at the same time.
#
# This is the LONG-TERM memory backend, scoped per user_id, and
# it now survives process restarts (unlike InMemoryStore).
# ============================================================

print()
print("=" * 60)
print("Connecting to PostgreSQL (long-term store)...")
print("=" * 60)

print(
    "Database:",
    get_safe_database_info(DB_URI)
)


try:

    store_connection = psycopg.connect(
        DB_URI,
        autocommit=True,
        row_factory=dict_row,
        connect_timeout=CONNECTION_TIMEOUT,
    )

    print(
        "PostgreSQL TCP connection successful."
    )


except Exception as error:

    print()
    print("=" * 60)
    print("POSTGRESQL CONNECTION FAILED (STORE)")
    print("=" * 60)

    print(
        "Error:",
        error
    )

    print("=" * 60)

    try:

        connection.close()

    except Exception:

        pass

    try:

        store_connection.close()

    except Exception:

        pass

    raise RuntimeError(
        "Could not connect to PostgreSQL for the long-term store."
    ) from error


# ============================================================
# CREATE LANGGRAPH STORE
# ============================================================

print()
print(
    "Creating LangGraph PostgreSQL store..."
)


try:

    store = PostgresStore(
        store_connection
    )

    print(
        "LangGraph store created."
    )


except Exception as error:

    print()
    print(
        "Failed to create LangGraph store:"
    )

    print(
        error
    )

    try:

        store_connection.close()

    except Exception:

        pass

    raise RuntimeError(
        "Could not create LangGraph PostgreSQL store."
    ) from error


# ============================================================
# CREATE / UPDATE LANGGRAPH TABLES (STORE)
# ============================================================

print()
print(
    "Setting up LangGraph store tables..."
)


try:

    store.setup()

    print(
        "LangGraph store tables are ready."
    )


except Exception as error:

    print()
    print("=" * 60)
    print("LANGGRAPH STORE SETUP FAILED")
    print("=" * 60)

    print(
        "Error:",
        error
    )

    print("=" * 60)

    try:

        store_connection.close()

    except Exception:

        pass

    raise RuntimeError(
        "Could not initialize LangGraph store tables."
    ) from error


# ============================================================
# FINAL STATUS
# ============================================================

print()
print("=" * 60)
print("DATABASE READY")
print("=" * 60)

print(
    "PostgreSQL: CONNECTED"
)

print(
    "LangGraph checkpointer (short-term): READY"
)

print(
    "LangGraph store (long-term): READY"
)

print(
    "Persistence: ENABLED"
)

print("=" * 60)