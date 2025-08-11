import logging
from utils import run_command
import sys
from subprocess import CalledProcessError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def partition_disk(disk: str) -> None:
    print(f"Partitionnement du disque {disk}...")

    try:
        # S'assurer qu'on travaille avec le nom du périphérique sans /dev/
        disk_name = disk.replace('/dev/', '')
        
        # Créer une nouvelle table de partitions GPT
        run_command(["parted", f"/dev/{disk_name}", "--script", "mklabel", "gpt"])
        
        # Créer une partition primaire utilisant 100% de l'espace disque
        run_command(["parted", f"/dev/{disk_name}", "--script", "mkpart", "primary", "0%", "100%"])
        
        print(f"Disque {disk_name} partitionné avec succès.")
    except FileNotFoundError:
        logging.error(f"Erreur : Commande `parted` introuvable. Assurez-vous qu'elle est installée.")
        sys.exit(2)
    except CalledProcessError as e:
        logging.error(f"Erreur : Échec du partitionnement de {disk} : {e}")
        sys.exit(1)