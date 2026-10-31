// Active les animations uniquement si ce script fonctionne réellement.
document.documentElement.classList.add('js');

document.addEventListener('DOMContentLoaded', function () {
  var liensNavigation = Array.from(
    document.querySelectorAll('#menuPrincipal .navbar-nav .nav-link')
  );
  var mettreAJourNavigation = function (lienSelectionne) {
    var lienActif = lienSelectionne || liensNavigation.find(function (lien) {
      return lien.hash && lien.hash === window.location.hash;
    }) || liensNavigation.find(function (lien) {
      return lien.dataset.defaultActive === 'true';
    });

    liensNavigation.forEach(function (lien) {
      var actif = lien === lienActif;
      lien.classList.toggle('active', actif);
      if (actif) {
        lien.setAttribute('aria-current', 'page');
      } else {
        lien.removeAttribute('aria-current');
      }
    });
  };

  liensNavigation.forEach(function (lien) {
    lien.addEventListener('click', function () {
      mettreAJourNavigation(lien);
    });
  });
  window.addEventListener('hashchange', function () {
    mettreAJourNavigation();
  });
  mettreAJourNavigation();

  // Applique immédiatement le filtre de ville après la sélection.
  document.querySelectorAll('select[data-auto-submit="true"]').forEach(function (select) {
    select.addEventListener('change', function () {
      if (select.value) { select.form.requestSubmit(); }
    });
  });

  // Referme le menu mobile après une navigation vers une section de l'accueil.
  document.querySelectorAll('#menuPrincipal a[href*="#"]').forEach(function (lien) {
    lien.addEventListener('click', function () {
      var menu = document.getElementById('menuPrincipal');
      if (menu && menu.classList.contains('show') && window.bootstrap) {
        bootstrap.Collapse.getOrCreateInstance(menu).hide();
      }
    });
  });

  // Ombre sous l'en-tête au défilement
  var header = document.querySelector('.rr-header');
  if (header) {
    var majEntete = function () {
      header.classList.toggle('rr-scrolled', window.scrollY > 10);
    };
    majEntete();
    window.addEventListener('scroll', majEntete, { passive: true });
  }

  // Apparition progressive des blocs
  var blocs = document.querySelectorAll('.rr-reveal');
  var toutAfficher = function () {
    blocs.forEach(function (b) { b.classList.add('rr-visible'); });
  };

  if ('IntersectionObserver' in window) {
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (entree.isIntersecting) {
          entree.target.classList.add('rr-visible');
          observateur.unobserve(entree.target);
        }
      });
    }, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });
    blocs.forEach(function (b) { observateur.observe(b); });
    // Filet de sécurité : rien ne reste invisible
    setTimeout(toutAfficher, 1500);
  } else {
    toutAfficher();
  }

  // Fermeture automatique des messages de succès
  document.querySelectorAll('.alert-success').forEach(function (alerte) {
    setTimeout(function () {
      if (window.bootstrap) { bootstrap.Alert.getOrCreateInstance(alerte).close(); }
    }, 6000);
  });
});
