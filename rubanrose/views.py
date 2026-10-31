from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import VILLES_BENIN
from .models import Activite, Cagnotte, Organisation


def _organisations_publiques():
    """Organisations approuvées et actives, seules visibles du public."""
    return Organisation.objects.filter(
        statut_verification=Organisation.Statut.APPROUVEE,
        est_active=True,
    )


def _paginer(request, queryset, par_page=9):
    return Paginator(queryset, par_page).get_page(request.GET.get('page'))


def _querystring(request):
    """Paramètres GET sans 'page', pour conserver les filtres en paginant."""
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def accueil(request):
    maintenant = timezone.now()
    aujourdhui = timezone.localdate()
    organisations_publiques = _organisations_publiques()
    villes = VILLES_BENIN
    ville = request.GET.get('ville', '').strip()
    if ville not in villes:
        ville = ''

    organisations = organisations_publiques
    if ville:
        organisations = organisations.filter(ville=ville)

    activites = (
        Activite.objects.publiques()
        .filter(date_debut__gte=maintenant)
        .select_related('organisation')
        .order_by('date_debut')
    )
    cagnottes = (
        Cagnotte.objects.publiques()
        .filter(date_fin__gte=aujourdhui)
        .select_related('organisation')
        .order_by('-date_creation')
    )
    organisations = organisations.order_by('-date_inscription')

    contexte = {
        'organisations': organisations,
        'activites': activites,
        'cagnottes': cagnottes,
        'villes': villes,
        'ville_selectionnee': ville,
    }
    return render(request, 'rubanrose/accueil.html', contexte)


def presentation(request):
    return redirect(f"{reverse('rubanrose:accueil')}#presentation")


# --- Organisations --------------------------------------------------------
def liste_organisations(request):
    q = request.GET.get('q', '').strip()
    ville = request.GET.get('ville', '').strip()

    organisations = _organisations_publiques()
    if q:
        organisations = organisations.filter(
            Q(nom__icontains=q)
            | Q(description__icontains=q)
            | Q(zone_intervention__icontains=q)
        )
    if ville:
        organisations = organisations.filter(ville=ville)

    villes = (
        _organisations_publiques().order_by('ville')
        .values_list('ville', flat=True).distinct()
    )
    return render(request, 'rubanrose/organisation_liste.html', {
        'page_obj': _paginer(request, organisations),
        'querystring': _querystring(request),
        'q': q,
        'ville': ville,
        'villes': villes,
    })


def detail_organisation(request, slug):
    organisation = get_object_or_404(_organisations_publiques(), slug=slug)
    activites = (
        Activite.objects.publiques()
        .filter(organisation=organisation)
        .order_by('-date_debut')[:6]
    )
    cagnottes = Cagnotte.objects.publiques().filter(organisation=organisation)[:6]
    return render(request, 'rubanrose/organisation_detail.html', {
        'organisation': organisation,
        'activites': activites,
        'cagnottes': cagnottes,
    })


# --- Activités ------------------------------------------------------------
def liste_activites(request):
    q = request.GET.get('q', '').strip()
    categorie = request.GET.get('categorie', '').strip()
    periode = request.GET.get('periode', 'a_venir')
    maintenant = timezone.now()

    activites = Activite.objects.publiques().select_related('organisation')

    if periode == 'passees':
        activites = activites.filter(date_debut__lt=maintenant).order_by('-date_debut')
    elif periode == 'toutes':
        pass
    else:
        periode = 'a_venir'
        activites = activites.filter(date_debut__gte=maintenant)

    if categorie in dict(Activite.Categorie.choices):
        activites = activites.filter(categorie=categorie)
    else:
        categorie = ''

    if q:
        activites = activites.filter(
            Q(titre__icontains=q)
            | Q(description__icontains=q)
            | Q(lieu__icontains=q)
            | Q(organisation__nom__icontains=q)
        )

    return render(request, 'rubanrose/activite_liste.html', {
        'page_obj': _paginer(request, activites),
        'querystring': _querystring(request),
        'q': q,
        'categorie': categorie,
        'periode': periode,
        'categories': Activite.Categorie.choices,
    })


def detail_activite(request, slug):
    activite = get_object_or_404(
        Activite.objects.publiques().select_related('organisation'), slug=slug,
    )
    autres = (
        Activite.objects.publiques()
        .filter(organisation=activite.organisation)
        .exclude(pk=activite.pk)
        .order_by('-date_debut')[:3]
    )
    return render(request, 'rubanrose/activite_detail.html', {
        'activite': activite,
        'autres_activites': autres,
    })


# --- Cagnottes ------------------------------------------------------------
def liste_cagnottes(request):
    q = request.GET.get('q', '').strip()
    periode = request.GET.get('periode', 'toutes')
    aujourdhui = timezone.localdate()

    cagnottes = Cagnotte.objects.publiques().select_related('organisation')

    if periode == 'en_cours':
        cagnottes = cagnottes.filter(date_debut__lte=aujourdhui, date_fin__gte=aujourdhui)
    elif periode == 'terminees':
        cagnottes = cagnottes.filter(date_fin__lt=aujourdhui)
    else:
        periode = 'toutes'

    if q:
        cagnottes = cagnottes.filter(
            Q(titre__icontains=q)
            | Q(description__icontains=q)
            | Q(organisation__nom__icontains=q)
        )

    return render(request, 'rubanrose/cagnotte_liste.html', {
        'page_obj': _paginer(request, cagnottes),
        'querystring': _querystring(request),
        'q': q,
        'periode': periode,
    })


def detail_cagnotte(request, slug):
    cagnotte = get_object_or_404(
        Cagnotte.objects.publiques().select_related('organisation'), slug=slug,
    )
    return render(request, 'rubanrose/cagnotte_detail.html', {'cagnotte': cagnotte})
