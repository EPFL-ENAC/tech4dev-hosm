export default {
  appTitle: 'Annotation de jeux de données',

  import: 'Importer',
  export: 'Exporter',
  tutorial: 'Tutoriel',
  about: 'À propos',

  sidebarTitle: 'Images annotées',
  noImages: 'Aucune image pour le moment',
  annotateNew: 'Annoter nouvelle image',

  image: '0 image | 1 image | {n} images',
  annotation: '0 annotation | 1 annotation | {n} annotations',

  deleteImage: "Supprimer l'image",
  deleteImageMessage:
    'Êtes-vous sûr de vouloir supprimer cette image ? Cela supprimera également toutes les annotations liées à cette image. Cette action est irréversible.',
  deleteImageSkipMessage: 'Ne plus demander durant cette session',

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

  draw: 'Dessin',
  selectMove: 'Sélection/Déplacer',
  damageLevel: 'Niveau de dégats',
  delete: 'Supprimer',
  showReferenceMap: 'Montrer carte',
  recenter: 'Recentrer',
  hideReferenceMap: 'Cacher carte',
  captionDrawMode:
    'Clic : créer nouvelle annotation. Double-clic : placer dernier point. Clic + glisser : naviguer.',
  captionSelectMoveMode: 'Clic : sélectionner. Clic + glisser : déplacer.',
};
