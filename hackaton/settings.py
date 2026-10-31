"""
Configuration Django du projet hackaton (RubanRose Connect).
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Sécurité -----------------------------------------------------------
# Garde la SECRET_KEY générée par Django lors de la création du projet.
SECRET_KEY = 'django-insecure-884g6y#_fpw-uwj)y5+ofg%)wbqfqzsh18wb8-d)b81d+uxq3s'

# Développement local uniquement. Passer DEBUG à False en production.
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# --- Applications -------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Application du projet
    'rubanrose.apps.RubanroseConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hackaton.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Dossier "templates" à la racine : pages d'erreur 403/404/500
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hackaton.wsgi.application'

# --- Base de données ----------------------------------------------------
# SQLite en local. Pour migrer vers PostgreSQL plus tard, seul ce bloc
# devra changer (le code des modèles n'utilise rien de spécifique à SQLite).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Validation des mots de passe ---------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalisation ----------------------------------------------
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques et médias ---------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Authentification ---------------------------------------------------
# Ces noms d'URL seront créés à l'étape "Authentification".
LOGIN_URL = 'rubanrose:connexion'
LOGIN_REDIRECT_URL = 'rubanrose:tableau_de_bord'
LOGOUT_REDIRECT_URL = 'rubanrose:accueil'

# --- Paiements ----------------------------------------------------------
# Aucun prestataire de paiement n'est intégré dans cette version.
# Mettre à True uniquement lorsqu'une intégration réelle (compatible Bénin)
# aura été développée et testée.
PAIEMENTS_ACTIVES = False