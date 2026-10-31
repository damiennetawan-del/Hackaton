import re
import unicodedata

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from .models import Activite, Cagnotte, Organisation

TAILLE_MAX_LOGO = 2 * 1024 * 1024  # 2 Mo
TAILLE_MAX_IMAGE_ACTIVITE = 5 * 1024 * 1024  # 5 Mo
AUTRE_VILLE = 'Autre ville'


def _cle_tri(texte):
    """Tri alphabétique sans tenir compte des accents."""
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode().lower()


VILLES_BENIN = sorted({
    'Cotonou', 'Porto-Novo', 'Parakou', 'Abomey-Calavi', 'Djougou', 'Bohicon',
    'Natitingou', 'Lokossa', 'Ouidah', 'Abomey', 'Kandi', 'Savè', 'Malanville',
    'Pobè', 'Dogbo', 'Sèmè-Podji', 'Allada', 'Comé', 'Aplahoué', 'Dassa-Zoumè',
    'Savalou', 'Tanguiéta', 'Nikki', 'Kétou', 'Sakété', 'Grand-Popo', 'Covè',
    'Zagnanado', 'Banikoara', 'Ouèssè', 'Bembèrèkè', 'Kouandé', 'Péhunco',
    'Cobly', 'Boukoumbé', 'Kérou', 'Glazoué', 'Tchaourou', 'Adjarra', 'Avrankou',
    'Ifangni', 'Adjohoun', 'Dangbo', 'Bonou', 'Zè', 'Toffo', 'Tori-Bossito',
    'Kpomassè', 'Sô-Ava', 'Athiémé', 'Bopa', 'Houéyogbé', 'Lalo', 'Djakotomey',
    'Klouékanmè', 'Toviklin', 'Adja-Ouèrè', 'Ouaké', 'Copargo', 'Ségbana',
    'Gogounou', 'Karimama', 'Matéri', 'Toucountouna', 'Kalalé', 'Pèrèrè',
}, key=_cle_tri)


def choix_villes(ville_actuelle=None):
    """Liste de choix des villes. Conserve une ville déjà enregistrée même si elle n'est pas dans la liste."""
    villes = list(VILLES_BENIN)
    if ville_actuelle and ville_actuelle not in villes and ville_actuelle != AUTRE_VILLE:
        villes.append(ville_actuelle)
    return (
        [('', 'Choisir une ville…')]
        + [(v, v) for v in villes]
        + [(AUTRE_VILLE, AUTRE_VILLE)]
    )


class BootstrapFormMixin:
    """Ajoute les classes Bootstrap aux champs et marque les champs en erreur."""

    def appliquer_style(self):
        for champ in self.fields.values():
            widget = champ.widget
            classe = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
            widget.attrs['class'] = (widget.attrs.get('class', '') + ' ' + classe).strip()

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for nom in self.errors:
                if nom in self.fields:
                    widget = self.fields[nom].widget
                    widget.attrs['class'] = (widget.attrs.get('class', '') + ' is-invalid').strip()


class ConnexionForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Nom d'utilisateur"
        self.fields['password'].label = 'Mot de passe'
        self.fields['username'].widget.attrs.update({'autofocus': True, 'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'autocomplete': 'current-password'})
        self.appliquer_style()


class OrganisationForm(BootstrapFormMixin, forms.ModelForm):
    """Informations modifiables d'une organisation (jamais le statut de vérification)."""

    ville = forms.ChoiceField(label='Ville')

    class Meta:
        model = Organisation
        fields = [
            'nom', 'ville', 'zone_intervention', 'description', 'logo',
            'email_public', 'telephone_public', 'site_web',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'logo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        help_texts = {
            'logo': 'Image JPG ou PNG, 2 Mo maximum (facultatif).',
            'zone_intervention': "Quartiers, communes ou départements où vous intervenez.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ville_actuelle = self.instance.ville if self.instance and self.instance.pk else None
        self.fields['ville'].choices = choix_villes(ville_actuelle)
        self.appliquer_style()

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if isinstance(logo, UploadedFile) and logo.size > TAILLE_MAX_LOGO:
            raise ValidationError('Le logo ne doit pas dépasser 2 Mo.')
        return logo

    def clean_telephone_public(self):
        telephone = self.cleaned_data.get('telephone_public', '').strip()
        if telephone and not re.fullmatch(r'[0-9+()\s.\-]{8,20}', telephone):
            raise ValidationError('Numéro de téléphone invalide.')
        return telephone


class ActiviteForm(BootstrapFormMixin, forms.ModelForm):
    """Champs qu'une organisation peut modifier sans toucher à la validation."""

    class Meta:
        model = Activite
        fields = ['titre', 'description', 'categorie', 'image', 'lieu', 'date_debut', 'date_fin']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'date_debut': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'},
            ),
            'date_fin': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'},
            ),
        }
        help_texts = {
            'image': 'Affiche au format image, 5 Mo maximum (facultative).',
            'date_fin': 'Facultative. Doit être postérieure à la date de début.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_debut'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['date_fin'].input_formats = ['%Y-%m-%dT%H:%M']
        self.appliquer_style()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if isinstance(image, UploadedFile) and image.size > TAILLE_MAX_IMAGE_ACTIVITE:
            raise ValidationError("L'affiche ne doit pas dépasser 5 Mo.")
        return image


class CagnotteForm(BootstrapFormMixin, forms.ModelForm):
    """Champs de proposition, sans montant collecté ni statut modifiable."""

    class Meta:
        model = Cagnotte
        fields = [
            'titre', 'description', 'objectif_financier', 'date_debut', 'date_fin',
            'image', 'informations_transparence',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'informations_transparence': forms.Textarea(attrs={'rows': 4}),
            'date_debut': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'date_fin': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
        help_texts = {
            'objectif_financier': 'Objectif annoncé en FCFA. Aucun paiement en ligne ne sera effectué.',
            'date_fin': 'La date de fin doit être égale ou postérieure à la date de début.',
            'image': 'Image au format JPG ou PNG, 5 Mo maximum (facultative).',
            'informations_transparence': 'Précisez l’utilisation prévue des fonds et les modalités de suivi et de compte rendu.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_debut'].input_formats = ['%Y-%m-%d']
        self.fields['date_fin'].input_formats = ['%Y-%m-%d']
        self.appliquer_style()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if isinstance(image, UploadedFile) and image.size > TAILLE_MAX_IMAGE_ACTIVITE:
            raise ValidationError("L'image ne doit pas dépasser 5 Mo.")
        return image


class InscriptionOrganisationForm(OrganisationForm):
    """Création du compte utilisateur et de l'organisation (en attente de vérification)."""

    username = forms.CharField(
        label="Nom d'utilisateur", max_length=150,
        validators=[User.username_validator],
        help_text='Lettres, chiffres et @/./+/-/_ uniquement.',
    )
    email = forms.EmailField(label='E-mail de connexion')
    password1 = forms.CharField(
        label='Mot de passe', strip=False, widget=forms.PasswordInput,
        help_text='8 caractères minimum, ni trop simple, ni uniquement numérique.',
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe', strip=False, widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Un compte existe déjà avec cette adresse e-mail.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Les deux mots de passe ne correspondent pas.')
        elif p1:
            utilisateur_temporaire = User(
                username=cleaned.get('username', ''), email=cleaned.get('email', ''),
            )
            try:
                password_validation.validate_password(p1, user=utilisateur_temporaire)
            except ValidationError as erreur:
                self.add_error('password1', erreur)
        return cleaned

    @transaction.atomic
    def save(self):
        utilisateur = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
        )
        organisation = super().save(commit=False)
        organisation.user = utilisateur
        # Toute nouvelle organisation est en attente : jamais choisi par le formulaire.
        organisation.statut_verification = Organisation.Statut.EN_ATTENTE
        organisation.est_active = True
        organisation.save()
        return organisation
