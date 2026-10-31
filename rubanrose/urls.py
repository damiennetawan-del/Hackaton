from django.conf import settings
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import TemplateView

from . import views, views_espace

app_name = 'rubanrose'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('presentation/', views.presentation, name='presentation'),
    path('organisations/', views.liste_organisations, name='liste_organisations'),
    path('organisations/<slug:slug>/', views.detail_organisation, name='detail_organisation'),

    path('activites/', views.liste_activites, name='liste_activites'),
    path('activites/<slug:slug>/', views.detail_activite, name='detail_activite'),

    path('cagnottes/', views.liste_cagnottes, name='liste_cagnottes'),
    path('cagnottes/<slug:slug>/', views.detail_cagnotte, name='detail_cagnotte'),

    # Authentification et espace privé des organisations
    path('espace-organisation/', views_espace.acces_organisation, name='acces_organisation'),
    path('inscription/', views_espace.inscription, name='inscription'),
    path('connexion/', views_espace.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', LogoutView.as_view(), name='deconnexion'),
    path('mon-espace/', views_espace.tableau_de_bord, name='tableau_de_bord'),
    path('mon-espace/organisation/', views_espace.modifier_organisation, name='modifier_organisation'),
    path('mon-espace/activites/', views_espace.liste_activites_espace, name='liste_activites_espace'),
    path('mon-espace/activites/nouvelle/', views_espace.creer_activite, name='creer_activite'),
    path('mon-espace/activites/<int:pk>/modifier/', views_espace.modifier_activite, name='modifier_activite'),
    path('mon-espace/cagnottes/', views_espace.liste_cagnottes_espace, name='liste_cagnottes_espace'),
    path('mon-espace/cagnottes/nouvelle/', views_espace.creer_cagnotte, name='creer_cagnotte'),
    path('mon-espace/cagnottes/<int:pk>/modifier/', views_espace.modifier_cagnotte, name='modifier_cagnotte'),
]

# Aperçu des pages d'erreur en développement (DEBUG=True uniquement).
if settings.DEBUG:
    urlpatterns += [
        path('apercu-erreur/403/', TemplateView.as_view(template_name='403.html')),
        path('apercu-erreur/404/', TemplateView.as_view(template_name='404.html')),
        path('apercu-erreur/500/', TemplateView.as_view(template_name='500.html')),
    ]
