import logging
import os
from functools import cache
from pathlib import Path

import cv2
import numpy as np

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
