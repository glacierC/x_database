"""
CLI for managing watched accounts and groups in x_database.

Usage:
    python cli.py account add <handle> [handle...]
    python cli.py account remove <handle>
    python cli.py account list

    python cli.py group create <name> [description]
    python cli.py group assign <name> <handle> [handle...]
    python cli.py group unassign <name> <handle>
    python cli.py group list
    python cli.py group show <name>
    python cli.py group delete <name>
"""

import sys
from src.db import (
    init_db,
    add_watched_account,
    remove_watched_account,
    get_watched_accounts,
    create_group,
    assign_to_group,
    unassign_from_group,
    get_groups,
    get_group_members,
    get_conn,
)


def cmd_account(args: list[str]) -> None:
    if not args:
        print("Usage: account <add|remove|list> ...")
        sys.exit(1)
    sub = args[0]

    if sub == "add":
        handles = args[1:]
        if not handles:
            print("Provide at least one handle.")
            sys.exit(1)
        for h in handles:
            add_watched_account(h.lstrip("@"))
            print(f"  + {h.lstrip('@')}")

    elif sub == "remove":
        if len(args) < 2:
            print("Usage: account remove <handle>")
            sys.exit(1)
        handle = args[1].lstrip("@")
        remove_watched_account(handle)
        print(f"  - {handle}")

    elif sub == "list":
        accounts = get_watched_accounts()
        if not accounts:
            print("(no watched accounts)")
        for a in accounts:
            fetched = a["last_fetched_at"] or "never"
            source = a.get("source") or "manual"
            print(f"  {a['handle']:<30} [{source:<10}] last fetched: {fetched}")

    else:
        print(f"Unknown subcommand: {sub}")
        sys.exit(1)


def cmd_group(args: list[str]) -> None:
    if not args:
        print("Usage: group <create|assign|unassign|list|show|delete> ...")
        sys.exit(1)
    sub = args[0]

    if sub == "create":
        if len(args) < 2:
            print("Usage: group create <name> [description]")
            sys.exit(1)
        name = args[1]
        description = " ".join(args[2:]) if len(args) > 2 else ""
        create_group(name, description)
        print(f"  Group '{name}' created.")

    elif sub == "assign":
        if len(args) < 3:
            print("Usage: group assign <name> <handle> [handle...]")
            sys.exit(1)
        name = args[1]
        handles = [h.lstrip("@") for h in args[2:]]
        for h in handles:
            assign_to_group(name, h)
            print(f"  {h} → {name}")

    elif sub == "unassign":
        if len(args) < 3:
            print("Usage: group unassign <name> <handle>")
            sys.exit(1)
        name, handle = args[1], args[2].lstrip("@")
        unassign_from_group(name, handle)
        print(f"  {handle} removed from {name}")

    elif sub == "list":
        groups = get_groups()
        if not groups:
            print("(no groups)")
        for g in groups:
            members = get_group_members(g["name"])
            desc = f" — {g['description']}" if g["description"] else ""
            print(f"  {g['name']:<20} ({len(members)} accounts){desc}")

    elif sub == "show":
        if len(args) < 2:
            print("Usage: group show <name>")
            sys.exit(1)
        name = args[1]
        members = get_group_members(name)
        print(f"Group: {name}  ({len(members)} accounts)")
        for h in members:
            print(f"  - {h}")

    elif sub == "delete":
        if len(args) < 2:
            print("Usage: group delete <name>")
            sys.exit(1)
        name = args[1]
        with get_conn() as conn:
            conn.execute("DELETE FROM account_group_members WHERE group_name = ?", (name,))
            conn.execute("DELETE FROM account_groups WHERE name = ?", (name,))
        print(f"  Group '{name}' deleted.")

    else:
        print(f"Unknown subcommand: {sub}")
        sys.exit(1)


def main() -> None:
    init_db()
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]
    rest = args[1:]

    if cmd == "account":
        cmd_account(rest)
    elif cmd == "group":
        cmd_group(rest)
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: account, group")
        sys.exit(1)


if __name__ == "__main__":
    main()
