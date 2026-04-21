export interface UserInfo {
  firstName: string;
  lastName: string;
  email: string;
}

export type Point = [number, number];

export interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface Geometry {
  bounds: Bounds;
  points: Point[];
}

export interface Selector {
  type: 'POLYGON';
  geometry: Geometry;
}

export interface Creator {
  isGuest: boolean;
  id: string;
}

export interface Body {
  id?: string;
  purpose: string;
  value: string;
}

export interface Target {
  annotation: string;
  selector: Selector;
  creator: Creator;
  created: Date;
}

export interface Annotation {
  id: string;
  bodies: Body[];
  target: Target;
}

export interface AnnotatedImage {
  imageId: number | null;
  imageUrl: string;
  annotations: Annotation[];
  completed: boolean;
}

export interface AnnotationData {
  userInfo: UserInfo;
  annotatedImages: AnnotatedImage[];
}

export interface Overlap {
  image_path: string;
  homography_matrix: number[][];
  overlap_ratio: number;
  resolution: [number, number];
}

export interface ImageGPSLocation {
  latitude: number;
  longitude: number;
}

export type ValidationStatus = 'pending' | 'approved' | 'rejected';

export interface AnnotationRead {
  id: number;
  polygon: Point[];
  damage_level: number;
  annotated_image_id: number | null;
}

export interface AnnotatedImageRead {
  id: number;
  image_path: string;
  validation_status: ValidationStatus;
  completed: boolean;
  annotator_id: number | null;
  annotations: AnnotationRead[];
}
