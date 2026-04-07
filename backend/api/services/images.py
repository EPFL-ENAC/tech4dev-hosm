import json
import logging
import os
from functools import cache
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException
from PIL import Image

from api.config import config
from api.services.files import list_local_files

logger = logging.getLogger("uvicorn.error")


detector = cv2.ORB_create(nfeatures=config.N_FEATURES)  # type: ignore
matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


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
    overlaps = [
        (
            other_image_path,
            *compute_overlap(image_path, other_image_path),
        )
        for other_image_path in other_image_paths
    ]

    best = max(overlaps, key=lambda x: x[2], default=("", [], 0.0))
    return best if best[2] > 0 else None


@cache
def get_image_resolution(image_path: str) -> tuple[int, int]:
    with Image.open(Path(config.DATA_PATH) / image_path) as img:
        return img.size


@cache
def get_image_names(dataset_path: str) -> set[str]:
    return {
        path.split(os.sep)[-1]
        for path in list_local_files(Path(config.DATA_PATH) / Path(dataset_path))
        if path.lower().endswith((".jpg", ".jpeg", ".png"))
    }


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


@cache
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

    pts1 = np.float32([kp1[m.queryIdx].pt for m in good_matches])
    pts2 = np.float32([kp2[m.trainIdx].pt for m in good_matches])

    homography_matrix, mask = cv2.findHomography(pts1, pts2, cv2.RANSAC, 5.0)
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

        lat_deg = lat[0][0] / lat[0][1] if isinstance(lat[0], list) else lat[0]
        lat_min = lat[1][0] / lat[1][1] if isinstance(lat[1], list) else lat[1]
        lat_sec = lat[2][0] / lat[2][1] if isinstance(lat[2], list) else lat[2]

        lon_deg = lon[0][0] / lon[0][1] if isinstance(lon[0], list) else lon[0]
        lon_min = lon[1][0] / lon[1][1] if isinstance(lon[1], list) else lon[1]
        lon_sec = lon[2][0] / lon[2][1] if isinstance(lon[2], list) else lon[2]

        latitude = lat_deg + lat_min / 60 + lat_sec / 3600
        longitude = lon_deg + lon_min / 60 + lon_sec / 3600

        if lat_ref == "S":
            latitude = -latitude
        if lon_ref == "W":
            longitude = -longitude

        return {"latitude": latitude, "longitude": longitude}

    except Exception as e:
        logger.error(f"Error parsing GPS data for {image_path}: {e}")
        raise HTTPException(
            status_code=404, detail="Invalid GPS data format in metadata"
        )
