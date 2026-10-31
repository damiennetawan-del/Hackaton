from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ActiviteForm, CagnotteForm, ConnexionForm, InscriptionOrganisationForm,
    OrganisationForm,
)
from .models import Activite, Cagnotte, Organisation


def organisation_requise(vue):
    """
    Réserve une vue aux utilisateurs connectés disposant d'une organisation.
    Passe l'organisation de l'utilisateur à la vue : une organisation ne
    peut donc jamais agir que sur ses propres données.
    """
    @wraps(vue)
    @login_required
    def enveloppe(request, *args, **kwargs):
        try:
            organisation = request.user.organisation
        except Organisation.DoesNotExist:
            if request.user.is_staff:
                messages.info(request, "Votre compte est un compte d'administration.")
                return redirect('admin:index')
            raise PermissionDenied
        return vue(request, organisation, *args, **kwargs)
    return enveloppe


class ConnexionView(LoginView):
    template_name = 'rubanrose/connexion.html'
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, 'Connexion réussie. Bienvenue !')
        return super().form_valid(form)


def inscription(request):
    if request.user.is_authenticated:
        return redirect('rubanrose:tableau_de_bord')

    if request.method == 'POST':
        form = InscriptionOrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            organisation = form.save()
            login(request, organisation.user)
            messages.success(
                request,
                "Votre organisation est inscrite. Elle est en attente de vérification "
                "par un administrateur : vous pourrez publier dès son approbation.",
            )
            return redirect('rubanrose:tableau_de_bord')
    else:
        form = InscriptionOrganisationForm()
    return render(request, 'rubanrose/inscription.html', {'form': form})


def acces_organisation(request):
    """Point d'entrée unique pour choisir la connexion ou l'inscription."""
    if request.user.is_authenticated:
        return redirect('rubanrose:tableau_de_bord')
    return render(request, 'rubanrose/acces_organisation.html')


@organisation_requise
def tableau_de_bord(request, organisation):
    activites = organisation.activites.order_by('-date_creation')
    cagnottes = organisation.cagnottes.order_by('-date_creation')
    return render(request, 'rubanrose/tableau_de_bord.html', {
        'organisation': organisation,
        'activites': activites[:5],
        'cagnottes': cagnottes[:5],
        'nb_activites': activites.count(),
        'nb_activites_publiees': activites.filter(statut=Activite.Statut.PUBLIEE).count(),
        'nb_cagnottes': cagnottes.count(),
        'nb_cagnottes_validees': cagnottes.filter(statut=Cagnotte.Statut.VALIDEE).count(),
    })


@organisation_requise
def liste_activites_espace(request, organisation):
    activites = organisation.activites.order_by('-date_creation')
    return render(request, 'rubanrose/espace_activites.html', {
        'organisation': organisation,
        'activites': activites,
    })


@organisation_requise
def creer_activite(request, organisation):
    if not organisation.peut_publier:
        messages.error(
            request,
            "Votre organisation doit être approuvée et active avant de proposer une activité.",
        )
        return redirect('rubanrose:tableau_de_bord')

    if request.method == 'POST':
        form = ActiviteForm(request.POST, request.FILES)
        if form.is_valid():
            activite = form.save(commit=False)
            activite.organisation = organisation
            activite.statut = Activite.Statut.EN_ATTENTE
            activite.motif_refus = ''
            activite.save()
            messages.success(request, "Votre activité a été envoyée pour validation.")
            return redirect('rubanrose:liste_activites_espace')
    else:
        form = ActiviteForm()
    return render(request, 'rubanrose/espace_activite_formulaire.html', {
        'form': form,
        'organisation': organisation,
        'titre_page': 'Proposer une activité',
    })


@organisation_requise
def modifier_activite(request, organisation, pk):
    # Le filtre propriétaire est appliqué avant tout accès à l'objet : un identifiant
    # appartenant à une autre organisation ne permet pas de lire ou modifier son activité.
    activite = get_object_or_404(organisation.activites, pk=pk)
    statut_initial = activite.statut

    if request.method == 'POST':
        form = ActiviteForm(request.POST, request.FILES, instance=activite)
        if form.is_valid():
            activite = form.save(commit=False)
            if statut_initial in (Activite.Statut.PUBLIEE, Activite.Statut.REFUSEE):
                activite.statut = Activite.Statut.EN_ATTENTE
                activite.motif_refus = ''
            activite.organisation = organisation
            activite.save()
            if statut_initial == Activite.Statut.PUBLIEE:
                messages.success(request, "Activité modifiée et renvoyée pour validation.")
            elif statut_initial == Activite.Statut.REFUSEE:
                messages.success(request, "Activité modifiée et soumise de nouveau à validation.")
            else:
                messages.success(request, "Votre activité a été mise à jour.")
            return redirect('rubanrose:liste_activites_espace')
    else:
        form = ActiviteForm(instance=activite)
    return render(request, 'rubanrose/espace_activite_formulaire.html', {
        'form': form,
        'organisation': organisation,
        'activite': activite,
        'titre_page': 'Modifier une activité',
    })


@organisation_requise
def liste_cagnottes_espace(request, organisation):
    cagnottes = organisation.cagnottes.order_by('-date_creation')
    return render(request, 'rubanrose/espace_cagnottes.html', {
        'organisation': organisation,
        'cagnottes': cagnottes,
    })


@organisation_requise
def creer_cagnotte(request, organisation):
    if not organisation.peut_publier:
        messages.error(
            request,
            "Votre organisation doit être approuvée et active avant de proposer une cagnotte.",
        )
        return redirect('rubanrose:tableau_de_bord')

    if request.method == 'POST':
        form = CagnotteForm(request.POST, request.FILES)
        if form.is_valid():
            cagnotte = form.save(commit=False)
            cagnotte.organisation = organisation
            cagnotte.statut = Cagnotte.Statut.EN_ATTENTE
            cagnotte.motif_refus = ''
            cagnotte.montant_collecte = None
            cagnotte.justificatif_collecte = ''
            cagnotte.save()
            messages.success(request, "Votre cagnotte a été envoyée pour validation.")
            return redirect('rubanrose:liste_cagnottes_espace')
    else:
        form = CagnotteForm()
    return render(request, 'rubanrose/espace_cagnotte_formulaire.html', {
        'form': form,
        'organisation': organisation,
        'titre_page': 'Proposer une cagnotte',
    })


@organisation_requise
def modifier_cagnotte(request, organisation, pk):
    # L'objet est recherché dans la relation de l'organisation connectée uniquement.
    cagnotte = get_object_or_404(organisation.cagnottes, pk=pk)
    statut_initial = cagnotte.statut

    if request.method == 'POST':
        form = CagnotteForm(request.POST, request.FILES, instance=cagnotte)
        if form.is_valid():
            cagnotte = form.save(commit=False)
            if statut_initial in (Cagnotte.Statut.VALIDEE, Cagnotte.Statut.REFUSEE):
                cagnotte.statut = Cagnotte.Statut.EN_ATTENTE
                cagnotte.motif_refus = ''
            cagnotte.organisation = organisation
            # Le formulaire n'expose jamais la collecte réelle ni son justificatif.
            cagnotte.save()
            if statut_initial == Cagnotte.Statut.VALIDEE:
                messages.success(request, "Cagnotte modifiée et renvoyée pour validation.")
            elif statut_initial == Cagnotte.Statut.REFUSEE:
                messages.success(request, "Cagnotte modifiée et soumise de nouveau à validation.")
            else:
                messages.success(request, "Votre cagnotte a été mise à jour.")
            return redirect('rubanrose:liste_cagnottes_espace')
    else:
        form = CagnotteForm(instance=cagnotte)
    return render(request, 'rubanrose/espace_cagnotte_formulaire.html', {
        'form': form,
        'organisation': organisation,
        'cagnotte': cagnotte,
        'titre_page': 'Modifier une cagnotte',
    })


@organisation_requise
def modifier_organisation(request, organisation):
    if request.method == 'POST':
        form = OrganisationForm(request.POST, request.FILES, instance=organisation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos informations ont été mises à jour.')
            return redirect('rubanrose:tableau_de_bord')
    else:
        form = OrganisationForm(instance=organisation)
    return render(request, 'rubanrose/organisation_modifier.html', {
        'form': form,
        'organisation': organisation,
    })
