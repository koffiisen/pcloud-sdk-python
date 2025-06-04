# pCloud SDK for Python

Un SDK Python pour interagir avec l'API pCloud, converti depuis le SDK PHP officiel.

## Démarrage rapide

```python
from pcloud_sdk import PCloudSDK

# Login simple avec gestion automatique des tokens (RECOMMANDÉ)
sdk = PCloudSDK()  # Par défaut: serveur EU, auth directe, token manager activé
sdk.login("votre_email@example.com", "votre_password")

# Utilisation immédiate
print(f"Connecté: {sdk.user.get_user_email()}")

# Upload avec progression temps réel
def progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    print(f"📤 {percentage:.1f}% ({speed/1024/1024:.1f} MB/s)")

sdk.file.upload("/chemin/vers/fichier.txt", progress_callback=progress)

# Les prochaines fois, connexion instantanée grâce au token manager ! 🚀
```

## Suivi de progression en temps réel 📊

Le SDK v2.0 inclut un système de callbacks pour suivre la progression des uploads et downloads :

```python
from progress_utils import create_progress_bar, create_detailed_progress

# Barre de progression interactive
progress_bar = create_progress_bar("Mon Upload")
sdk.file.upload("fichier.txt", progress_callback=progress_bar)
# [████████████████████████████████████████] 100.0% (15.2/15.2MB) 2.1MB/s

# Progression détaillée avec logs
detailed = create_detailed_progress(log_file="transfers.log")
sdk.file.download(file_id, "./downloads/", progress_callback=detailed)

# Callback personnalisé
def mon_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    if percentage % 25 == 0:  # Tous les 25%
        print(f"🎯 {kwargs['operation']}: {percentage:.0f}% terminé")

sdk.file.upload("gros_fichier.zip", progress_callback=mon_callback)
```

## Installation

```bash
pip install requests
```

Le SDK utilise uniquement la bibliothèque `requests` comme dépendance externe.

## Nouveautés v2.0

✨ **Gestionnaire de token intégré** - Plus besoin de se reconnecter !
🇪🇺 **Serveur EU par défaut** - Optimisé pour l'Europe
🔐 **Authentification directe par défaut** - Plus simple à utiliser
💾 **Sauvegarde automatique des credentials** - Connexion instantanée

## Configuration initiale

### 1. Créer une application pCloud (optionnel pour login direct)

1. Allez sur [pCloud Developer Console](https://docs.pcloud.com/my_apps/)
2. Créez une nouvelle application
3. Notez votre **Client ID** (App Key) et **Client Secret** (App Secret)
4. Configurez votre **Redirect URI**

**Note:** Pour le login direct avec email/password, vous n'avez pas besoin de créer une application.

### 2. Authentification - Trois méthodes disponibles

#### Méthode 1: Login direct avec gestionnaire de token (Recommandé)

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Initialisation simple avec paramètres optimaux par défaut
sdk = PCloudSDK()  # token_manager=True, location_id=2 (EU), auth_type="direct"

try:
    # Première fois : fournir email/password
    login_info = sdk.login("votre_email@example.com", "votre_mot_de_passe")
    print(f"Connecté: {login_info['email']}")
    
    # Les fois suivantes : connexion automatique instantanée !
    # sdk.login()  # Pas besoin d'email/password, utilise le token sauvegardé
    
except PCloudException as e:
    print(f"Erreur: {e}")
```

#### Méthode 2: OAuth2 Flow (Pour applications tierces)

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Initialiser avec OAuth2
sdk = PCloudSDK(
    app_key="votre_client_id",
    app_secret="votre_client_secret",
    auth_type="oauth2"
)

# Étape 1: Obtenir l'URL d'autorisation
auth_url = sdk.get_auth_url("http://localhost:8000/callback")
print(f"Visitez cette URL: {auth_url}")

# Étape 2: Échanger le code contre un token
try:
    token_info = sdk.authenticate("code_recu_du_callback")
    print(f"Token d'accès: {token_info['access_token']}")
except PCloudException as e:
    print(f"Erreur d'authentification: {e}")
```

#### Méthode 3: Token existant

```python
sdk = PCloudSDK(
    access_token="votre_token_existant",
    auth_type="direct",
    token_manager=False  # Optionnel: désactiver la gestion auto
)
```

#### Méthode 4: Sans gestionnaire de token (mode manuel)

```python
sdk = PCloudSDK(token_manager=False)
# Doit fournir credentials à chaque fois
sdk.login("email", "password")
```

## Gestion automatique des tokens 🔑

Le SDK inclut un gestionnaire de token intégré pour éviter les reconnexions fréquentes.

### Fonctionnalités automatiques :

- ✅ **Sauvegarde automatique** des tokens après connexion
- ✅ **Chargement automatique** des tokens sauvegardés
- ✅ **Test de validité** avant utilisation
- ✅ **Reconnexion transparente** si le token expire
- ✅ **Gestion multi-comptes** avec fichiers séparés

### Utilisation basique :

```python
# Première utilisation
sdk = PCloudSDK()
sdk.login("email@example.com", "password")
# Token automatiquement sauvegardé dans .pcloud_credentials

# Utilisations suivantes (même script plus tard)
sdk = PCloudSDK()  
sdk.login()  # Connexion instantanée avec le token sauvegardé !
```

### Configuration avancée :

```python
# Fichier de credentials personnalisé
sdk = PCloudSDK(token_file=".my_pcloud_session")

# Forcer une nouvelle connexion
sdk.login("email", "password", force_login=True)

# Désactiver complètement le gestionnaire
sdk = PCloudSDK(token_manager=False)

# Nettoyer les credentials sauvegardés
sdk.logout()  # Supprime le fichier et déconnecte

# Informations sur les credentials
info = sdk.get_credentials_info()
print(f"Connecté depuis {info['age_days']:.1f} jours")
```

### Sécurité :

- 🔒 **Tokens chiffrés** dans le fichier de credentials
- ⏰ **Expiration automatique** après 30 jours
- 🚫 **Pas de mots de passe** sauvegardés (seulement les tokens)
- 🧹 **Nettoyage automatique** des tokens invalides

## Utilisation

### Informations utilisateur

```python
# Obtenir les informations de l'utilisateur
user_info = sdk.user.get_user_info()
print(f"Email: {sdk.user.get_user_email()}")
print(f"Quota utilisé: {sdk.user.get_used_quota()} bytes")
print(f"Quota total: {sdk.user.get_quota()} bytes")
```

### Gestion des dossiers

```python
# Lister le contenu du dossier racine
root_contents = sdk.folder.list_root()
print("Contenu racine:", root_contents)

# Créer un nouveau dossier
folder_id = sdk.folder.create("Mon Nouveau Dossier", parent=0)
print(f"ID du dossier créé: {folder_id}")

# Lister le contenu d'un dossier
contents = sdk.folder.get_content(folder_id)
print("Contenu du dossier:", contents)

# Renommer un dossier
sdk.folder.rename(folder_id, "Nouveau Nom")

# Déplacer un dossier
sdk.folder.move(folder_id, new_parent=0)

# Supprimer un dossier
sdk.folder.delete(folder_id)

# Supprimer récursivement
sdk.folder.delete_recursive(folder_id)
```

### Gestion des fichiers

```python
# Uploader un fichier
upload_result = sdk.file.upload(
    file_path="/chemin/vers/fichier.txt",
    folder_id=0,  # 0 = dossier racine
    filename="fichier_upload.txt"  # optionnel
)
file_id = upload_result['metadata']['fileid']
print(f"Fichier uploadé avec l'ID: {file_id}")

# Obtenir les informations d'un fichier
file_info = sdk.file.get_info(file_id)
print("Info fichier:", file_info)

# Obtenir le lien de téléchargement
download_link = sdk.file.get_link(file_id)
print(f"Lien de téléchargement: {download_link}")

# Télécharger un fichier
sdk.file.download(file_id, destination="/chemin/telechargement/")

# Renommer un fichier
sdk.file.rename(file_id, "nouveau_nom.txt")

# Déplacer un fichier
sdk.file.move(file_id, folder_id=nouveau_dossier_id)

# Copier un fichier
sdk.file.copy(file_id, folder_id=dossier_destination_id)

# Supprimer un fichier
delete_result = sdk.file.delete(file_id)
print("Fichier supprimé:", delete_result)
```

### Gestion des erreurs

```python
try:
    result = sdk.file.upload("/fichier/inexistant.txt")
except PCloudException as e:
    print(f"Erreur pCloud: {e}")
    print(f"Code d'erreur: {e.code}")
except Exception as e:
    print(f"Erreur générale: {e}")
```

## Utilisation avancée

### Utilisation directe des classes

```python
from pcloud_sdk import App, User, File, Folder

# Configuration manuelle
app = App()
app.set_app_key("votre_client_id")
app.set_app_secret("votre_client_secret")
app.set_access_token("votre_token")
app.set_location_id(1)

# Utilisation des classes directement
user = User(app)
folder = Folder(app)
file_manager = File(app)
```

### Configuration des timeouts

```python
# Configurer le timeout pour les requêtes (en secondes)
app.set_curl_execution_timeout(1800)  # 30 minutes
```

### Upload de gros fichiers

Le SDK gère automatiquement l'upload en chunks de 10MB pour les gros fichiers:

```python
# Upload d'un gros fichier (géré automatiquement en chunks)
result = sdk.file.upload("/chemin/vers/gros_fichier.zip", folder_id=0)
```

## Serveurs et localisation

- `location_id=2` : Serveurs EU (par défaut) 🇪🇺
- `location_id=1` : Serveurs USA 🇺🇸

```python
# Serveur EU (par défaut)
sdk = PCloudSDK()  # location_id=2 par défaut

# Forcer serveur US
sdk = PCloudSDK(location_id=1)

# Le gestionnaire de token se souvient de votre serveur préféré
```

## Nouveaux paramètres par défaut

Le SDK v2.0 utilise des paramètres optimisés :

| Paramètre | Ancienne valeur | Nouvelle valeur | Raison |
|-----------|----------------|------------------|---------|
| `location_id` | 1 (US) | **2 (EU)** | Meilleure latence Europe |
| `auth_type` | "oauth2" | **"direct"** | Plus simple à utiliser |
| `token_manager` | Non disponible | **True** | Évite les reconnexions |

### Migration depuis v1.0

```python
# v1.0 (ancien)
sdk = PCloudSDK("", "")
sdk.login("email", "password", location_id=2)

# v2.0 (nouveau) - Équivalent plus simple
sdk = PCloudSDK()  # Tous les paramètres optimaux par défaut
sdk.login("email", "password")
```

## Exemple complet

### Exemple avec login direct (le plus simple)

```python
from pcloud_sdk import PCloudSDK, PCloudException
import os

def exemple_login_direct():
    """Exemple avec authentification directe par email/password"""
    
    # Connexion directe - pas besoin d'app key/secret
    sdk = PCloudSDK("", "")
    
    try:
        # Login avec email/password
        login_info = sdk.login("votre_email@example.com", "votre_password")
        print(f"Connecté en tant que: {login_info['email']}")
        
        # Afficher les infos utilisateur
        print(f"Quota utilisé: {sdk.user.get_used_quota()} bytes")
        print(f"Quota total: {sdk.user.get_quota()} bytes")
        
        # Lister les fichiers du dossier racine
        root_contents = sdk.folder.list_root()
        print("Contenu racine:", len(root_contents.get('contents', [])), "éléments")
        
        # Créer un dossier de test
        folder_id = sdk.folder.create("Test Python SDK")
        print(f"Dossier créé: {folder_id}")
        
        # Upload un fichier
        with open("test.txt", 'w') as f:
            f.write("Hello pCloud!")
        
        upload_result = sdk.file.upload("test.txt", folder_id)
        file_id = upload_result['metadata']['fileid']
        print(f"Fichier uploadé: {file_id}")
        
        # Télécharger le fichier
        sdk.file.download(file_id, "./downloads/")
        print("Fichier téléchargé!")
        
        # Nettoyer
        sdk.file.delete(file_id)
        sdk.folder.delete(folder_id)
        os.remove("test.txt")
        print("Nettoyage terminé")
        
    except PCloudException as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    exemple_login_direct()
```

### Exemple avec OAuth2 (pour applications tierces)

```python
from pcloud_sdk import PCloudSDK, PCloudException
import os

def main():
    # Configuration
    sdk = PCloudSDK(
        app_key="votre_client_id",
        app_secret="votre_client_secret"
    )
    
    # Authentification (à faire une seule fois)
    if not sdk.is_authenticated():
        auth_url = sdk.get_auth_url("http://localhost:8000/callback")
        print(f"Allez sur: {auth_url}")
        
        code = input("Entrez le code d'autorisation: ")
        token_info = sdk.authenticate(code)
        print(f"Authentifié! Token: {token_info['access_token']}")
    
    try:
        # Afficher les infos utilisateur
        print(f"Connecté en tant que: {sdk.user.get_user_email()}")
        
        # Créer un dossier de test
        folder_id = sdk.folder.create("Test Python SDK")
        print(f"Dossier créé: {folder_id}")
        
        # Upload un fichier de test
        test_file = "test.txt"
        with open(test_file, 'w') as f:
            f.write("Hello from Python SDK!")
        
        upload_result = sdk.file.upload(test_file, folder_id)
        file_id = upload_result['metadata']['fileid']
        print(f"Fichier uploadé: {file_id}")
        
        # Télécharger le fichier
        sdk.file.download(file_id, "./downloads/")
        print("Fichier téléchargé dans ./downloads/")
        
        # Nettoyer
        os.remove(test_file)
        sdk.file.delete(file_id)
        sdk.folder.delete(folder_id)
        print("Nettoyage terminé")
        
    except PCloudException as e:
        print(f"Erreur pCloud: {e}")

if __name__ == "__main__":
    main()
```

## Fonctionnalités

### ✅ Implémenté
- Authentification OAuth2 et directe (email/password)
- **Gestionnaire de token automatique** 🆕
- **Callbacks de progression pour upload/download** 🆕
- **Utilitaires de progression prêts à l'emploi** 🆕
- Gestion des utilisateurs
- Gestion des dossiers (créer, supprimer, renommer, déplacer)
- Gestion des fichiers (upload, download, supprimer, renommer, déplacer, copier)
- Upload en chunks pour gros fichiers
- Retry automatique des requêtes
- Support multi-région (US/EU) avec **EU par défaut** 🆕
- Gestion des erreurs
- **Reconnexion automatique** 🆕
- **Sauvegarde persistante des sessions** 🆕

### 🆕 Nouveautés v2.0
- **Token Manager intégré** : Plus de reconnexion manuelle !
- **Callbacks de progression** : Suivi temps réel des transfers
- **Utilitaires de progression** : Barres de progression, logs, affichages détaillés
- **Serveur EU par défaut** : Optimisé pour l'Europe
- **Authentification directe par défaut** : Plus simple à utiliser
- **Auto-save des credentials** : Sessions persistantes
- **Configuration minimale** : `PCloudSDK()` suffit !

### 🔄 Différences par rapport au SDK PHP
- Utilise `requests` au lieu de cURL
- Gestion des exceptions Python native
- Type hints pour une meilleure documentation
- Classe wrapper `PCloudSDK` pour plus de simplicité
- **Gestionnaire de token automatique** (pas dans le PHP SDK)
- **Callbacks de progression temps réel** (pas dans le PHP SDK)

## Dépendances

- Python 3.6+
- requests

## Migration v1.0 → v2.0

### Changements non-breaking :
✅ Tout le code v1.0 fonctionne encore

### Améliorations automatiques :
🚀 Ajoutez simplement `sdk = PCloudSDK()` au lieu de `PCloudSDK("", "")`

### Avantages de la migration :
- 🔑 **Tokens sauvegardés automatiquement**
- 🇪🇺 **Serveur EU par défaut** (meilleure latence Europe)
- ⚡ **Connexions instantanées** après la première fois
- 🛡️ **Gestion automatique des expirations**

## Licence

Ce SDK est une conversion du SDK PHP officiel de pCloud. Consultez la documentation officielle pCloud pour les conditions d'utilisation.