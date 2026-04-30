export interface UserInfo {
  fullName: string;
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
  validationStatus?: ValidationStatus;
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

export type DamageLevel = 'unset' | 'undamaged' | 'damaged';

export interface AnnotationRead {
  id: number;
  polygon: Point[];
  damage_level: DamageLevel;
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

export interface UserReadWithStats {
  id: number;
  email: string;
  full_name: string;
  is_reviewer: boolean;
  created_at: string;
  last_action_at: string | null;
  annotated_images_count: number;
  non_reviewed_images_count: number;
  total_annotations_count: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
