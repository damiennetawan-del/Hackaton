from django.contrib import admin, messages

from .models import Activite, Cagnotte, Organisation

admin.site.site_header = 'RubanRose Connect : administration'
admin.site.site_title = 'RubanRose Connect'
admin.site.index_title = 'Gestion de la plateforme'


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'statut_verification', 'est_active', 'date_inscription')
    list_filter = ('statut_verification', 'est_active', 'ville')
    search_fields = ('nom', 'ville', 'email_public', 'user__username')
    readonly_fields = ('date_inscription',)
    date_hierarchy = 'date_inscription'
    actions = ['approuver', 'refuser', 'activer', 'desactiver']

    @admin.action(description='Approuver les organisations sélectionnées', permissions=['change'])
    def approuver(self, request, queryset):
        n = queryset.update(statut_verification=Organisation.Statut.APPROUVEE, motif_refus='')
        self.message_user(request, f'{n} organisation(s) approuvée(s).', messages.SUCCESS)

    @admin.action(description='Refuser les organisations sélectionnées', permissions=['change'])
    def refuser(self, request, queryset):
        n = queryset.update(statut_verification=Organisation.Statut.REFUSEE)
        self.message_user(
            request,
            f'{n} organisation(s) refusée(s). Pensez à renseigner le motif du refus dans la fiche.',
            messages.WARNING,
        )

    @admin.action(description='Activer les organisations sélectionnées', permissions=['change'])
    def activer(self, request, queryset):
        n = queryset.update(est_active=True)
        self.message_user(request, f'{n} organisation(s) activée(s).', messages.SUCCESS)

    @admin.action(description='Désactiver les organisations sélectionnées', permissions=['change'])
    def desactiver(self, request, queryset):
        n = queryset.update(est_active=False)
        self.message_user(request, f'{n} organisation(s) désactivée(s).', messages.WARNING)


@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'organisation', 'categorie', 'date_debut', 'statut', 'date_creation')
    list_filter = ('statut', 'categorie', 'organisation')
    search_fields = ('titre', 'description', 'lieu', 'organisation__nom')
    readonly_fields = ('date_creation', 'date_modification')
    date_hierarchy = 'date_debut'
    actions = ['approuver', 'refuser']

    @admin.action(description='Approuver et publier', permissions=['change'])
    def approuver(self, request, queryset):
        total = queryset.count()
        eligibles = queryset.filter(
            organisation__statut_verification=Organisation.Statut.APPROUVEE,
            organisation__est_active=True,
        )
        n = eligibles.update(statut=Activite.Statut.PUBLIEE, motif_refus='')
        self.message_user(request, f'{n} activité(s) publiée(s).', messages.SUCCESS)
        if total - n:
            self.message_user(
                request,
                f"{total - n} activité(s) ignorée(s) : l'organisation n'est pas approuvée ou active.",
                messages.WARNING,
            )

    @admin.action(description='Refuser', permissions=['change'])
    def refuser(self, request, queryset):
        n = queryset.update(statut=Activite.Statut.REFUSEE)
        self.message_user(request, f'{n} activité(s) refusée(s).', messages.WARNING)


@admin.register(Cagnotte)
class CagnotteAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'organisation', 'objectif_financier', 'montant_collecte',
        'date_debut', 'date_fin', 'statut',
    )
    list_filter = ('statut', 'organisation')
    search_fields = ('titre', 'description', 'organisation__nom')
    readonly_fields = ('date_creation',)
    actions = ['approuver', 'refuser']

    @admin.action(description='Valider les cagnottes sélectionnées', permissions=['change'])
    def approuver(self, request, queryset):
        total = queryset.count()
        eligibles = queryset.filter(
            organisation__statut_verification=Organisation.Statut.APPROUVEE,
            organisation__est_active=True,
        )
        n = eligibles.update(statut=Cagnotte.Statut.VALIDEE, motif_refus='')
        self.message_user(request, f'{n} cagnotte(s) validée(s).', messages.SUCCESS)
        if total - n:
            self.message_user(
                request,
                f"{total - n} cagnotte(s) ignorée(s) : l'organisation n'est pas approuvée ou active.",
                messages.WARNING,
            )

    @admin.action(description='Refuser les cagnottes sélectionnées', permissions=['change'])
    def refuser(self, request, queryset):
        n = queryset.update(statut=Cagnotte.Statut.REFUSEE)
        self.message_user(request, f'{n} cagnotte(s) refusée(s).', messages.WARNING)