"""Script to extract gimbal and flight pitch angles for all images and save to CSV."""

import asyncio
import csv
import logging
import os
import sys

from fastapi import HTTPException

from api.config import config
from api.services.images import get_all_image_paths, get_image_pitch_angles

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main(output_path: str = "pitch_angles.csv") -> None:
    """Iterate over all dataset images, extract pitch angles, and write them to a CSV."""
    image_paths = sorted(get_all_image_paths())
    logger.info(f"Found {len(image_paths)} images")

    dataset_paths: list[str] = []
    image_names: list[str] = []
    gimbal_angles: list[str | float] = []
    flight_angles: list[str | float] = []

    for image_path in image_paths:
        dataset_path = os.path.dirname(image_path)
        image_name = os.path.basename(image_path)

        try:
            angles = await get_image_pitch_angles(image_path)
        except HTTPException as e:
            logger.warning(f"Skipping {image_path}: {e.detail}")
            continue
        except Exception as e:
            logger.warning(f"Skipping {image_path}: {e}")
            continue

        dataset_paths.append(dataset_path)
        image_names.append(image_name)
        gimbal_angles.append(angles.gimbal if angles.gimbal is not None else "")
        flight_angles.append(angles.flight if angles.flight is not None else "")

        if len(dataset_paths) % 100 == 0:
            logger.info(f"Processed {len(dataset_paths)} images")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["dataset_path", "image_name", "gimbal_pitch_angle", "flight_pitch_angle"]
        )
        writer.writerows(
            zip(dataset_paths, image_names, gimbal_angles, flight_angles)
        )

    logger.info(f"Wrote {len(dataset_paths)} rows to {output_path}")


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "pitch_angles.csv"
    asyncio.run(main(output_path))
