#!/usr/bin/env python3
"""
Utilitaires pour le suivi de progression des uploads/downloads pCloud
Classes helper prêtes à l'emploi
"""

import time
from datetime import datetime
from typing import Optional


class SimpleProgressBar:
    """Barre de progression simple et efficace"""

    def __init__(
        self,
        title: str = "Progress",
        width: int = 50,
        show_speed: bool = True,
        show_eta: bool = True,
    ):
        """
        Args:
            title: Titre à afficher
            width: Largeur de la barre de progression
            show_speed: Afficher la vitesse de transfert
            show_eta: Afficher le temps estimé restant
        """
        self.title = title
        self.width = width
        self.show_speed = show_speed
        self.show_eta = show_eta
        self.start_time = None
        self.last_update = 0

    def __call__(
        self,
        bytes_transferred: int,
        total_bytes: int,
        percentage: float,
        speed: float,
        **kwargs,
    ):
        """Callback function pour les transferts pCloud"""

        if self.start_time is None:
            self.start_time = time.time()
            print(f"\n{self.title}: {kwargs.get('filename', 'file')}")

        # Limiter les updates pour éviter le flickering
        now = time.time()
        if now - self.last_update < 0.1 and percentage < 100:
            return
        self.last_update = now

        # Créer la barre
        filled = int(self.width * percentage / 100)
        bar = "█" * filled + "░" * (self.width - filled)

        # Formatage des données
        transferred_mb = bytes_transferred / (1024 * 1024)
        total_mb = total_bytes / (1024 * 1024)

        # Construire la ligne d'affichage
        display_parts = [f"[{bar}] {percentage:.1f}%"]
        display_parts.append(f"({transferred_mb:.1f}/{total_mb:.1f}MB)")

        if self.show_speed and speed > 0:
            speed_mb = speed / (1024 * 1024)
            display_parts.append(f"{speed_mb:.1f}MB/s")

        if self.show_eta and speed > 0 and percentage < 100:
            remaining_bytes = total_bytes - bytes_transferred
            eta_seconds = remaining_bytes / speed
            if eta_seconds < 60:
                eta_str = f"{int(eta_seconds)}s"
            elif eta_seconds < 3600:
                eta_str = f"{int(eta_seconds / 60)}m{int(eta_seconds % 60)}s"
            else:
                eta_str = f"{int(eta_seconds / 3600)}h{int((eta_seconds % 3600) / 60)}m"
            display_parts.append(f"ETA:{eta_str}")

        # Afficher
        display_line = " ".join(display_parts)
        print(f"\r{display_line}", end="", flush=True)

        # Nouvelle ligne à la fin
        if percentage >= 100:
            elapsed = time.time() - self.start_time
            final_speed = (
                bytes_transferred / elapsed / (1024 * 1024) if elapsed > 0 else 0
            )
            print(
                f"\n✅ Terminé en {elapsed:.1f}s (vitesse moyenne: {final_speed:.1f}MB/s)"
            )


class DetailedProgress:
    """Affichage détaillé de la progression avec logs"""

    def __init__(self, log_file: Optional[str] = None):
        """
        Args:
            log_file: Fichier de log optionnel pour sauvegarder la progression
        """
        self.log_file = log_file
        self.start_time = None
        self.checkpoints = []

    def __call__(
        self,
        bytes_transferred: int,
        total_bytes: int,
        percentage: float,
        speed: float,
        **kwargs,
    ):
        """Callback avec affichage détaillé"""

        if self.start_time is None:
            self.start_time = time.time()
            operation = kwargs.get("operation", "transfer")
            filename = kwargs.get("filename", "file")
            print(f"\n🚀 Starting {operation}: {filename} ({total_bytes:,} bytes)")

        # Enregistrer checkpoint
        checkpoint = {
            "time": time.time(),
            "bytes": bytes_transferred,
            "percentage": percentage,
            "speed": speed,
        }
        self.checkpoints.append(checkpoint)

        status = kwargs.get("status", "progress")

        # Affichage selon le statut
        if status == "starting":
            print("📋 Initialisation du transfert...")
        elif status == "saving":
            print("💾 Sauvegarde en cours...")
        elif status == "completed":
            elapsed = time.time() - self.start_time
            avg_speed = (
                bytes_transferred / elapsed / (1024 * 1024) if elapsed > 0 else 0
            )
            print(f"✅ Transfert terminé!")
            print(f"   Durée: {elapsed:.1f}s")
            print(f"   Vitesse moyenne: {avg_speed:.1f}MB/s")
            print(f"   Taille: {bytes_transferred:,} bytes")
        elif status == "error":
            print(f"❌ Erreur: {kwargs.get('error', 'Unknown error')}")
        else:
            # Affichage périodique
            if int(percentage) % 20 == 0 and len(self.checkpoints) > 1:
                elapsed = time.time() - self.start_time
                print(
                    f"📊 Progression: {percentage:.1f}% "
                    f"({bytes_transferred:,}/{total_bytes:,} bytes) "
                    f"- {speed / (1024 * 1024):.1f}MB/s "
                    f"- {elapsed:.1f}s elapsed"
                )

        # Log dans fichier si spécifié
        if self.log_file:
            self._log_to_file(checkpoint, **kwargs)

    def _log_to_file(self, checkpoint: dict, **kwargs):
        """Enregistrer la progression dans un fichier"""
        timestamp = datetime.now().isoformat()
        operation = kwargs.get("operation", "transfer")
        filename = kwargs.get("filename", "file")
        status = kwargs.get("status", "progress")

        log_line = (
            f"{timestamp} | {operation} | {filename} | "
            f"{checkpoint['percentage']:.1f}% | "
            f"{checkpoint['bytes']:,} bytes | "
            f"{checkpoint['speed'] / (1024 * 1024):.1f}MB/s | "
            f"{status}\n"
        )

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass  # Ignorer les erreurs de log


class MinimalProgress:
    """Affichage minimal - seulement les étapes importantes"""

    def __init__(self):
        self.milestones = {0, 25, 50, 75, 100}  # Pourcentages à afficher
        self.shown = set()
        self.start_time = None

    def __call__(
        self,
        bytes_transferred: int,
        total_bytes: int,
        percentage: float,
        speed: float,
        **kwargs,
    ):
        """Callback minimal"""

        if self.start_time is None:
            self.start_time = time.time()
            filename = kwargs.get("filename", "file")
            operation = kwargs.get("operation", "transfer")
            print(f"🚀 {operation.title()}: {filename}")

        # Afficher seulement aux milestones
        milestone = min(self.milestones, key=lambda x: abs(x - percentage))
        if milestone in self.milestones and milestone not in self.shown:
            if milestone < 100:
                print(f"📊 {milestone}%...")
            self.shown.add(milestone)

        # Message final
        status = kwargs.get("status", "progress")
        if status == "completed":
            elapsed = time.time() - self.start_time
            print(f"✅ Terminé en {elapsed:.1f}s")
        elif status == "error":
            print(f"❌ Erreur: {kwargs.get('error', 'Unknown')}")


class SilentProgress:
    """Progression silencieuse - pour logging uniquement"""

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.start_time = None

        # Créer/vider le fichier de log
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"# pCloud Transfer Log - {datetime.now().isoformat()}\n")
            f.write(
                "# timestamp,operation,filename,percentage,bytes_transferred,total_bytes,speed_mbps,status\n"
            )

    def __call__(
        self,
        bytes_transferred: int,
        total_bytes: int,
        percentage: float,
        speed: float,
        **kwargs,
    ):
        """Callback silencieux avec log CSV"""

        if self.start_time is None:
            self.start_time = time.time()

        timestamp = datetime.now().isoformat()
        operation = kwargs.get("operation", "transfer")
        filename = kwargs.get("filename", "file")
        status = kwargs.get("status", "progress")
        speed_mbps = speed / (1024 * 1024)

        log_line = f"{timestamp},{operation},{filename},{percentage:.1f},{bytes_transferred},{total_bytes},{speed_mbps:.2f},{status}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass


# Factory functions pour création rapide
def create_progress_bar(title: str = "Transfer", **kwargs) -> SimpleProgressBar:
    """Créer une barre de progression simple"""
    return SimpleProgressBar(title=title, **kwargs)


def create_detailed_progress(log_file: Optional[str] = None) -> DetailedProgress:
    """Créer un tracker de progression détaillé"""
    return DetailedProgress(log_file=log_file)


def create_minimal_progress() -> MinimalProgress:
    """Créer un tracker de progression minimal"""
    return MinimalProgress()


def create_silent_progress(log_file: str) -> SilentProgress:
    """Créer un tracker silencieux avec log"""
    return SilentProgress(log_file)


# Exemples d'utilisation rapide
if __name__ == "__main__":
    print("🧪 Test des utilitaires de progression")
    print("=" * 40)

    # Simulation d'un transfert
    def simulate_transfer(progress_callback):
        """Simuler un transfert pour tester les callbacks"""
        total_size = 10 * 1024 * 1024  # 10MB
        chunk_size = 512 * 1024  # 512KB chunks

        transferred = 0
        start_time = time.time()

        while transferred < total_size:
            time.sleep(0.1)  # Simuler le temps de transfert
            transferred += chunk_size
            if transferred > total_size:
                transferred = total_size

            elapsed = time.time() - start_time
            speed = transferred / elapsed if elapsed > 0 else 0
            percentage = (transferred / total_size) * 100

            if transferred == chunk_size:
                progress_callback(
                    transferred,
                    total_size,
                    percentage,
                    speed,
                    operation="upload",
                    filename="test_file.txt",
                    status="starting",
                )
            elif transferred >= total_size:
                progress_callback(
                    transferred,
                    total_size,
                    percentage,
                    speed,
                    operation="upload",
                    filename="test_file.txt",
                    status="completed",
                )
            else:
                progress_callback(
                    transferred,
                    total_size,
                    percentage,
                    speed,
                    operation="upload",
                    filename="test_file.txt",
                )

    # Test des différents progress trackers
    print("1️⃣ Test SimpleProgressBar:")
    simulate_transfer(create_progress_bar("Upload Test"))

    print("\n2️⃣ Test MinimalProgress:")
    simulate_transfer(create_minimal_progress())

    print("\n3️⃣ Test DetailedProgress:")
    simulate_transfer(create_detailed_progress())

    print("\n4️⃣ Test SilentProgress (voir silent_log.csv):")
    simulate_transfer(create_silent_progress("silent_log.csv"))
    print("📝 Log sauvegardé dans silent_log.csv")

    print("\n✅ Tests terminés!")
