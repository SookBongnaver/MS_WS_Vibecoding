import argparse
import json
import sys

from .catalog import CATEGORIES, EXAMPLES
from .config import ROOT, SCENARIOS, load_config
from .runtime import calculate, instruction, model_client, save_report, turn
from .storage import FixtureStore, SqlStore, connect_sql, seed


def readonly_check(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""
SELECT HAS_PERMS_BY_NAME('workshop.Record','OBJECT','SELECT'),
       HAS_PERMS_BY_NAME('workshop.Record','OBJECT','INSERT'),
       HAS_PERMS_BY_NAME('workshop.Record','OBJECT','UPDATE'),
       HAS_PERMS_BY_NAME('workshop.Record','OBJECT','DELETE'),
       HAS_PERMS_BY_NAME('workshop.Record','OBJECT','ALTER'),
       HAS_PERMS_BY_NAME('workshop.Record','OBJECT','CONTROL'),
       IS_ROLEMEMBER('db_owner')
""")
        row = cursor.fetchone()
        if row is None or row[0] != 1 or any(value != 0 for value in row[1:]):
            raise PermissionError("Runtime requires SELECT-only access. Use a non-admin Entra DB user.")
    finally:
        cursor.close()


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Synthetic business agent workshop")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    selection = check.add_mutually_exclusive_group(required=True)
    for option in ("local", "model", "db"):
        selection.add_argument(f"--{option}", action="store_true")
    for command in ("example", "run", "seed"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--scenario", choices=SCENARIOS, required=True)
        if command != "seed":
            cmd.add_argument("--mode", choices=("starter", "solution"), default="starter")
    args = parser.parse_args()
    if args.command == "check" and args.local:
        for scenario in SCENARIOS:
            store = FixtureStore(scenario)
            instruction(scenario)
            print(f"OK {scenario}: {len(store.rows)} synthetic records")
        print("LOCAL ONLY: no Azure, DB or model connection was tested.")
        return
    if args.command == "example":
        result = calculate(FixtureStore(args.scenario), args.mode, EXAMPLES[args.scenario])
        print("OFFLINE CALCULATION ONLY - no model and no Azure SQL connection.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    require = "model" if args.command == "check" and args.model else "db"
    config = load_config(require="all" if args.command == "run" else require)
    if args.command == "check" and args.model:
        with model_client(config) as client:
            response = client.chat.completions.create(
                model=config["deployment"], messages=[{"role": "user", "content": "Reply only: MODEL_OK"}],
                max_completion_tokens=200,
            )
            text = response.choices[0].message.content
            if not text:
                raise RuntimeError("Model returned empty content")
            print(text)
        return
    connection = connect_sql(config)
    try:
        if args.command == "seed":
            confirm = input(f"Insert missing synthetic {args.scenario} records into configured DB? Type SEED: ")
            if confirm != "SEED":
                print("Cancelled. No changes made.")
                return
            print(f"Inserted: {seed(connection, args.scenario)} (existing rows unchanged)")
            return
        readonly_check(connection)
        scenario = config["scenario"] if args.command == "check" else args.scenario
        store = SqlStore(connection, scenario)
        if args.command == "check":
            for category in CATEGORIES[scenario]:
                rows = store.list_records(category)
                if not rows:
                    raise ValueError(f"No {category} records. Ask administrator to seed {scenario}.")
                print(f"DB_OK {category}: {len(rows)} rows")
            return
        print(f"Mode: {args.mode}; scenario: {scenario}. Synthetic data only.")
        print("Type exit to finish; /save exports the last answer after confirmation.")
        history = [{"role": "system", "content": instruction(scenario)}]
        last = None
        with model_client(config) as client:
            while True:
                question = input("\nYou> ").strip()
                if question == "exit":
                    break
                if question == "/save":
                    if last is None:
                        print("No completed answer to save.")
                        continue
                    name = input("Filename (for example briefing-01.txt): ").strip()
                    if input("Save this answer locally? Type SAVE: ") == "SAVE":
                        print(save_report(last, name))
                    else:
                        print("Save cancelled.")
                    continue
                if not question:
                    print("Enter a business question, /save or exit.")
                    continue
                if len(question) > 4000:
                    print("Request too long; limit is 4000 characters.")
                    continue
                if len(history) > 100:
                    print("Conversation limit reached. Restart for a new session.")
                    break
                last = turn(client, config["deployment"], store, args.mode, history, question)
                print("\nAgent>", last)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
