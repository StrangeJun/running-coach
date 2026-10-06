"""Run manually with: python -m app.garmin_cli"""

import argparse
import getpass
import logging
import sys
from pathlib import Path

from app.integrations.garmin import (
    DEFAULT_TOKEN_DIRECTORY, GarminAccessError, GarminClient, GarminDataError,
)


def _credentials() -> tuple[str, str]:
    return input("Garmin email: ").strip(), getpass.getpass("Garmin password: ")


def _mfa() -> str:
    return getpass.getpass("Garmin MFA code: ").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the latest recent Garmin run as normalized JSON.")
    parser.add_argument("--token-dir", type=Path, default=DEFAULT_TOKEN_DIRECTORY)
    parser.add_argument("--limit", type=int, default=50, help="Recent running activities to inspect (1–100).")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")

    # Upstream failure logging may include responses; expose only our safe errors.
    logging.getLogger("garminconnect").setLevel(logging.CRITICAL + 1)
    client = GarminClient(args.token_dir, credential_provider=_credentials, prompt_mfa=_mfa)
    try:
        run = client.latest_run(limit=args.limit)
    except (GarminAccessError, GarminDataError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Garmin access cancelled.", file=sys.stderr)
        return 1
    if run is None:
        print("No running activity found in the recent activity window.", file=sys.stderr)
        return 2
    print(run.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
