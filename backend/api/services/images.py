import json
import logging
import math
import os
import random
import re
from functools import cache
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.config import config
from api.models.annotations import AnnotatedImage, ValidationStatus
from api.models.images import ImagePitchAngles
from api.services.files import list_local_files

logger = logging.getLogger("uvicorn.error")


EARTH_RADIUS = 6_371_000  # meters

detector = cv2.ORB_create(nfeatures=config.N_FEATURES)  # type: ignore
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


async def get_random_image_path_with_few_annotators(
    available_image_paths: set[str],
    session: AsyncSession,
) -> str | None:
    if not available_image_paths:
        return None

    # Get annotator counts for all annotated images in the available set
    # Don't count rejected annotations
    query = (
        select(
            AnnotatedImage.image_path,
            func.count(AnnotatedImage.annotator_id).label("annotator_count"),
        )
        .where(
            AnnotatedImage.image_path.in_(list(available_image_paths)),
        )
        .where(
            AnnotatedImage.validation_status != ValidationStatus.REJECTED,
        )
        .group_by(AnnotatedImage.image_path)
    )
    result = await session.exec(query)
    annotated_counts = {image_path: count for image_path, count in result.all()}

    # Prioritise images that have never been annotated (0 annotators)
    unannotated_paths = available_image_paths - annotated_counts.keys()
    if unannotated_paths:
        return random.choice(list(unannotated_paths))

    # All images are annotated. Find the minimum from the data we already have
    min_count = min(annotated_counts.values())
    best_images = [
        path for path, count in annotated_counts.items() if count == min_count
    ]
    return random.choice(best_images)


async def get_best_overlap(
    image_path: str, excluded_image_names: list[str]
) -> tuple[str, list[list[float]], float] | None:
    other_image_names = list(
        get_image_names(os.path.dirname(image_path))
        - set(excluded_image_names)
        - {os.path.basename(image_path)}
    )
    return await get_best_overlap_with_others(image_path, other_image_names)


async def get_best_overlap_with_others(
    image_path: str, other_image_names: list[str]
) -> tuple[str, list[list[float]], float] | None:
    other_image_paths = [
        os.path.join(os.path.dirname(image_path), name) for name in other_image_names
    ]
    distances = [
        (
            other_image_path,
            compute_geographic_distance(image_path, other_image_path),
        )
        for other_image_path in other_image_paths
    ]
    print(distances)
    best = min(distances, key=lambda x: x[1], default=("", float("inf")))

    if best[1] == float("inf"):
        return None

    best_image_path = best[0]
    homography_matrix, overlap_ratio = compute_overlap(image_path, best_image_path)
    return best_image_path, homography_matrix, overlap_ratio


@cache
def get_image_resolution(image_path: str) -> tuple[int, int]:
    with Image.open(Path(config.DATA_PATH) / image_path) as img:
        return img.size


@cache
def get_dataset_image_names() -> dict[str, set[str]]:
    dataset_image_names = {}

    for dataset_path in config.DATASETS:
        image_names = list_local_files(Path(config.DATA_PATH) / dataset_path)
        image_names = [
            path.split(os.sep)[-1]
            for path in image_names
            if path.lower().endswith(tuple(config.IMAGE_EXTENSIONS))
        ]
        image_names.sort()
        dataset_image_names[dataset_path] = set(image_names)

    return dataset_image_names


@cache
def get_image_names(dataset_path: str) -> set[str]:
    return get_dataset_image_names().get(dataset_path, set())


@cache
def get_all_image_paths() -> set[str]:
    """Get all image paths across all datasets."""

    all_image_paths = set()

    for dataset_path, image_names in get_dataset_image_names().items():
        image_paths = {os.path.join(dataset_path, name) for name in image_names}
        all_image_paths.update(image_paths)

    return all_image_paths


@cache
def compute_overlap(
    image1_path: str, image2_path: str
) -> tuple[list[list[float]], float]:
    if image1_path < image2_path:
        homography_matrix, overlap_ratio = _compute_overlap(image1_path, image2_path)
        return np.linalg.inv(homography_matrix).tolist(), overlap_ratio
    else:
        homography_matrix, overlap_ratio = _compute_overlap(image2_path, image1_path)
        return homography_matrix.tolist(), overlap_ratio


def _compute_overlap(image1_path: str, image2_path: str) -> tuple[np.ndarray, float]:
    logger.info(f"Computing overlap between {image1_path} and {image2_path}")

    kp1, des1 = compute_keypoints_and_descriptors(image1_path)
    kp2, des2 = compute_keypoints_and_descriptors(image2_path)

    try:
        matches = matcher.match(des1, des2)
    except cv2.error as e:
        logger.error(
            f"Error matching features between {image1_path} and {image2_path}: {e}"
        )
        return np.eye(3), 0.0

    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[: config.N_MATCHES]

    if not good_matches:
        return np.eye(3), 0.0

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])  # type: ignore
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])  # type: ignore

    homography_matrix, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)  # type: ignore
    inliers = mask.ravel().sum()
    total = len(mask)
    overlap_ratio = inliers / total if total > 0 else 0.0

    return homography_matrix, overlap_ratio


@cache
def compute_keypoints_and_descriptors(
    image_path: str,
) -> tuple[tuple[cv2.KeyPoint], np.ndarray]:
    image = cv2.imread(Path(config.DATA_PATH) / image_path, cv2.IMREAD_GRAYSCALE)
    keypoints, descriptors = detector.detectAndCompute(image, None)
    return keypoints, descriptors


async def get_image_location(image_path: str) -> dict[str, float]:
    return _get_image_location_sync(image_path)


@cache
def _get_image_location_sync(image_path: str) -> dict[str, float]:
    loc = None

    try:
        loc = _get_image_location_from_json(image_path)
    except Exception:
        pass

    if loc is not None and loc["latitude"] is not None and loc["longitude"] is not None:
        return loc

    return _get_image_location_from_exif(image_path)


def _dms_to_decimal(dms: list, ref: str) -> float:
    deg = dms[0][0] / dms[0][1] if isinstance(dms[0], list) else dms[0]
    min = dms[1][0] / dms[1][1] if isinstance(dms[1], list) else dms[1]
    sec = dms[2][0] / dms[2][1] if isinstance(dms[2], list) else dms[2]
    decimal = deg + min / 60 + sec / 3600

    if ref in ("S", "W"):
        decimal = -decimal

    return decimal


def _get_image_location_from_json(image_path: str) -> dict[str, float]:
    json_path = os.path.splitext(image_path)[0] + ".json"

    try:
        with open(Path(config.DATA_PATH) / json_path, "r") as f:
            metadata = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading location data for {image_path}: {e}")
        raise HTTPException(
            status_code=404,
            detail="Corresponding JSON metadata file not found or invalid",
        )

    gps_data = metadata.get("GPS", {})

    try:
        lat_ref = gps_data.get("GPSLatitudeRef", "N")
        lat = gps_data.get("GPSLatitude")
        lon_ref = gps_data.get("GPSLongitudeRef", "E")
        lon = gps_data.get("GPSLongitude")

        if not lat or not lon:
            logger.warning(f"Missing GPS coordinates for {image_path}")
            raise HTTPException(
                status_code=404, detail="GPS coordinates not found in metadata"
            )

        latitude = _dms_to_decimal(lat, lat_ref)
        longitude = _dms_to_decimal(lon, lon_ref)

        return {"latitude": latitude, "longitude": longitude}

    except Exception as e:
        logger.error(f"Error parsing GPS data for {image_path}: {e}")
        raise HTTPException(
            status_code=404, detail="Invalid GPS data format in metadata"
        )


def _get_image_location_from_exif(image_path: str) -> dict[str, float]:
    with Image.open(Path(config.DATA_PATH) / image_path) as img:
        exif_data = img._getexif()  # type: ignore

        if not exif_data:
            logger.warning(f"No EXIF data found for {image_path}")
            raise HTTPException(status_code=404, detail="No EXIF data found")

        tagged = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
        gps_info = tagged.get("GPSInfo")

        if not gps_info:
            logger.warning(f"No GPS data found in EXIF for {image_path}")
            raise HTTPException(status_code=404, detail="No GPS data found in EXIF")

        gps = {GPSTAGS.get(tag, tag): value for tag, value in gps_info.items()}

        try:
            lat_ref = gps.get("GPSLatitudeRef", "N")
            lat = gps.get("GPSLatitude")
            lon_ref = gps.get("GPSLongitudeRef", "E")
            lon = gps.get("GPSLongitude")

            if not lat or not lon:
                logger.warning(f"Missing GPS coordinates in EXIF for {image_path}")
                raise HTTPException(
                    status_code=404, detail="GPS coordinates not found in EXIF"
                )

            latitude = _dms_to_decimal(list(lat), lat_ref)
            longitude = _dms_to_decimal(list(lon), lon_ref)

            return {"latitude": latitude, "longitude": longitude}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error parsing EXIF GPS data for {image_path}: {e}")
            raise HTTPException(
                status_code=404, detail="Invalid GPS data format in EXIF"
            )


def compute_geographic_distance(image1_path: str, image2_path: str) -> float:
    try:
        loc1 = _get_image_location_sync(image1_path)
        loc2 = _get_image_location_sync(image2_path)
    except HTTPException:
        return float("inf")

    lat1, lon1 = math.radians(loc1["latitude"]), math.radians(loc1["longitude"])
    lat2, lon2 = math.radians(loc2["latitude"]), math.radians(loc2["longitude"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS * c


async def get_image_pitch_angles(image_path: str) -> ImagePitchAngles:
    xmp_data = _get_image_xmp(image_path)
    if xmp_data is None:
        logger.warning(f"No XMP metadata found for {image_path}")
        raise HTTPException(status_code=404, detail="No XMP metadata found")

    gimbal = _extract_xmp_tag(xmp_data, "GimbalPitchDegree")
    flight = _extract_xmp_tag(xmp_data, "FlightPitchDegree")

    return ImagePitchAngles(
        gimbal=None if gimbal is None else float(gimbal),
        flight=None if flight is None else float(flight),
    )


def _get_image_xmp(image_path: str) -> str | None:
    """Return the image XMP packet as a string, if present."""
    full_path = Path(config.DATA_PATH) / image_path
    with Image.open(full_path) as img:
        xmp = img.info.get("xmp")
        if not xmp:
            xmp = img.info.get("XML:com.adobe.xmp")
        if isinstance(xmp, bytes):
            return xmp.decode("utf-8", errors="ignore")
        return xmp


def _extract_xmp_tag(xmp_data: str, tag_name: str) -> str | None:
    """Extract a tag value from an XMP packet by its local tag name."""
    escaped = re.escape(tag_name)
    patterns = (
        rf'{escaped}\s*=\s*["\']([^"\']+)["\']',
        rf"<[^>]*?{escaped}[^>]*>([^<]+)</",
    )
    for pattern in patterns:
        match = re.search(pattern, xmp_data, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


# Trigger cache population at startup
get_all_image_paths()
