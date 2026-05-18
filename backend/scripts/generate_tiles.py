"""Utility function to generate dzi tiles for all images in the given directory (recursively).

The directory structure is replicated in the tiles directory.
"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pyvips

from api.config import config


TILE_SIZE = 256  # pixels
TILE_SUFFIX = ".webp[Q=70]"


def main(dir_path: str, tiles_dir_path) -> None:
    tasks: list[tuple[str, str]] = []

    for root, _, files in os.walk(dir_path):
        for file in files:
            if not file.lower().endswith(tuple(config.IMAGE_EXTENSIONS)):
                continue

            image_path = os.path.join(root, file)
            image_name = os.path.splitext(file)[0]
            relative_path = os.path.relpath(image_path, dir_path)
            tile_output_base_path = os.path.join(
                tiles_dir_path, os.path.dirname(relative_path), image_name
            )

            if os.path.exists(tile_output_base_path + ".dzi"):
                print(f"Tiles already exist for {image_path}, skipping...")
                continue

            tasks.append((image_path, tile_output_base_path))

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_generate_tiles, image_path, tile_output_base_path)
            for image_path, tile_output_base_path in tasks
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error generating tiles: {e}")


def _generate_tiles(image_path: str, tile_output_base_path: str) -> None:
    print(f"Generating tiles for {image_path}...")
    os.makedirs(os.path.dirname(tile_output_base_path), exist_ok=True)
    image = pyvips.Image.new_from_file(image_path, access="sequential")
    image.dzsave(tile_output_base_path, suffix=TILE_SUFFIX, tile_size=TILE_SIZE)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_tiles.py <dir_path> <tiles_dir_path>")
        sys.exit(1)

    dir_path = sys.argv[1]
    tiles_dir_path = sys.argv[2]
    main(dir_path, tiles_dir_path)
