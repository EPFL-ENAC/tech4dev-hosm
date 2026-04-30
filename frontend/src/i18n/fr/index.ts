export default {
  appTitle: 'Annotation de jeux de données',

  import: 'Importer',
  export: 'Exporter',
  tutorial: 'Tutoriel',
  about: 'À propos',

  sidebarTitle: 'Images annotées',
  noImages: 'Aucune image pour le moment',
  markAsCompleted: 'Marquer comme terminé',
  markAsIncomplete: 'Marquer comme non terminé',
  annotateNew: 'Annoter nouvelle image',
  noImageSelected: 'Aucune image sélectionnée',
  noImageSelectedMessage:
    'Utilisez la barre latérale pour ajouter une image et commencer à annoter.',

  image: '0 image | 1 image | {n} images',
  annotation: '0 annotation | 1 annotation | {n} annotations',

  deleteImage: "Supprimer l'image",
  deleteImageMessage:
    'Êtes-vous sûr de vouloir supprimer cette image ? Cela supprimera également toutes les annotations liées à cette image. Cette action est irréversible.',
  deleteImageSkipMessage: 'Ne plus demander durant cette session',
  deleteImageFailed: "Échec de suppression de l'image",

  noMoreImages: 'Aucune image supplémentaire disponible pour annotation.',
  annotationsCopied: 'Annotations copiées depuis {filename}.',

  tutorialTitle: 'Tutoriel',
  tutorialSteps: [
    'Obtenez une nouvelle image à annoter en cliquant sur le bouton "Annoter nouvelle image" dans la barre latérale.',
    'Utilisez le mode "Dessin" pour ajouter des polygones délimitant les bâtiments, puis définissez un niveau de dégats.',
    'Utilisez le mode "Sélection/Déplacer" pour ajuster les annotations existantes.',
    'Utilisez le bouton "Exporter" pour télécharger vos annotations sous forme de fichier JSON.',
  ],
  finish: 'Terminer',
  close: 'Fermer',

  aboutTitle: 'À propos',
  aboutJointEffort:
    "Cette interface est le fruit d'un travail commun entre la Humanitarian OpenStreetMap Team (HOT), NAXA, et l'EPFL.",
  aboutDevelopment: 'Le développement a été réalisé par {link}.',
  aboutRepository: 'Dépôt : {link}',

  draw: 'Dessin',
  selectMove: 'Sélection/Déplacer',
  damageLevel: 'Niveau de dégats',
  damageLevel_unset: 'Non défini',
  damageLevel_undamaged: 'Non endommagé',
  damageLevel_damaged: 'Endommagé',
  delete: 'Supprimer',
  showReferenceMap: 'Montrer carte',
  recenter: 'Recentrer',
  hideReferenceMap: 'Cacher carte',
  changeSource: 'Changer source',
  referenceMapUnavailable: 'Carte de référence indisponible',
  captionDrawMode:
    'Clic : créer nouvelle annotation. Double-clic : placer dernier point. Clic + glisser : naviguer.',
  captionSelectMoveMode: 'Clic : sélectionner. Clic + glisser : déplacer.',

  // Login page
  login: 'Connexion',
  logout: 'Déconnexion',
  emailLabel: 'Adresse e-mail',
  emailRequired: "L'adresse e-mail est requise",
  emailInvalid: 'Entrez une adresse e-mail valide',
  fullNameLabel: 'Nom complet',
  fullNameRequired: 'Le nom complet est requis',
  codeLabel: 'Code',
  codeRequired: 'Le code est requis',
  welcomeMessage: 'Bienvenue, {name} !',
  loginFailed: 'Échec de la connexion',
  emailExistsNameMismatch: 'Un compte existe déjà avec cet e-mail. Veuillez saisir le nom correct.',

  // Admin page
  adminPageTitle: 'Tableau de bord',
  usersTableTitle: 'Utilisateurs',
  userName: 'Nom',
  userEmail: 'E-mail',
  userRole: 'Rôle',
  userAccountCreated: 'Compte créé',
  userLastAction: 'Dernière action',
  lastActionNow: 'maintenant',
  lastActionMinutesAgo: 'il y a {minutes}min',
  lastActionHoursAgo: 'il y a {hours}h',
  lastActionDaysAgo: 'il y a {days}j.',
  never: 'Jamais',
  annotatedImages: 'Images annotées',
  nonReviewedImages: 'Images non-évaluées',
  totalAnnotations: 'Annotations totales',
  roleAnnotator: 'Annotateur',
  roleReviewer: 'Évaluateur',
  noUsersFound: 'Aucun utilisateur trouvé',
  errorLoadingUsers: 'Erreur de chargement des utilisateurs',
  refresh: 'Actualiser',
  page: 'Page',
  of: 'sur',
  itemsPerPage: 'Éléments par page',
  review: 'Évaluer',

  // Review page
  reviewPageTitle: 'Évaluation des annotations',
  backToAdminPage: 'Page admin',
  validate: 'Valider',
  reject: 'Rejeter',
  nextImage: 'Image suivante',
  noMoreImagesToReview: 'Aucune image supplémentaire à évaluer.',

  // 404 page
  notFoundMessage: 'Oups, rien à voir ici...',
  goHome: 'Accueil',

  // Export dialog
  exportAnnotations: 'Exporter les annotations',

  // Annotation errors (map + store)
  selectAnnotationToEnable: 'Sélectionnez une annotation pour activer',
  errorLoadingImageTitle: "Erreur de chargement de l'image",
  errorLoadingImageMessage:
    "Impossible de charger l'image. Veuillez essayer de sélectionner une autre image.",
  failedToAddAnnotation: "Échec de l'ajout de l'annotation",
  failedToUpdateAnnotation: "Échec de la mise à jour de l'annotation",
  failedToDeleteAnnotation: "Échec de la suppression de l'annotation",
  failedToUpdateDamageLevel: 'Échec de la mise à jour du niveau de dégats',
  failedToLoadAnnotations: 'Échec du chargement des annotations',
  failedToAddImage: "Échec de l'ajout de l'image",
  failedToRemoveImage: "Échec de la suppression de l'image",
  failedToUpdateCompleted: "Échec de la mise à jour du statut de l'image",
  failedToUpdateValidationStatus: "Échec de la mise à jour du statut de validation de l'image",
};
