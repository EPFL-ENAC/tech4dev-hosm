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
  completionMarkRemoved: 'Completion mark removed',
  ensureNoUnsetDamage: 'Make sure all annotations have a damage level set',
  ensureAllBuildingsAnnotated: 'Make sure all buildings are annotated',
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

  skip: 'Skip',
  tutorialTitle: 'Tutorial',
  tutorialSteps: [
    'Click "Annotate new" in the sidebar to get a new image to annotate.',
    'Click "Add annotation" or press the [N] key to add a new annotation.',
    "Click to start drawing a polygon around buildings and add points. Double-click to finalize. <b>Include facades, and don't worry about parts outside the image.</b>",
    'Click to set the damage level, or use the [1] and [2] keys. <b>Multiple buildings sharing the same damage level can be enclosed in a single polygon.</b>',
    'Click "Show map" to display a reference map. Make sure to orient it correctly.',
    'Mark as completed once all buildings have been annotated and the damage levels set, or if there are no buildings on the image.',
  ],
  next: 'Next',
  finish: 'Finish',

  aboutTitle: 'About',
  aboutJointEffort:
    'This interface is a joint effort between the Humanitarian OpenStreetMap Team (HOT), NAXA, and EPFL.',
  aboutDevelopment: 'The development was carried out by {link}.',
  aboutRepository: 'Repository: {link}',

  addAnnotation: 'Add annotation',
  abort: 'Abort',
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
    'Click to start new annotation and add points. [Ctrl+Z] to remove one point. Double-click to put last point. Clic and drag to move. [Esc] to abort.',
  captionSelectMoveMode: 'Click to select. Click and drag to move. [N] to add new annotation.',
  captionDelete: '[Delete] to delete selected. [1], [2], [3] to set damage level.',
  escKey: 'Esc',
  deleteKey: 'Delete',

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

  // Admin page
  adminPageTitle: 'Admin Dashboard',
  usersTableTitle: 'Users',
  userName: 'Name',
  userEmail: 'Email',
  userRole: 'Role',
  userAccountCreated: 'Account Created',
  userLastAction: 'Last Action',
  lastActionNow: 'now',
  lastActionMinutesAgo: '{minutes}min ago',
  lastActionHoursAgo: '{hours}h ago',
  lastActionDaysAgo: '{days}d. ago',
  never: 'Never',
  annotatedImages: 'Annotated Images',
  nonReviewedImages: 'Non-reviewed images',
  totalAnnotations: 'Total Annotations',
  roleAnnotator: 'Annotator',
  roleReviewer: 'Reviewer',
  noUsersFound: 'No users found',
  errorLoadingUsers: 'Error loading users',
  refresh: 'Refresh',
  page: 'Page',
  of: 'of',
  itemsPerPage: 'Items per page',
  review: 'Review',
  toAnnotationPage: 'Annotation Interface',

  // Review page
  reviewPageTitle: 'Annotations Review',
  backToAdminPage: 'Admin Page',
  validate: 'Validate',
  reject: 'Reject',
  nextImage: 'Next image',
  noMoreImagesToReview: 'No more images to review.',

  // 404 page
  notFoundMessage: 'Oops, nothing here...',
  goHome: 'Go Home',

  // Table header tooltips
  tooltipImageName: 'Name of the image',
  tooltipAnnotationsCount: 'Number of annotations',
  tooltipCompletionStatus: 'Completion status',
  tooltipValidationStatus: 'Validation status',

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
  failedToUpdateValidationStatus: 'Failed to update image validation status',
};
