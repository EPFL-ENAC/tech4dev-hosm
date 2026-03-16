export interface UserInfo {
  firstName: string;
  lastName: string;
  email: string;
}

export interface Point {
  x: number;
  y: number;
}

export interface Polygon {
  points: Point[];
}

export type DamageLevel = 0 | 1 | 2 | 3;

export interface Annotation {
  polygon: Polygon;
  damageLevel: DamageLevel;
}

export interface AnnotatedImage {
  imageUrl: string;
  annotations: Annotation[];
}

export interface AnnotationData {
  userInfo: UserInfo;
  annotatedImages: AnnotatedImage[];
}
