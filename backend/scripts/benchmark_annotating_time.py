"""Benchmark the annotating-time computation: before (ORM) vs after (SQL).

Seeds a deterministic dataset (annotators x images x annotations), then
compares the old Python/ORM implementation (embedded below, copied from
commit 45d1d5c) with the new SQL implementation in
``api.services.annotations``. The script verifies that both produce the
same per-annotator totals, measures wall time (1 warm-up + N timed runs,
fresh session per call) and peak Python memory (tracemalloc, separate
runs).

Examples:
    .venv/bin/python scripts/benchmark_annotating_time.py
    .venv/bin/python scripts/benchmark_annotating_time.py \\
        --db-url postgresql+asyncpg://bench:bench@localhost:5434/bench --do-it
"""

import argparse
import asyncio
import re
import time
import tracemalloc
from collections import defaultdict
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from itertools import islice

from sqlalchemy import func, insert, select, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel import select as sm_select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models.annotations import (
    AnnotatedImage,
    Annotation,
    CompletionStatus,
    DamageLevel,
    User,
    ValidationStatus,
)
from api.services.annotations import (
    get_annotating_seconds_by_annotator as get_annotating_seconds_sql,
)

POLYGON = [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]]
SEED_BASE = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)


# --- BEFORE: ORM/Python implementation (copied from commit 45d1d5c) -------


def compute_annotating_time(image: AnnotatedImage) -> timedelta:
    """Compute the total time spent annotating one image.

    Collect the effective timestamp of each annotation (updated_at when set,
    otherwise created_at), batch them by day, and for each day take the span
    between the latest and the earliest timestamp. A day with a single
    annotation contributes zero. Return the sum over all days.
    """
    timestamps_by_day: dict[date, list[datetime]] = defaultdict(list)

    for annotation in image.annotations:
        if annotation.updated_at is not None:
            timestamp = annotation.updated_at
        else:
            timestamp = annotation.created_at
        if timestamp is None:
            continue
        # SQLite returns naive UTC datetimes; Postgres returns aware ones.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        timestamps_by_day[timestamp.date()].append(timestamp)

    total = timedelta()
    for timestamps in timestamps_by_day.values():
        if len(timestamps) < 2:
            continue  # Single annotation on this day: zero time.
        total += max(timestamps) - min(timestamps)
    return total


async def get_annotating_seconds_by_annotator_orm(
    annotator_ids: list[int], session: AsyncSession
) -> dict[int, int]:
    """Compute the total annotating time (seconds) for each given annotator."""
    if not annotator_ids:
        return {}

    images = await session.exec(
        sm_select(AnnotatedImage).where(AnnotatedImage.annotator_id.in_(annotator_ids))
    )
    totals: dict[int, timedelta] = defaultdict(timedelta)
    for image in images:
        if image.annotator_id is not None:
            totals[image.annotator_id] += compute_annotating_time(image)

    return {
        annotator_id: round(total.total_seconds())
        for annotator_id, total in totals.items()
    }


# --- Dataset seeding -------------------------------------------------------


def user_rows(annotators: int) -> Iterator[dict]:
    for i in range(annotators):
        yield {
            "id": i + 1,
            "email": f"bench{i:03d}@example.com",
            "full_name": f"Bench Annotator {i}",
            "is_reviewer": False,
        }


def image_rows(annotators: int, images_per_annotator: int) -> Iterator[dict]:
    for i in range(annotators):
        for j in range(images_per_annotator):
            yield {
                "id": i * images_per_annotator + j + 1,
                "image_path": f"bench/{i:03d}/{j:03d}.jpg",
                "annotator_id": i + 1,
                "validation_status": ValidationStatus.PENDING,
                "completion_status": CompletionStatus.NOT_COMPLETED,
            }


def annotation_rows(
    annotators: int, images_per_annotator: int, annotations_per_image: int
) -> Iterator[dict]:
    for i in range(annotators):
        for j in range(images_per_annotator):
            start = SEED_BASE + timedelta(days=j % 5, minutes=(i * 7 + j * 13) % 360)
            for k in range(annotations_per_image):
                created_at = start + timedelta(seconds=45 * k)
                yield {
                    "annotated_image_id": i * images_per_annotator + j + 1,
                    "polygon": POLYGON,
                    "damage_level": DamageLevel.UNSET,
                    "created_at": created_at,
                    "updated_at": (
                        created_at + timedelta(seconds=90) if k % 3 == 2 else None
                    ),
                }


def chunked(rows: Iterator[dict], size: int) -> Iterator[list[dict]]:
    while True:
        chunk = list(islice(rows, size))
        if not chunk:
            return
        yield chunk


async def seed(engine, args) -> list[int]:
    """Create the tables and insert the deterministic dataset.

    Any existing tables of the target database are dropped, so this wipes
    its data. main() refuses persistent targets without --do-it.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

        await conn.execute(insert(User.__table__), list(user_rows(args.annotators)))
        for chunk in chunked(
            image_rows(args.annotators, args.images_per_annotator), args.chunk_size
        ):
            await conn.execute(insert(AnnotatedImage.__table__), chunk)
        for chunk in chunked(
            annotation_rows(
                args.annotators,
                args.images_per_annotator,
                args.annotations_per_image,
            ),
            args.chunk_size,
        ):
            await conn.execute(insert(Annotation.__table__), chunk)

    if engine.dialect.name == "postgresql":
        # Give the planner up-to-date statistics after the bulk insert.
        async with engine.begin() as conn:
            await conn.execute(text("ANALYZE"))

    async with engine.connect() as conn:
        users_count = await conn.scalar(
            select(func.count()).select_from(User.__table__)
        )
        images_count = await conn.scalar(
            select(func.count()).select_from(AnnotatedImage.__table__)
        )
        annotations_count = await conn.scalar(
            select(func.count()).select_from(Annotation.__table__)
        )
        print(
            f"Dataset: {users_count} users, {images_count} images, "
            f"{annotations_count} annotations"
        )

    return list(range(1, args.annotators + 1))


# --- Measurement helpers ---------------------------------------------------


async def run_once(engine, fn, annotator_ids: list[int]) -> dict[int, int]:
    """Run one call on a fresh session (no ORM identity-map carry-over)."""
    async with AsyncSession(engine) as session:
        return await fn(annotator_ids, session)


def mask_password(url: str) -> str:
    return re.sub(r"://([^:/@]+):[^@]+@", r"://\1:***@", url)


async def check_correctness(engine, annotator_ids: list[int]) -> bool:
    """Verify that the old and new implementations agree (<= 1s tolerance)."""
    old = await run_once(engine, get_annotating_seconds_by_annotator_orm, annotator_ids)
    new = await run_once(engine, get_annotating_seconds_sql, annotator_ids)

    if set(old) != set(new):
        print(f"MISMATCH: id sets differ (old {len(old)}, new {len(new)})")
        return False

    max_diff = max((abs(old[key] - new[key]) for key in old), default=0)
    print(f"Correctness: max |old - new| = {max_diff} s over {len(old)} annotators")

    if max_diff > 1:
        differing = [
            (key, old[key], new[key]) for key in old if abs(old[key] - new[key]) > 1
        ]
        print(f"MISMATCH: {len(differing)} annotators differ, first 5: {differing[:5]}")
        return False

    print("Correctness: MATCH")
    return True


async def timed_runs(engine, fn, annotator_ids: list[int], runs: int) -> list[float]:
    """One untimed warm-up, then N timed runs (fresh session each)."""
    await run_once(engine, fn, annotator_ids)
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        await run_once(engine, fn, annotator_ids)
        times.append(time.perf_counter() - start)
    return times


async def peak_memory(engine, fn, annotator_ids: list[int]) -> float:
    """Peak Python-side memory of one call, in MB."""
    tracemalloc.start()
    await run_once(engine, fn, annotator_ids)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / (1024 * 1024)


# --- Report ----------------------------------------------------------------

IMPLEMENTATIONS = [
    ("before (ORM/Python)", get_annotating_seconds_by_annotator_orm),
    ("after (SQL)", get_annotating_seconds_sql),
]


def print_report(url: str, dialect: str, measurements: dict, runs: int) -> None:
    print()
    print(f"Database: {mask_password(url)} (dialect: {dialect})")
    print(f"Timed runs per implementation: {runs} (plus 1 untimed warm-up each)")
    print(
        "Note: timings come from runs WITHOUT tracemalloc; "
        "memory peaks come from separate runs."
    )
    print()
    print(
        f"{'implementation':<22} {'best (s)':>10} {'mean (s)':>10} {'peak mem (MB)':>14}"
    )
    for label, _ in IMPLEMENTATIONS:
        entry = measurements[label]
        print(
            f"{label:<22} {entry['best']:>10.3f} {entry['mean']:>10.3f} "
            f"{entry['peak_mb']:>14.1f}"
        )
    speedup = (
        measurements["before (ORM/Python)"]["best"]
        / measurements["after (SQL)"]["best"]
    )
    print(f"\nSpeedup (best/best): {speedup:.1f}x")
    print()
    print("| implementation | runs | best (s) | mean (s) | peak mem (MB) |")
    print("| --- | --- | --- | --- | --- |")
    for label, _ in IMPLEMENTATIONS:
        entry = measurements[label]
        print(
            f"| {label} | {runs} | {entry['best']:.3f} | {entry['mean']:.3f} "
            f"| {entry['peak_mb']:.1f} |"
        )
    print()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", default="sqlite+aiosqlite:///:memory:")
    parser.add_argument("--annotators", type=int, default=100)
    parser.add_argument("--images-per-annotator", type=int, default=100)
    parser.add_argument("--annotations-per-image", type=int, default=20)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--chunk-size", type=int, default=5000)
    parser.add_argument(
        "--do-it",
        action="store_true",
        help="Confirm wiping the target database; required for every "
        "persistent target (anything except an in-memory SQLite database).",
    )
    args = parser.parse_args()

    # Only an in-memory SQLite database is safe to drop without consent.
    # Any other target (postgres, a real sqlite file) is persistent: the
    # seed step below drops and re-creates its tables.
    if not (args.db_url.startswith("sqlite") and ":memory:" in args.db_url):
        if not args.do_it:
            parser.error(
                f"--db-url {mask_password(args.db_url)} is persistent: "
                "seeding drops and re-creates its tables. "
                "Pass --do-it to confirm."
            )
        engine_kwargs = {}
    else:
        engine_kwargs = {"poolclass": StaticPool}
    engine = create_async_engine(args.db_url, **engine_kwargs)

    try:
        annotator_ids = await seed(engine, args)

        if not await check_correctness(engine, annotator_ids):
            return 1

        measurements = {}
        for label, fn in IMPLEMENTATIONS:
            times = await timed_runs(engine, fn, annotator_ids, args.runs)
            peak_mb = await peak_memory(engine, fn, annotator_ids)
            measurements[label] = {
                "runs_detail": times,
                "best": min(times),
                "mean": sum(times) / len(times),
                "peak_mb": peak_mb,
            }
            print(
                f"{label}: runs = "
                + ", ".join(f"{t:.3f}s" for t in times)
                + f"; peak mem = {peak_mb:.1f} MB"
            )

        print_report(args.db_url, engine.dialect.name, measurements, args.runs)
        return 0
    finally:
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
