import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vaultdb.errors import StorageError
from vaultdb.storage import DocumentStorage


@dataclass
class VaultInspectionResult:
    file: str
    created_at: Optional[str]
    vault_version: Optional[str]
    app_name: str
    salt: str
    document_count: int
    document_ids: List[str]


def print_human_output(result: VaultInspectionResult, max_ids: int, quiet: bool):
    if not quiet:
        print("VaultDB Inspector 🔍")
        print("-" * 30)
    print(f"📁 File: {result.file}")
    print(f"📅 Created At: {result.created_at}")
    print(f"🔖 Vault Version: {result.vault_version}")
    print(f"🏷️ App Name: {result.app_name}")
    print(f"🧂 Salt: {result.salt[:20]}... (truncated)")
    print(f"📄 Document Count: {result.document_count}")
    if result.document_ids:
        print(f"🆔 IDs (first {len(result.document_ids)}):")
        for _id in result.document_ids[:max_ids]:
            print(f"  - {_id}")
        if result.document_count > max_ids:
            print(f"... and {result.document_count - max_ids} more")


def inspect_vault(path: str, max_ids: int = 10, output_json: bool = False, quiet: bool = False):
    try:
        if max_ids < 0:
            raise ValueError("max_ids must be >= 0")

        if not os.path.exists(path):
            print(f"Error: No such file: {path}", file=sys.stderr)
            sys.exit(1)

        store = DocumentStorage(path)
        meta = dict(store.meta)
        doc_ids = list(store.data.keys())

        result = VaultInspectionResult(
            file=os.path.basename(path),
            created_at=meta.get("created_at"),
            vault_version=meta.get("vault_version"),
            app_name=meta.get("app_name", "—"),
            salt=meta.get("salt", "missing"),
            document_count=len(doc_ids),
            document_ids=doc_ids[:max_ids]
        )

        if output_json:
            print(json.dumps(result.__dict__, indent=2))
        else:
            print_human_output(result, max_ids, quiet)

    except StorageError as e:
        print(f"Storage error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="VaultDB CLI — inspect encrypted .vault files without revealing data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a VaultDB .vault file")
    inspect_parser.add_argument("vault_path", help="Path to the .vault file")
    inspect_parser.add_argument("--max-ids", "-n", type=int, default=10,
                                help="Max number of document IDs to display")
    inspect_parser.add_argument("--json", action="store_true", help="Output as JSON")
    inspect_parser.add_argument("--quiet", "-q", action="store_true",
                                help="Suppress headers and emojis")

    args = parser.parse_args()

    if args.command == "inspect":
        inspect_vault(args.vault_path, args.max_ids, args.json, args.quiet)


if __name__ == "__main__":
    main()