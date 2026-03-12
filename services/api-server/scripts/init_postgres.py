from argparse import ArgumentParser

from app.repositories.bootstrap import initialize_postgres_database


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Initialize the aitender PostgreSQL schema and optional seed data."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional PostgreSQL connection URL. Falls back to AITENDER_DATABASE_URL.",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Create schema only and skip default seed data.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    initialize_postgres_database(
        database_url=args.database_url,
        seed=not args.skip_seed,
    )
    print("PostgreSQL schema initialization completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
