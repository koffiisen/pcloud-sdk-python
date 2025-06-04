#!/usr/bin/env python3
"""
Exemple d'utilisation basique du SDK pCloud
Démontre les opérations les plus courantes
"""

import os
import sys
import tempfile

# Import du SDK pCloud
from pcloud_sdk import PCloudSDK
from pcloud_sdk.progress_utils import create_progress_bar


def main():
    """Exemple d'utilisation basique du SDK pCloud"""
    
    print("🚀 Exemple d'utilisation basique du SDK pCloud")
    print("=" * 50)
    
    # 1. Configuration et authentification
    print("\n1️⃣ Authentification...")
    
    # Option A: Utiliser des variables d'environnement
    email = os.environ.get('PCLOUD_EMAIL')
    password = os.environ.get('PCLOUD_PASSWORD')
    
    pcloud = PCloudSDK()
    
    if email and password:
        print(f"📧 Connexion avec email: {email}")
        pcloud.login(email, password)
    else:
        # Option B: Saisie manuelle (pour démo)
        print("📧 Variables d'environnement non trouvées")
        print("💡 Conseil: définissez PCLOUD_EMAIL et PCLOUD_PASSWORD")
        
        email = input("Email pCloud: ").strip()
        password = input("Mot de passe: ").strip()
        
        if not email or not password:
            print("❌ Email et mot de passe requis")
            return
            
        pcloud.login(email, password)
    
    try:
        # 2. Informations utilisateur
        print("\n2️⃣ Informations du compte...")
        user_info = pcloud.user.get_user_info()
        
        print(f"👤 Utilisateur: {user_info.get('email', 'N/A')}")
        print(f"💾 Quota: {user_info.get('quota', 0) // (1024**3):.1f} GB")
        print(f"📁 Utilisé: {user_info.get('usedquota', 0) // (1024**3):.1f} GB")
        
        # 3. Lister le contenu du dossier racine
        print("\n3️⃣ Contenu du dossier racine...")
        root_content = pcloud.folder.list_root()
        
        folders = root_content.get('contents', [])
        print(f"📂 {len([f for f in folders if f.get('isfolder')])} dossiers")
        print(f"📄 {len([f for f in folders if not f.get('isfolder')])} fichiers")
        
        # Afficher quelques éléments
        for item in folders[:5]:  # Premiers 5 éléments
            icon = "📁" if item.get('isfolder') else "📄"
            name = item.get('name', 'N/A')
            size = item.get('size', 0)
            if not item.get('isfolder'):
                size_mb = size / (1024 * 1024)
                print(f"  {icon} {name} ({size_mb:.1f} MB)")
            else:
                print(f"  {icon} {name}/")
        
        if len(folders) > 5:
            print(f"  ... et {len(folders) - 5} autres éléments")
        
        # 4. Créer un dossier de test
        print("\n4️⃣ Création d'un dossier de test...")
        test_folder_name = "SDK_Test_Folder"
        
        try:
            folder_id = pcloud.folder.create(test_folder_name, parent=0)
            print(f"✅ Dossier créé: {test_folder_name} (ID: {folder_id})")
        except Exception as e:
            print(f"⚠️ Dossier existe déjà ou erreur: {e}")
            # Essayer de le trouver
            for item in folders:
                if item.get('name') == test_folder_name and item.get('isfolder'):
                    folder_id = item.get('folderid')
                    print(f"📁 Utilisation du dossier existant (ID: {folder_id})")
                    break
            else:
                folder_id = 0  # Utiliser le dossier racine par défaut
        
        # 5. Upload d'un fichier de test
        print("\n5️⃣ Upload d'un fichier de test...")
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            test_content = f"""Fichier de test du SDK pCloud
Créé le: {__import__('datetime').datetime.now()}
Contenu: Ceci est un test d'upload du SDK pCloud Python
Taille: Environ 200 caractères pour tester l'upload
"""
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        # Upload avec barre de progression
        progress_bar = create_progress_bar("Upload Test")
        
        try:
            upload_result = pcloud.file.upload(
                tmp_file_path, 
                folder_id=folder_id,
                filename="test_sdk.txt",
                progress_callback=progress_bar
            )
            
            file_id = upload_result.get('metadata', [{}])[0].get('fileid')
            file_name = upload_result.get('metadata', [{}])[0].get('name')
            print(f"✅ Fichier uploadé: {file_name} (ID: {file_id})")
            
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            file_id = None
        
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        # 6. Download du fichier
        if file_id:
            print("\n6️⃣ Download du fichier...")
            
            download_dir = tempfile.mkdtemp()
            progress_bar_dl = create_progress_bar("Download Test")
            
            try:
                success = pcloud.file.download(
                    file_id, 
                    destination=download_dir,
                    progress_callback=progress_bar_dl
                )
                
                if success:
                    downloaded_files = os.listdir(download_dir)
                    if downloaded_files:
                        downloaded_file = os.path.join(download_dir, downloaded_files[0])
                        file_size = os.path.getsize(downloaded_file)
                        print(f"✅ Fichier téléchargé: {downloaded_files[0]} ({file_size} bytes)")
                        
                        # Vérifier le contenu
                        with open(downloaded_file, 'r') as f:
                            content = f.read()
                            if "SDK pCloud" in content:
                                print("✅ Contenu vérifié - download réussi!")
                    
            except Exception as e:
                print(f"❌ Erreur download: {e}")
            
            finally:
                # Nettoyer le dossier de téléchargement
                try:
                    import shutil
                    shutil.rmtree(download_dir)
                except:
                    pass
            
            # 7. Suppression du fichier de test
            print("\n7️⃣ Nettoyage...")
            try:
                pcloud.file.delete(file_id)
                print("✅ Fichier de test supprimé")
            except Exception as e:
                print(f"⚠️ Erreur suppression fichier: {e}")
        
        # 8. Suppression du dossier de test
        if folder_id and folder_id != 0:
            try:
                pcloud.folder.delete(folder_id)
                print("✅ Dossier de test supprimé")
            except Exception as e:
                print(f"⚠️ Erreur suppression dossier: {e}")
        
        print("\n🎉 Test basique terminé avec succès!")
        print("\n💡 Ce que vous pouvez faire maintenant:")
        print("   - Explorer les autres exemples dans le dossier examples/")
        print("   - Consulter la documentation dans docs/")
        print("   - Utiliser le CLI: pcloud-sdk --help")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        print("💡 Vérifiez vos identifiants et votre connexion internet")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())