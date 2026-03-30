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

export interface W3CPointSelector {
  type: 'PointSelector';
  x: number;
  y: number;
}

export interface W3CFragmentSelector {
  type: 'FragmentSelector';
  value: string;
  conformsTo: string;
}

export interface W3CAnnotationBody {
  type: 'TextualBody';
  value: string;
  format: 'text/plain';
  purpose: 'tagging';
}

export interface W3CAnnotationTarget {
  source: string;
  selector: W3CPointSelector[] | W3CFragmentSelector;
}

export interface W3CAnnotation {
  id: string;
  type: 'Annotation';
  body: W3CAnnotationBody | W3CAnnotationBody[];
  target: W3CAnnotationTarget | string;
}
