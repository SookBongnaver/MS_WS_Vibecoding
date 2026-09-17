import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ("walkerhill", "mintit", "speedmate", "incross", "intellix")


def validate_endpoint(endpoint):
    if not isinstance(endpoint, str):
        raise ValueError("endpoint must be a string")
    parsed = urlsplit(endpoint)
    host = parsed.hostname or ""
    allowed = re.fullmatch(
        r"[a-z0-9][a-z0-9-]*\.(openai\.azure\.com|services\.ai\.azure\.com)",
        host,
    )
    if (parsed.scheme != "https" or not allowed or parsed.port is not None
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path != "/openai/v1/"):
        raise ValueError(
            "endpoint must be https://RESOURCE.openai.azure.com/openai/v1/ "
            "or https://RESOURCE.services.ai.azure.com/openai/v1/; "
            "a Foundry project endpoint is NOT an OpenAI v1 endpoint"
        )
    return endpoint


def load_config(path=None, *, require="all"):
    path = path or ROOT / "config.local.json"
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise ValueError("Copy config.example.json to config.local.json and edit it.") from None
    if not isinstance(data, dict):
        raise ValueError("Configuration must be a JSON object")
    allowed = {"scenario", "endpoint", "deployment", "sql_server", "sql_database", "tenant_id"}
    if set(data) - allowed:
        raise ValueError("Unknown configuration fields; API keys/passwords are not supported")
    if data.get("scenario") not in SCENARIOS:
        raise ValueError("scenario must be one of: " + ", ".join(SCENARIOS))
    tenant = data.get("tenant_id", "")
    if tenant:
        UUID(tenant)
    if require in ("all", "model"):
        validate_endpoint(data.get("endpoint"))
        deployment = data.get("deployment")
        if not isinstance(deployment, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", deployment):
            raise ValueError("deployment must be your deployed model name, not a model family URL")
        if "YOUR-" in deployment.upper() or "YOUR-" in data["endpoint"].upper():
            raise ValueError("Replace the model placeholders in config.local.json")
    if require in ("all", "db"):
        server, database = data.get("sql_server"), data.get("sql_database")
        if not isinstance(server, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.database\.windows\.net", server):
            raise ValueError("sql_server must be SERVER.database.windows.net (no port/connection string)")
        if not isinstance(database, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_ -]{0,127}", database):
            raise ValueError("sql_database must be a plain database name")
        if "YOUR-" in server.upper() or "YOUR-" in database.upper():
            raise ValueError("Replace the SQL placeholders in config.local.json")
    return data
