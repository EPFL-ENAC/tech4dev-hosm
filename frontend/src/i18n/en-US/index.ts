export default {
  appTitle: 'Dataset annotation',

  import: 'Import',
  export: 'Export',
  tutorial: 'Tutorial',
  about: 'About',

  sidebarTitle: 'Annotated images',
  noImages: 'No images yet',
  annotateNew: 'Annotate new',

  image: '0 image | 1 image | {n} images',
  annotation: '0 annotation | 1 annotation | {n} annotations',

  deleteImage: 'Delete Image',
  deleteImageMessage:
    'Are you sure you want to delete this image? This will also delete all annotation data for this image. This action cannot be undone.',
  deleteImageSkipMessage: "Don't ask again during this session",

  noMoreImages: 'No more images available to annotate.',
  annotationsCopied: 'Copied annotations from {filename}.',

  tutorialTitle: 'Tutorial',
  tutorialSteps: [
    'Get a new image to annotate by clicking the "Annotate New" button in the sidebar.',
    'Use the "Draw" mode to add bounding polygons around buildings, then set a damage level.',
    'Use the "Select/Move" mode to adjust existing annotations.',
    'Use the "Export" button to download your annotations as a JSON file.',
  ],
  finish: 'Finish',
  close: 'Close',

  aboutTitle: 'About',

  draw: 'Draw',
  selectMove: 'Select/Move',
  damageLevel: 'Damage level',
  delete: 'Delete',
  showReferenceMap: 'Show map',
  recenter: 'Recenter',
  hideReferenceMap: 'Hide map',
  captionDrawMode:
    'Click to create a new annotation. Double-click to put last point. Click and drag to navigate.',
  captionSelectMoveMode: 'Click to select. Click and drag to move.',
};
