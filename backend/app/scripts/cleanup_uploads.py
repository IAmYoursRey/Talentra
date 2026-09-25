import asyncio
import argparse
import sys
from backend.app.services.maintenance import cleanup_stale_uploads


async def main():
    parser = argparse.ArgumentParser(description="Clean up stale pending uploads from TALENTRA storage.")
    parser.add_argument(
        "--ttl-seconds",
        type=int,
        default=86400,
        help="Age threshold in seconds for stale pending uploads (default: 86400 = 24h)",
    )
    args = parser.parse_args()

    print(f"Starting stale upload cleanup (threshold: {args.ttl_seconds} seconds)...")
    purged = await cleanup_stale_uploads(older_than_seconds=args.ttl_seconds)
    print(f"Successfully cleaned up {len(purged)} stale upload record(s).")


if __name__ == "__main__":
    asyncio.run(main())
