export default {
  appTitle: 'Dataset annotation',

  import: 'Import',
  export: 'Export',
  tutorial: 'Tutorial',
  about: 'About',

  sidebarTitle: 'Annotated images',
  noImages: 'No images yet',
  markAsCompleted: 'Mark as completed',
  markAsIncomplete: 'Mark as incomplete',
  annotateNew: 'Annotate new',
  noImageSelected: 'No image selected',
  noImageSelectedMessage: 'Use the sidebar to add an image and start annotating.',

  image: '0 image | 1 image | {n} images',
  annotation: '0 annotation | 1 annotation | {n} annotations',

  deleteImage: 'Delete Image',
  deleteImageMessage:
    'Are you sure you want to delete this image? This will also delete all annotation data for this image. This action cannot be undone.',
  deleteImageSkipMessage: "Don't ask again during this session",
  deleteImageFailed: 'Failed to delete image',

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
  damageLevel_unset: 'Unset',
  damageLevel_undamaged: 'Undamaged',
  damageLevel_damaged: 'Damaged',
  delete: 'Delete',
  showReferenceMap: 'Show map',
  recenter: 'Recenter',
  hideReferenceMap: 'Hide map',
  changeSource: 'Change source',
  referenceMapUnavailable: 'Reference map unavailable',
  captionDrawMode:
    'Click to create a new annotation. Double-click to put last point. Click and drag to navigate.',
  captionSelectMoveMode: 'Click to select. Click and drag to move.',

  // Login page
  login: 'Login',
  logout: 'Logout',
  emailLabel: 'Email',
  emailRequired: 'Email is required',
  emailInvalid: 'Enter a valid email',
  fullNameLabel: 'Full Name',
  fullNameRequired: 'Full name is required',
  codeLabel: 'Code',
  codeRequired: 'Code is required',
  welcomeMessage: 'Welcome, {name}!',
  loginFailed: 'Login failed',
  emailExistsNameMismatch:
    'An account already exists with this email. Please enter the correct name.',

  // Review page
  reviewPage: 'Review Page',
  usersTableTitle: 'Users',
  userName: 'Name',
  userEmail: 'Email',
  userRole: 'Role',
  userAccountCreated: 'Account Created',
  annotatedImages: 'Annotated Images',
  totalAnnotations: 'Total Annotations',
  roleAnnotator: 'Annotator',
  roleReviewer: 'Reviewer',
  noUsersFound: 'No users found',
  errorLoadingUsers: 'Error loading users',
  refresh: 'Refresh',

  // 404 page
  notFoundMessage: 'Oops, nothing here...',
  goHome: 'Go Home',

  // Export dialog
  exportAnnotations: 'Export Annotations',

  // Annotation errors (map + store)
  selectAnnotationToEnable: 'Select an annotation to enable',
  errorLoadingImageTitle: 'Error Loading Image',
  errorLoadingImageMessage: 'Failed to load the image. Please try selecting a different image.',
  failedToAddAnnotation: 'Failed to add annotation',
  failedToUpdateAnnotation: 'Failed to update annotation',
  failedToDeleteAnnotation: 'Failed to delete annotation',
  failedToUpdateDamageLevel: 'Failed to update damage level',
  failedToLoadAnnotations: 'Failed to load annotations',
  failedToAddImage: 'Failed to add image',
  failedToRemoveImage: 'Failed to remove image',
  failedToUpdateCompleted: 'Failed to update image completed status',
};
