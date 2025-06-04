#!/usr/bin/env python3
"""
Interface en ligne de commande pour pCloud SDK Python v2.0
Usage: pcloud-sdk [command] [options]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from pcloud_sdk import PCloudSDK, PCloudException
    from pcloud_sdk.progress_utils import create_progress_bar, create_minimal_progress
except ImportError:
    print("❌ pCloud SDK non trouvé. Installez-le avec: pip install pcloud-sdk-python")
    sys.exit(1)


class PCloudCLI:
    """Interface CLI pour pCloud SDK"""

    def __init__(self):
        self.sdk = None
        self.config_file = Path.home() / ".pcloud_cli_config"

    def load_config(self) -> dict:
        """Charger la configuration CLI"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, config: dict):
        """Sauvegarder la configuration CLI"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Impossible de sauvegarder la config: {e}")

    def setup_sdk(self, args) -> bool:
        """Initialiser le SDK avec les arguments"""
        try:
            # Charger la config existante
            config = self.load_config()

            # Déterminer les paramètres de connexion
            email = args.email or config.get('email')
            location_id = args.location or config.get('location_id', 2)

            if not email and not args.token:
                print("❌ Email requis pour la première connexion")
                return False

            # Initialiser le SDK
            self.sdk = PCloudSDK(
                access_token=args.token or "",
                location_id=location_id,
                token_manager=not args.no_token_manager,
                token_file=args.token_file or config.get('token_file', '.pcloud_credentials')
            )

            # Connexion si nécessaire
            if not self.sdk.is_authenticated():
                if not email:
                    print("❌ Email requis pour l'authentification")
                    return False

                password = args.password
                if not password:
                    import getpass
                    password = getpass.getpass("🔑 Mot de passe pCloud: ")

                if not password:
                    print("❌ Mot de passe requis")
                    return False

                print(f"🔐 Connexion à pCloud...")
                login_info = self.sdk.login(email, password, location_id)
                print(f"✅ Connecté: {login_info['email']}")

                # Sauvegarder la config
                config.update({
                    'email': login_info['email'],
                    'location_id': login_info['locationid']
                })
                self.save_config(config)

            return True

        except PCloudException as e:
            print(f"❌ Erreur pCloud: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False

    def cmd_login(self, args):
        """Commande de connexion"""
        if not args.email:
            print("❌ Email requis: pcloud-sdk login --email your@email.com")
            return 1

        if self.setup_sdk(args):
            print("✅ Connexion réussie et sauvegardée")
            return 0
        return 1

    def cmd_logout(self, args):
        """Commande de déconnexion"""
        try:
            sdk = PCloudSDK(token_manager=True)
            sdk.logout()

            # Supprimer la config CLI
            if self.config_file.exists():
                self.config_file.unlink()

            print("✅ Déconnecté et credentials supprimés")
            return 0
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return 1

    def cmd_info(self, args):
        """Afficher les informations du compte"""
        if not self.setup_sdk(args):
            return 1

        try:
            user_info = self.sdk.user.get_user_info()
            used_quota = self.sdk.user.get_used_quota()
            total_quota = self.sdk.user.get_quota()

            print("📊 Informations du compte:")
            print(f"   📧 Email: {user_info.get('email', 'Unknown')}")
            print(f"   🆔 User ID: {user_info.get('userid', 'Unknown')}")
            print(f"   💾 Quota utilisé: {used_quota:,} bytes ({used_quota / (1024 ** 3):.2f} GB)")
            print(f"   📦 Quota total: {total_quota:,} bytes ({total_quota / (1024 ** 3):.2f} GB)")
            print(f"   🆓 Espace libre: {(total_quota - used_quota) / (1024 ** 3):.2f} GB")

            return 0
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return 1

    def cmd_list(self, args):
        """Lister le contenu d'un dossier"""
        if not self.setup_sdk(args):
            return 1

        try:
            if args.folder_id:
                contents = self.sdk.folder.get_content(args.folder_id)
            else:
                root_contents = self.sdk.folder.list_root()
                contents = root_contents.get('contents', [])

            if not contents:
                print("📁 Dossier vide")
                return 0

            print(f"📁 Contenu du dossier ({len(contents)} éléments):")

            for item in contents:
                icon = "📁" if item.get('isfolder') else "📄"
                name = item.get('name', 'Sans nom')

                if item.get('isfolder'):
                    print(f"   {icon} {name}/ (ID: {item.get('folderid', 'Unknown')})")
                else:
                    size = item.get('size', 0)
                    print(f"   {icon} {name} ({size:,} bytes, ID: {item.get('fileid', 'Unknown')})")

            return 0
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return 1

    def cmd_upload(self, args):
        """Upload un fichier"""
        if not self.setup_sdk(args):
            return 1

        if not args.file:
            print("❌ Fichier requis: pcloud-sdk upload --file /path/to/file")
            return 1

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ Fichier non trouvé: {file_path}")
            return 1

        try:
            # Choisir le callback de progression
            if args.quiet:
                progress_callback = None
            elif args.minimal:
                progress_callback = create_minimal_progress()
            else:
                progress_callback = create_progress_bar(f"Upload {file_path.name}")

            print(f"📤 Upload de {file_path.name}...")

            result = self.sdk.file.upload(
                str(file_path),
                folder_id=args.folder_id or 0,
                filename=args.name or file_path.name,
                progress_callback=progress_callback
            )

            if 'metadata' in result:
                file_id = result['metadata']['fileid']
                file_size = result['metadata']['size']
                print(f"✅ Upload réussi!")
                print(f"   🆔 File ID: {file_id}")
                print(f"   📏 Taille: {file_size:,} bytes")
                return 0
            else:
                print("❌ Upload échoué")
                return 1

        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            return 1

    def cmd_download(self, args):
        """Download un fichier"""
        if not self.setup_sdk(args):
            return 1

        if not args.file_id:
            print("❌ File ID requis: pcloud-sdk download --file-id 123456")
            return 1

        try:
            # Choisir le callback de progression
            if args.quiet:
                progress_callback = None
            elif args.minimal:
                progress_callback = create_minimal_progress()
            else:
                progress_callback = create_progress_bar("Download")

            destination = args.destination or "."

            print(f"📥 Download du fichier {args.file_id}...")

            success = self.sdk.file.download(
                args.file_id,
                destination,
                progress_callback=progress_callback
            )

            if success:
                print(f"✅ Download réussi dans: {destination}")
                return 0
            else:
                print("❌ Download échoué")
                return 1

        except Exception as e:
            print(f"❌ Erreur download: {e}")
            return 1

    def cmd_delete(self, args):
        """Supprimer un fichier ou dossier"""
        if not self.setup_sdk(args):
            return 1

        if not args.file_id and not args.folder_id:
            print("❌ File ID ou Folder ID requis")
            return 1

        try:
            if args.file_id:
                result = self.sdk.file.delete(args.file_id)
                print(f"✅ Fichier {args.file_id} supprimé")
            else:
                result = self.sdk.folder.delete(args.folder_id)
                print(f"✅ Dossier {args.folder_id} supprimé")

            return 0
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
            return 1


def main():
    """Point d'entrée principal du CLI"""
    parser = argparse.ArgumentParser(
        description="pCloud SDK Python CLI v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  pcloud-sdk login --email user@example.com
  pcloud-sdk info
  pcloud-sdk list
  pcloud-sdk upload --file /path/to/file.txt
  pcloud-sdk download --file-id 123456 --destination ./downloads/
  pcloud-sdk delete --file-id 123456
  pcloud-sdk logout
        """
    )

    # Arguments globaux
    parser.add_argument('--email', help='Email pCloud')
    parser.add_argument('--password', help='Mot de passe pCloud')
    parser.add_argument('--token', help='Token d\'accès existant')
    parser.add_argument('--location', type=int, choices=[1, 2], default=2,
                        help='Localisation serveur (1=US, 2=EU, défaut=2)')
    parser.add_argument('--token-file', help='Fichier de token personnalisé')
    parser.add_argument('--no-token-manager', action='store_true',
                        help='Désactiver le gestionnaire de token')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Mode silencieux')
    parser.add_argument('--minimal', '-m', action='store_true',
                        help='Progression minimale')

    # Sous-commandes
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')

    # Login
    login_parser = subparsers.add_parser('login', help='Se connecter à pCloud')
    login_parser.add_argument('--email', required=True, help='Email pCloud')

    # Logout
    subparsers.add_parser('logout', help='Se déconnecter de pCloud')

    # Info
    subparsers.add_parser('info', help='Afficher les informations du compte')

    # List
    list_parser = subparsers.add_parser('list', help='Lister le contenu d\'un dossier')
    list_parser.add_argument('--folder-id', type=int, help='ID du dossier (défaut=racine)')

    # Upload
    upload_parser = subparsers.add_parser('upload', help='Upload un fichier')
    upload_parser.add_argument('--file', required=True, help='Chemin du fichier à uploader')
    upload_parser.add_argument('--folder-id', type=int, default=0, help='ID du dossier destination')
    upload_parser.add_argument('--name', help='Nom personnalisé pour le fichier')

    # Download
    download_parser = subparsers.add_parser('download', help='Download un fichier')
    download_parser.add_argument('--file-id', type=int, required=True, help='ID du fichier')
    download_parser.add_argument('--destination', default='.', help='Dossier de destination')

    # Delete
    delete_parser = subparsers.add_parser('delete', help='Supprimer un fichier ou dossier')
    delete_group = delete_parser.add_mutually_exclusive_group(required=True)
    delete_group.add_argument('--file-id', type=int, help='ID du fichier à supprimer')
    delete_group.add_argument('--folder-id', type=int, help='ID du dossier à supprimer')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Exécuter la commande
    cli = PCloudCLI()

    try:
        if args.command == 'login':
            return cli.cmd_login(args)
        elif args.command == 'logout':
            return cli.cmd_logout(args)
        elif args.command == 'info':
            return cli.cmd_info(args)
        elif args.command == 'list':
            return cli.cmd_list(args)
        elif args.command == 'upload':
            return cli.cmd_upload(args)
        elif args.command == 'download':
            return cli.cmd_download(args)
        elif args.command == 'delete':
            return cli.cmd_delete(args)
        else:
            print(f"❌ Commande inconnue: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Opération interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
