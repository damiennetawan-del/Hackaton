from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


def generer_slug_unique(instance, valeur):
    """Génère un slug unique pour le modèle de l'instance."""
    base = slugify(valeur)[:50] or 'element'
    slug = base
    compteur = 2
    modele = instance.__class__
    while modele.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f'{base}-{compteur}'
        compteur += 1
    return slug


# ---------------------------------------------------------------------------
# Organisation
# ---------------------------------------------------------------------------
class Organisation(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente de vérification'
        APPROUVEE = 'APPROUVEE', 'Approuvée'
        REFUSEE = 'REFUSEE', 'Refusée'

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='organisation',
        verbose_name='compte utilisateur',
    )
    nom = models.CharField('nom', max_length=150, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True, editable=False)
    description = models.TextField('description')
    logo = models.ImageField('logo', upload_to='logos/', blank=True, null=True)
    zone_intervention = models.CharField(
        "adresse ou zone d'intervention", max_length=255,
    )
    ville = models.CharField('ville', max_length=100)
    email_public = models.EmailField('e-mail public')
    telephone_public = models.CharField('téléphone public', max_length=30, blank=True)
    site_web = models.URLField('site web', blank=True)
    date_inscription = models.DateTimeField("date d'inscription", auto_now_add=True)
    statut_verification = models.CharField(
        'statut de vérification', max_length=12,
        choices=Statut.choices, default=Statut.EN_ATTENTE,
    )
    motif_refus = models.TextField('motif du refus', blank=True)
    est_active = models.BooleanField('active', default=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'organisation'
        verbose_name_plural = 'organisations'

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generer_slug_unique(self, self.nom)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('rubanrose:detail_organisation', kwargs={'slug': self.slug})

    @property
    def est_approuvee(self):
        return self.statut_verification == self.Statut.APPROUVEE

    @property
    def peut_publier(self):
        """Une organisation ne peut publier que si elle est approuvée ET active."""
        return self.est_approuvee and self.est_active


# ---------------------------------------------------------------------------
# Activité
# ---------------------------------------------------------------------------
class ActiviteQuerySet(models.QuerySet):
    def publiques(self):
        """Activités visibles par le grand public."""
        return self.filter(
            statut=Activite.Statut.PUBLIEE,
            organisation__statut_verification=Organisation.Statut.APPROUVEE,
            organisation__est_active=True,
        )


class Activite(models.Model):
    class Categorie(models.TextChoices):
        SENSIBILISATION = 'SENSIBILISATION', 'Sensibilisation'
        DEPISTAGE = 'DEPISTAGE', 'Dépistage'
        CONFERENCE = 'CONFERENCE', 'Conférence'
        ACCOMPAGNEMENT = 'ACCOMPAGNEMENT', 'Accompagnement'
        COLLECTE = 'COLLECTE', 'Collecte solidaire'
        AUTRE = 'AUTRE', 'Autre initiative'

    class Statut(models.TextChoices):
        BROUILLON = 'BROUILLON', 'Brouillon'
        EN_ATTENTE = 'EN_ATTENTE', 'En attente de validation'
        PUBLIEE = 'PUBLIEE', 'Publiée'
        REFUSEE = 'REFUSEE', 'Refusée'

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name='activites',
        verbose_name='organisation responsable',
    )
    titre = models.CharField('titre', max_length=200)
    slug = models.SlugField(max_length=60, unique=True, blank=True, editable=False)
    description = models.TextField('description')
    categorie = models.CharField(
        'catégorie', max_length=20, choices=Categorie.choices,
        default=Categorie.SENSIBILISATION,
    )
    image = models.ImageField('image ou affiche', upload_to='activites/', blank=True, null=True)
    lieu = models.CharField('lieu', max_length=255)
    date_debut = models.DateTimeField('date de début')
    date_fin = models.DateTimeField('date de fin', blank=True, null=True)
    statut = models.CharField(
        'statut de publication', max_length=12,
        choices=Statut.choices, default=Statut.EN_ATTENTE,
    )
    motif_refus = models.TextField('motif du refus', blank=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)
    date_modification = models.DateTimeField('dernière modification', auto_now=True)

    objects = ActiviteQuerySet.as_manager()

    class Meta:
        ordering = ['date_debut']
        verbose_name = 'activité'
        verbose_name_plural = 'activités'

    def __str__(self):
        return self.titre

    def clean(self):
        super().clean()
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError(
                {'date_fin': 'La date de fin doit être postérieure à la date de début.'}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generer_slug_unique(self, self.titre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('rubanrose:detail_activite', kwargs={'slug': self.slug})

    @property
    def est_a_venir(self):
        return self.date_debut >= timezone.now()


# ---------------------------------------------------------------------------
# Cagnotte solidaire
# ---------------------------------------------------------------------------
class CagnotteQuerySet(models.QuerySet):
    def publiques(self):
        """Cagnottes visibles par le grand public."""
        return self.filter(
            statut=Cagnotte.Statut.VALIDEE,
            organisation__statut_verification=Organisation.Statut.APPROUVEE,
            organisation__est_active=True,
        )


class Cagnotte(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente de validation'
        VALIDEE = 'VALIDEE', 'Validée'
        REFUSEE = 'REFUSEE', 'Refusée'

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name='cagnottes',
        verbose_name='organisation responsable',
    )
    titre = models.CharField('titre', max_length=200)
    slug = models.SlugField(max_length=60, unique=True, blank=True, editable=False)
    description = models.TextField('description')
    objectif_financier = models.DecimalField(
        'objectif financier (FCFA)', max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal('1'))],
    )
    # Reste vide (NULL) tant qu'aucune collecte réelle et vérifiable n'existe.
    montant_collecte = models.DecimalField(
        'montant collecté (FCFA)', max_digits=12, decimal_places=0,
        blank=True, null=True, validators=[MinValueValidator(Decimal('0'))],
        help_text='À renseigner uniquement si une collecte réelle et vérifiable existe.',
    )
    justificatif_collecte = models.TextField(
        'justificatif de la collecte', blank=True,
        help_text="Indiquer comment le montant collecté peut être vérifié.",
    )
    date_debut = models.DateField('date de début')
    date_fin = models.DateField('date de fin')
    image = models.ImageField('image', upload_to='cagnottes/', blank=True, null=True)
    informations_transparence = models.TextField(
        'informations de transparence',
        help_text="Utilisation prévue des fonds, responsables, modalités de suivi et de compte rendu.",
    )
    statut = models.CharField(
        'statut de validation', max_length=12,
        choices=Statut.choices, default=Statut.EN_ATTENTE,
    )
    motif_refus = models.TextField('motif du refus', blank=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    objects = CagnotteQuerySet.as_manager()

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'cagnotte solidaire'
        verbose_name_plural = 'cagnottes solidaires'

    def __str__(self):
        return self.titre

    def clean(self):
        super().clean()
        erreurs = {}
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            erreurs['date_fin'] = 'La date de fin doit être postérieure à la date de début.'
        if self.montant_collecte is not None and not self.justificatif_collecte.strip():
            erreurs['justificatif_collecte'] = (
                'Un justificatif est obligatoire lorsqu\'un montant collecté est renseigné.'
            )
        if erreurs:
            raise ValidationError(erreurs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generer_slug_unique(self, self.titre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('rubanrose:detail_cagnotte', kwargs={'slug': self.slug})

    @property
    def paiements_disponibles(self):
        """Vrai uniquement si un prestataire de paiement réel a été intégré."""
        return getattr(settings, 'PAIEMENTS_ACTIVES', False)

    @property
    def pourcentage_collecte(self):
        """None si aucun montant vérifiable n'est renseigné."""
        if self.montant_collecte is None or not self.objectif_financier:
            return None
        return min(int(self.montant_collecte * 100 / self.objectif_financier), 100)

    @property
    def est_en_cours(self):
        aujourdhui = timezone.localdate()
        return self.date_debut <= aujourdhui <= self.date_fin