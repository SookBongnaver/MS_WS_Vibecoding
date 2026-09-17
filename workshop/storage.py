import json
import re
import struct

from .catalog import CATEGORIES
from .config import ROOT

MAX_ROWS = 30
MAX_PAYLOAD = 16000


def validate_lookup(scenario, category, record_id=None):
    if scenario not in CATEGORIES or category not in CATEGORIES[scenario]:
        raise ValueError("Unknown scenario/category")
    if record_id is not None and (not isinstance(record_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", record_id)):
        raise ValueError("record_id must contain 1-64 letters, digits, underscores or hyphens")


def fixture_records(scenario):
    if scenario not in CATEGORIES:
        raise ValueError("Unknown scenario")
    rows = json.loads((ROOT / "data" / f"{scenario}.json").read_text(encoding="utf-8"))
    seen = set()
    for row in rows:
        validate_lookup(scenario, row["category"], row["record_id"])
        if row["record_id"] in seen:
            raise ValueError("Duplicate fixture ID")
        seen.add(row["record_id"])
        if not isinstance(row["payload"], dict) or len(json.dumps(row["payload"])) > MAX_PAYLOAD:
            raise ValueError("Invalid fixture payload")
    return rows


class FixtureStore:
    def __init__(self, scenario):
        self.scenario = scenario
        self.rows = fixture_records(scenario)

    def list_records(self, category):
        validate_lookup(self.scenario, category)
        rows = [r.copy() for r in self.rows if r["category"] == category]
        if len(rows) > MAX_ROWS:
            raise ValueError("Category exceeds workshop row limit; refusing incomplete calculation")
        return rows

    def get_record(self, category, record_id):
        validate_lookup(self.scenario, category, record_id)
        return next((r for r in self.list_records(category) if r["record_id"] == record_id), None)


def credential(config):
    from azure.identity import AzureCliCredential
    return AzureCliCredential(**({"tenant_id": config["tenant_id"]} if config.get("tenant_id") else {}))


def connect_sql(config):
    import pyodbc
    token = credential(config).get_token("https://database.windows.net/.default").token
    encoded = token.encode("utf-16-le")
    token_struct = struct.pack("<I", len(encoded)) + encoded
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{config['sql_server']},1433;Database={config['sql_database']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=15;"
    )
    return pyodbc.connect(connection_string, attrs_before={1256: token_struct}, autocommit=False, timeout=15)


class SqlStore:
    def __init__(self, connection, scenario):
        if scenario not in CATEGORIES:
            raise ValueError("Unknown scenario")
        self.connection, self.scenario = connection, scenario

    def _select(self, category, record_id=None):
        validate_lookup(self.scenario, category, record_id)
        cursor = self.connection.cursor()
        cursor.timeout = 15
        try:
            # The extra row detects truncation; never silently calculate partial totals.
            query = "SELECT TOP (31) record_id, category, payload FROM workshop.Record WHERE scenario = ? AND category = ?"
            params = [self.scenario, category]
            if record_id is not None:
                query += " AND record_id = ?"
                params.append(record_id)
            cursor.execute(query + " ORDER BY record_id", *params)
            rows = cursor.fetchmany(MAX_ROWS + 1)
            if len(rows) > MAX_ROWS:
                raise ValueError("Category exceeds 30 rows; refusing incomplete calculation")
            result = []
            for rid, cat, raw in rows:
                if len(raw) > MAX_PAYLOAD:
                    raise ValueError("Database payload exceeds workshop limit")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError("Database payload must be a JSON object")
                result.append({"record_id": rid, "category": cat, "payload": payload})
            return result
        finally:
            cursor.close()

    def list_records(self, category):
        return self._select(category)

    def get_record(self, category, record_id):
        rows = self._select(category, record_id)
        return rows[0] if rows else None


def seed(connection, scenario):
    rows = fixture_records(scenario)
    cursor = connection.cursor()
    cursor.timeout = 30
    inserted = 0
    try:
        schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
        cursor.execute(schema)
        for row in rows:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM workshop.Record WITH (UPDLOCK,HOLDLOCK) "
                "WHERE scenario=? AND record_id=?) "
                "BEGIN INSERT INTO workshop.Record(scenario,record_id,category,payload) "
                "VALUES (?,?,?,?); SELECT 1 AS inserted; END ELSE SELECT 0 AS inserted;",
                scenario, row["record_id"], scenario, row["record_id"], row["category"],
                json.dumps(row["payload"], ensure_ascii=False),
            )
            while cursor.description is None:
                if not cursor.nextset():
                    raise RuntimeError("Seed insert result missing")
            inserted += int(cursor.fetchone()[0])
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
