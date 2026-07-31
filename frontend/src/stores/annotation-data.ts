import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { baseUrl, authFetch } from 'boot/api';
import type {
  AnnotatedImage,
  AnnotationData,
  Annotation,
  Overlap,
  Point,
  AnnotatedImageRead,
  AnnotationRead,
  DamageLevel as DamageLevelType,
  ValidationStatus,
  CompletionStatus,
} from '../models';
import { Notify } from 'quasar';
import { getI18nT } from 'src/utils/i18n';

export const DAMAGE_LEVELS: DamageLevelType[] = ['unset', 'undamaged', 'damaged'];
export const DAMAGE_COLORS = ['#444444', '#1974d2', '#ff007f'];

const OVERLAP_RATIO_THRESHOLD = 0.3;
const INTERSECTION_THRESHOLD = 1e-6;
const ANNOTATIONS_EQUAL_THRESHOLD = 1e-9;

function annotationToApi(annotation: Annotation): {
  polygon: number[][];
  damage_level: DamageLevelType;
} {
  const damageBody = annotation.bodies.find((b) => b.purpose === 'damage');
  const damageLevel = damageBody ? (damageBody.value as DamageLevelType) : 'unset';
  const polygon = annotation.target.selector.geometry.points;
  return { polygon, damage_level: damageLevel };
}

function annotationFromApi(apiAnnotation: {
  id: number;
  polygon: number[][];
  damage_level: DamageLevelType;
}): Annotation {
  return {
    id: apiAnnotation.id.toString(),
    bodies: [{ purpose: 'damage', value: apiAnnotation.damage_level }],
    target: {
      annotation: '',
      selector: {
        type: 'POLYGON',
        geometry: {
          bounds: {
            minX: Math.min(...(apiAnnotation.polygon.map((p) => p[0]) as number[])),
            maxX: Math.max(...(apiAnnotation.polygon.map((p) => p[0]) as number[])),
            minY: Math.min(...(apiAnnotation.polygon.map((p) => p[1]) as number[])),
            maxY: Math.max(...(apiAnnotation.polygon.map((p) => p[1]) as number[])),
          },
          points: apiAnnotation.polygon as Point[],
        },
      },
      creator: { isGuest: false, id: '' },
      created: new Date(),
    },
  };
}

function annotationsEqual(a: Annotation, b: Annotation): boolean {
  if (a.id !== b.id) return false;

  const aDamage = a.bodies.find((body) => body.purpose === 'damage')?.value ?? 'unset';
  const bDamage = b.bodies.find((body) => body.purpose === 'damage')?.value ?? 'unset';
  if (aDamage !== bDamage) return false;

  const aPoints = a.target.selector.geometry.points;
  const bPoints = b.target.selector.geometry.points;
  if (aPoints.length !== bPoints.length) return false;

  for (let i = 0; i < aPoints.length; i++) {
    const [ax, ay] = aPoints[i]!;
    const [bx, by] = bPoints[i]!;
    if (
      Math.abs(ax - bx) > ANNOTATIONS_EQUAL_THRESHOLD ||
      Math.abs(ay - by) > ANNOTATIONS_EQUAL_THRESHOLD
    )
      return false;
  }

  return true;
}

function circleFromThreePoints(
  p1: Point,
  p2: Point,
  p3: Point,
): { center: Point; radius: number } | null {
  // Perpendicular bisector of p1-p2
  const mid1: Point = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2];
  const dir1: Point = [-(p2[1] - p1[1]), p2[0] - p1[0]];
  // Perpendicular bisector of p2-p3
  const mid2: Point = [(p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2];
  const dir2: Point = [-(p3[1] - p2[1]), p3[0] - p2[0]];

  const det = dir1[0] * dir2[1] - dir1[1] * dir2[0];
  if (Math.abs(det) < INTERSECTION_THRESHOLD) return null; // parallel

  const dx = mid2[0] - mid1[0];
  const dy = mid2[1] - mid1[1];
  const t1 = (dx * dir2[1] - dy * dir2[0]) / det;

  const center: Point = [mid1[0] + t1 * dir1[0], mid1[1] + t1 * dir1[1]];
  const radius = Math.hypot(center[0] - p1[0], center[1] - p1[1]);

  return { center, radius };
}

function intersectBisectorAndCircle(
  edgeP1: Point,
  edgeP2: Point,
  circleCenter: Point,
  circleRadius: number,
  referencePoint: Point,
): Point {
  const dir: Point = [-(edgeP2[1] - edgeP1[1]), edgeP2[0] - edgeP1[0]];
  const dirLen = Math.hypot(dir[0], dir[1]);
  const unitDir: Point = [dir[0] / dirLen, dir[1] / dirLen];

  // The bisector goes through the circle center, so the two intersections
  // are simply center ± radius along the bisector direction.
  const pA: Point = [
    circleCenter[0] + circleRadius * unitDir[0],
    circleCenter[1] + circleRadius * unitDir[1],
  ];
  const pB: Point = [
    circleCenter[0] - circleRadius * unitDir[0],
    circleCenter[1] - circleRadius * unitDir[1],
  ];

  const distA = Math.hypot(pA[0] - referencePoint[0], pA[1] - referencePoint[1]);
  const distB = Math.hypot(pB[0] - referencePoint[0], pB[1] - referencePoint[1]);

  return distA < distB ? pA : pB;
}

type FetchCall = () => Promise<void>;

export const useAnnotationDataStore = defineStore('annotationData', () => {
  const userInfo = ref<AnnotationData['userInfo']>({
    fullName: '',
    email: '',
  });
  const annotatedImages = ref<AnnotatedImage[]>([]);
  const selectedImageUrl = ref<string | null>(null);
  const overlapsLoading = ref<Record<string, boolean>>({});
  const annotoriousIdToApiId = ref<Record<string, string>>({});
  const fetchQueue = ref<FetchCall[]>([]);
  const processingQueue = ref(false);
  const loadingAnnotations = ref(false);

  const imageCount = computed(() => annotatedImages.value.length);
  const totalAnnotations = computed(() =>
    annotatedImages.value.reduce((count, img) => count + img.annotations.length, 0),
  );
  const addingNewImage = ref(false);
  const overlapLoading = computed(() =>
    selectedImageUrl.value ? overlapsLoading.value[selectedImageUrl.value] === true : false,
  );
  const selectedImage = computed(() =>
    selectedImageUrl.value
      ? (annotatedImages.value.find((img) => img.imageUrl === selectedImageUrl.value) ?? null)
      : null,
  );

  async function loadAnnotations(annotatorId?: number) {
    loadingAnnotations.value = true;

    const url = annotatorId
      ? `${baseUrl}/annotations/annotated-images/?annotator_id=${annotatorId}`
      : `${baseUrl}/annotations/annotated-images/`;
    try {
      const response = await enqueueFetch(url);
      const images = await response.json();

      annotatedImages.value = images.map((img: AnnotatedImageRead) => ({
        imageId: img.id,
        imageUrl: `${baseUrl}/files/get/${img.image_path}`,
        annotations: img.annotations.map((ann: AnnotationRead) => annotationFromApi(ann)),
        completionStatus: img.completion_status,
        validationStatus: img.validation_status,
      }));

      if (annotatedImages.value.length > 0 && !selectedImageUrl.value) {
        selectedImageUrl.value = annotatedImages.value[annotatedImages.value.length - 1]!.imageUrl;
      }

      annotoriousIdToApiId.value = {};
    } catch (error) {
      console.error('Failed to load annotations:', error);
      const { Notify } = await import('quasar');
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToLoadAnnotations'),
      });
    } finally {
      loadingAnnotations.value = false;
    }
  }

  async function addImage(imageUrl: string) {
    const path = imageUrl.replace(`${baseUrl}/files/get/`, '');
    try {
      const response = await enqueueFetch(`${baseUrl}/annotations/annotated-images/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_path: path }),
      });
      if (!response.ok) {
        if (response.status === 409) {
          return;
        }
        throw new Error('Failed to add image');
      }
      const data = await response.json();

      const newImage: AnnotatedImage = {
        imageId: data.id,
        imageUrl: imageUrl,
        annotations: [],
        completionStatus: 'not_completed',
      };

      annotatedImages.value.push(newImage);
      if (!selectedImageUrl.value) {
        selectedImageUrl.value = imageUrl;
      }
    } catch (error) {
      console.error('Failed to add image:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToAddImage'),
      });
    }
  }

  async function removeImage(imageUrl: string) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    try {
      annotatedImages.value = annotatedImages.value.filter((img) => img.imageUrl !== imageUrl);
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}`,
        {
          method: 'DELETE',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to remove image');
      }
    } catch (error) {
      console.error('Failed to remove image:', error);
      annotatedImages.value.push(image);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToRemoveImage'),
      });
    }
  }

  function getAnnotationsForImage(imageUrl: string): Annotation[] {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    return image?.annotations ?? [];
  }

  async function addAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    const apiData = annotationToApi(annotation);
    try {
      const response = await enqueueFetch(`${baseUrl}/annotations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          annotated_image_id: image.imageId,
          polygon: apiData.polygon,
          damage_level: apiData.damage_level,
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to add annotation');
      }
      const data = await response.json();
      console.log(`Annotation ${data.id} added successfully`);

      image.annotations.push(annotation);
      annotoriousIdToApiId.value[annotation.id] = data.id.toString();

      if (image.completionStatus === 'completed') {
        Notify.create({
          type: 'warning',
          message: getI18nT()('completionMarkRemoved'),
        });
        await updateImageCompleted(imageUrl, 'not_completed');
      }

      return annotation;
    } catch (error) {
      console.error('Failed to add annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToAddAnnotation'),
      });
      return annotation;
    }
  }

  async function updateAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;
    console.log(`Updating annotation ${annotation.id} for image ${imageUrl}`);

    const index = image.annotations.findIndex((a) => a.id === annotation.id);
    if (index !== -1) {
      // Skip the backend call if nothing changed since the last update. The
      // pointer-up save and Annotorious' updateAnnotation event can both fire
      // for the same edit; this dedups them.
      if (annotationsEqual(image.annotations[index]!, annotation)) {
        return;
      }
      // Reflect the change locally before the (async) backend call.
      image.annotations[index] = annotation;
    }

    const apiData = annotationToApi(annotation);
    try {
      const response = await enqueueFetch(
        () =>
          `${baseUrl}/annotations/${annotoriousIdToApiId.value[annotation.id] || annotation.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiData),
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update annotation');
      }
      const annotationId = annotoriousIdToApiId.value[annotation.id] || annotation.id;
      console.log(`Annotation ${annotationId} updated successfully`);

      if (image.completionStatus === 'completed' && apiData.damage_level === 'unset') {
        Notify.create({
          type: 'warning',
          message: getI18nT()('completionMarkRemoved'),
        });
        await updateImageCompleted(imageUrl, 'not_completed');
      }
    } catch (error) {
      console.error('Failed to update annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateAnnotation'),
      });
    }
  }

  function circularizeAnnotation(imageUrl: string, annotationId: string): Annotation | undefined {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;

    const annotationIndex = image.annotations.findIndex((a) => a.id === annotationId);
    if (annotationIndex === -1) return;

    const annotation = image.annotations[annotationIndex]!;
    const points = annotation.target.selector.geometry.points;
    const n = points.length;
    const newPoints: Point[] = [];

    for (let i = 0; i < n; i++) {
      const pPrev = points[(i - 1 + n) % n]!;
      const pCurr = points[i]!;
      const pNext = points[(i + 1) % n]!;
      const pNextNext = points[(i + 2) % n]!;

      newPoints.push(pCurr);

      const edgeMid: Point = [(pCurr[0] + pNext[0]) / 2, (pCurr[1] + pNext[1]) / 2];

      let pointA: Point;
      const circle1 = circleFromThreePoints(pPrev, pCurr, pNext);
      if (circle1) {
        pointA = intersectBisectorAndCircle(pCurr, pNext, circle1.center, circle1.radius, edgeMid);
      } else {
        pointA = edgeMid;
      }

      let pointB: Point;
      const circle2 = circleFromThreePoints(pCurr, pNext, pNextNext);
      if (circle2) {
        pointB = intersectBisectorAndCircle(pCurr, pNext, circle2.center, circle2.radius, edgeMid);
      } else {
        pointB = edgeMid;
      }

      const midX = (pointA[0] + pointB[0]) / 2;
      const midY = (pointA[1] + pointB[1]) / 2;

      newPoints.push([midX, midY]);
    }

    const updatedAnnotation: Annotation = {
      ...annotation,
      target: {
        ...annotation.target,
        selector: {
          ...annotation.target.selector,
          geometry: {
            bounds: {
              minX: Math.min(...newPoints.map((p) => p[0])),
              maxX: Math.max(...newPoints.map((p) => p[0])),
              minY: Math.min(...newPoints.map((p) => p[1])),
              maxY: Math.max(...newPoints.map((p) => p[1])),
            },
            points: newPoints,
          },
        },
      },
    };

    return updatedAnnotation;
  }

  function orthogonalizeAnnotation(imageUrl: string, annotationId: string): Annotation | undefined {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;

    const annotationIndex = image.annotations.findIndex((a) => a.id === annotationId);
    if (annotationIndex === -1) return;

    const annotation = image.annotations[annotationIndex]!;
    const points = annotation.target.selector.geometry.points.map((p) => [...p]) as Point[];
    const n = points.length;
    if (n < 3) return;

    // Compute the overall orientation from each edge's orientation.
    // Quadruple the angles (after shifting to [0, 360)) so edges that are 90°
    // apart point in the same direction; averaging those directions as vectors
    // and dividing by 4 gives the dominant orientation without a modulo.
    let sumCos = 0;
    let sumSin = 0;
    for (let i = 0; i < n; i++) {
      const p1 = points[i]!;
      const p2 = points[(i + 1) % n]!;
      const dx = p2[0] - p1[0];
      const dy = p2[1] - p1[1];
      const angleDeg = (Math.atan2(dy, dx) * 180) / Math.PI;
      const quadrupled = (angleDeg + 180) * 4;
      const rad = (quadrupled * Math.PI) / 180;
      sumCos += Math.cos(rad);
      sumSin += Math.sin(rad);
    }
    const orientation = (Math.atan2(sumSin, sumCos) * 180) / Math.PI / 4;

    // Compute the centroid.
    const cx = points.reduce((sum, p) => sum + p[0], 0) / n;
    const cy = points.reduce((sum, p) => sum + p[1], 0) / n;

    // Shift centroid to the origin and rotate by the negative overall orientation.
    const theta = (-orientation * Math.PI) / 180;
    const cos = Math.cos(theta);
    const sin = Math.sin(theta);

    const rotatedPoints = points.map((p) => {
      const x = p[0] - cx;
      const y = p[1] - cy;
      return [x * cos - y * sin, x * sin + y * cos] as Point;
    });

    // Classify each edge as horizontal or vertical based on its slope.
    const edgeTypes: ('H' | 'V')[] = [];
    for (let i = 0; i < n; i++) {
      const p1 = rotatedPoints[i]!;
      const p2 = rotatedPoints[(i + 1) % n]!;
      const dx = p2[0] - p1[0];
      const dy = p2[1] - p1[1];
      const slope = dx === 0 ? Infinity : dy / dx;
      edgeTypes.push(Math.abs(slope) <= 1 ? 'H' : 'V');
    }

    // Orthogonalize the polygon in the rotated frame.
    // First pass: compute the mean coordinate for each edge (Y for horizontal,
    // X for vertical). Treating each shared vertex as belonging to both incident
    // edges lets us average their contributions instead of snapping one edge to
    // the other.
    const edgeMeans: number[] = [];
    for (let i = 0; i < n; i++) {
      const p1 = rotatedPoints[i]!;
      const p2 = rotatedPoints[(i + 1) % n]!;
      if (edgeTypes[i] === 'H') {
        edgeMeans.push((p1[1] + p2[1]) / 2);
      } else {
        edgeMeans.push((p1[0] + p2[0]) / 2);
      }
    }

    // Second pass: set each vertex coordinate from the mean(s) of its incident
    // edges. When both incident edges share an orientation, the vertex gets the
    // average of both edge means; otherwise it uses the single relevant mean.
    for (let i = 0; i < n; i++) {
      const prevType = i === 0 ? edgeTypes[n - 1] : edgeTypes[i - 1];
      const currType = edgeTypes[i]!;
      const vertex = rotatedPoints[i]!;

      if (currType === 'H' && prevType === 'H') {
        const prevMean = edgeMeans[i === 0 ? n - 1 : i - 1]!;
        const currMean = edgeMeans[i]!;
        vertex[1] = (prevMean + currMean) / 2;
      } else if (currType === 'H') {
        vertex[1] = edgeMeans[i]!;
      } else if (prevType === 'H') {
        vertex[1] = edgeMeans[i === 0 ? n - 1 : i - 1]!;
      }

      if (currType === 'V' && prevType === 'V') {
        const prevMean = edgeMeans[i === 0 ? n - 1 : i - 1]!;
        const currMean = edgeMeans[i]!;
        vertex[0] = (prevMean + currMean) / 2;
      } else if (currType === 'V') {
        vertex[0] = edgeMeans[i]!;
      } else if (prevType === 'V') {
        vertex[0] = edgeMeans[i === 0 ? n - 1 : i - 1]!;
      }
    }

    // If the first and last edges share an orientation, insert a new point at the
    // end to split the corner and avoid a mismatch when the polygon closes.
    if (edgeTypes[0] === edgeTypes[n - 1]) {
      if (edgeTypes[0] === 'H') {
        const firstMean = edgeMeans[0]!;
        rotatedPoints[0]![1] = firstMean;
        rotatedPoints.push([rotatedPoints[0]![0], rotatedPoints[n - 1]![1]] as Point);
      } else {
        const firstMean = edgeMeans[0]!;
        rotatedPoints[0]![0] = firstMean;
        rotatedPoints.push([rotatedPoints[n - 1]![0], rotatedPoints[0]![1]] as Point);
      }
    }

    // Recompute the new centroid in the rotated frame before translating back
    // to the original centroid location.
    const newCxRot = rotatedPoints.reduce((sum, p) => sum + p[0], 0) / rotatedPoints.length;
    const newCyRot = rotatedPoints.reduce((sum, p) => sum + p[1], 0) / rotatedPoints.length;

    // Rotate back.
    const backTheta = (orientation * Math.PI) / 180;
    const cosBack = Math.cos(backTheta);
    const sinBack = Math.sin(backTheta);

    const newCxBack = newCxRot * cosBack - newCyRot * sinBack;
    const newCyBack = newCxRot * sinBack + newCyRot * cosBack;

    const newPoints = rotatedPoints.map((p) => {
      const x = p[0] * cosBack - p[1] * sinBack;
      const y = p[0] * sinBack + p[1] * cosBack;
      return [x - newCxBack + cx, y - newCyBack + cy] as Point;
    });

    const updatedAnnotation: Annotation = {
      ...annotation,
      target: {
        ...annotation.target,
        selector: {
          ...annotation.target.selector,
          geometry: {
            bounds: {
              minX: Math.min(...newPoints.map((p) => p[0])),
              maxX: Math.max(...newPoints.map((p) => p[0])),
              minY: Math.min(...newPoints.map((p) => p[1])),
              maxY: Math.max(...newPoints.map((p) => p[1])),
            },
            points: newPoints,
          },
        },
      },
    };

    return updatedAnnotation;
  }

  async function deleteAnnotation(imageUrl: string, annotation: Annotation) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image) return;

    try {
      const response = await enqueueFetch(
        () =>
          `${baseUrl}/annotations/${annotoriousIdToApiId.value[annotation.id] || annotation.id}`,
        {
          method: 'DELETE',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to delete annotation');
      }
      const annotationId = annotoriousIdToApiId.value[annotation.id] || annotation.id;
      console.log(`Annotation ${annotationId} deleted successfully`);
      image.annotations = image.annotations.filter((a) => a.id !== annotation.id);
    } catch (error) {
      console.error('Failed to delete annotation:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToDeleteAnnotation'),
      });
    }
  }

  function setSelectedImageUrl(url: string | null) {
    selectedImageUrl.value = url;
  }

  async function addAnnotationsFromOverlap(imageUrl: string, overlap: Overlap | null) {
    if (!overlap) return;
    if (overlap.overlap_ratio < OVERLAP_RATIO_THRESHOLD) return;

    const sourceAnnotations = getAnnotationsForImage(`${baseUrl}/files/get/${overlap.image_path}`);
    if (sourceAnnotations.length === 0) return;

    const H = overlap.homography_matrix;
    const addAnnotationPromises: Promise<void>[] = [];

    for (const sourceAnnotation of sourceAnnotations) {
      const transformedPoints = sourceAnnotation.target.selector.geometry.points.map(
        (point: Point): Point => {
          const [x, y] = point;
          const x1 = H[0]![0]! * x + H[0]![1]! * y + H[0]![2]!;
          const y1 = H[1]![0]! * x + H[1]![1]! * y + H[1]![2]!;
          const w = H[2]![0]! * x + H[2]![1]! * y + H[2]![2]!;

          return [x1 / w, y1 / w];
        },
      );

      const bounds = {
        minX: Math.min(...transformedPoints.map((p) => p[0])),
        maxX: Math.max(...transformedPoints.map((p) => p[0])),
        minY: Math.min(...transformedPoints.map((p) => p[1])),
        maxY: Math.max(...transformedPoints.map((p) => p[1])),
      };

      if (
        bounds.maxX < 0 ||
        bounds.minX > overlap.resolution[0] ||
        bounds.maxY < 0 ||
        bounds.minY > overlap.resolution[1]
      ) {
        continue;
      }

      const newAnnotation: Annotation = {
        id: sourceAnnotation.id,
        bodies: sourceAnnotation.bodies,
        target: {
          ...sourceAnnotation.target,
          selector: {
            ...sourceAnnotation.target.selector,
            geometry: {
              bounds,
              points: transformedPoints,
            },
          },
        },
      };

      addAnnotationPromises.push(
        addAnnotation(imageUrl, newAnnotation)
          .then(() => {})
          .catch((error) => {
            console.error('Failed to add annotation from overlap:', error);
          }),
      );
    }

    try {
      await Promise.all(addAnnotationPromises);
      const t = getI18nT();
      Notify.create({
        message: t('annotationsCopied', { filename: overlap.image_path.split('/').slice(-1)[0] }),
      });
    } catch (error) {
      console.error('Failed to add annotations from overlap:', error);
    }
  }

  function setUserInfo(newUserInfo: AnnotationData['userInfo']) {
    userInfo.value = newUserInfo;
  }

  function clearAll() {
    userInfo.value = {
      fullName: '',
      email: '',
    };
    annotatedImages.value = [];
  }

  async function updateImageCompleted(imageUrl: string, status: CompletionStatus) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    try {
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completion_status: status }),
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update image completion status');
      }
      image.completionStatus = status;
    } catch (error) {
      console.error('Failed to update image completion status:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateCompleted'),
      });
    }
  }

  async function updateImageValidationStatus(imageUrl: string, status: ValidationStatus) {
    const image = annotatedImages.value.find((img) => img.imageUrl === imageUrl);
    if (!image || !image.imageId) return;

    const endpoint = status === 'approved' ? 'approve' : 'reject';
    try {
      const response = await enqueueFetch(
        `${baseUrl}/annotations/annotated-images/${image.imageId}/${endpoint}`,
        {
          method: 'POST',
        },
      );
      if (!response.ok) {
        throw new Error('Failed to update image validation status');
      }
      image.validationStatus = status;
    } catch (error) {
      console.error('Failed to update image validation status:', error);
      Notify.create({
        type: 'negative',
        message: getI18nT()('failedToUpdateValidationStatus'),
      });
    }
  }

  async function processFetchQueue() {
    if (processingQueue.value || fetchQueue.value.length === 0) {
      return;
    }
    processingQueue.value = true;

    while (fetchQueue.value.length > 0) {
      const run = fetchQueue.value[0]!;
      await run();
      fetchQueue.value.shift();
    }

    processingQueue.value = false;
  }

  function enqueueFetch(url: string | (() => string), options?: RequestInit): Promise<Response> {
    return new Promise((resolve, reject) => {
      fetchQueue.value.push(async () => {
        try {
          const resolvedUrl = typeof url === 'function' ? url() : url;
          const response = await authFetch(resolvedUrl, options);
          resolve(response);
        } catch (error) {
          reject(error instanceof Error ? error : new Error(String(error)));
        }
      });
      void processFetchQueue();
    });
  }

  function setNextImageForReview() {
    const currentIndex = annotatedImages.value.findIndex(
      (img) => img.imageUrl === selectedImageUrl.value,
    );
    // Find the next image with pending validation status after the current one
    for (let i = currentIndex + 1; i < annotatedImages.value.length; i++) {
      const img = annotatedImages.value[i]!;
      if (img.validationStatus === 'pending' || !img.validationStatus) {
        selectedImageUrl.value = img.imageUrl;
        return;
      }
    }
    // If no more pending images after current, check from the start
    for (let i = 0; i <= currentIndex; i++) {
      const img = annotatedImages.value[i]!;
      if (img.validationStatus === 'pending' || !img.validationStatus) {
        selectedImageUrl.value = img.imageUrl;
        return;
      }
    }
    // No pending images found
    Notify.create({
      type: 'info',
      message: getI18nT()('noMoreImagesToReview'),
    });
  }

  return {
    userInfo,
    annotatedImages,
    selectedImageUrl,
    overlapsLoading,
    annotoriousIdToApiId,
    fetchQueue,
    processingQueue,
    loadingAnnotations,
    imageCount,
    totalAnnotations,
    addingNewImage,
    overlapLoading,
    selectedImage,
    loadAnnotations,
    addImage,
    removeImage,
    getAnnotationsForImage,
    addAnnotation,
    updateAnnotation,
    circularizeAnnotation,
    orthogonalizeAnnotation,
    deleteAnnotation,
    setSelectedImageUrl,
    addAnnotationsFromOverlap,
    setUserInfo,
    clearAll,
    updateImageCompleted,
    updateImageValidationStatus,
    processFetchQueue,
    enqueueFetch,
    setNextImageForReview,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAnnotationDataStore, import.meta.hot));
}
