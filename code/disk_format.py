import logging
from utils import run_command
from subprocess import CalledProcessError
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def format_disk(disk: str, fs_choice: str) -> None:
    # S'assurer qu'on travaille avec le nom du périphérique sans /dev/
    disk_name = disk.replace('/dev/', '')
    partition = f"/dev/{disk_name}1"
    
    # Attendre brièvement que la partition soit reconnue par le système
    logging.info(f"Attente de la reconnaissance de la partition {partition}...")
    time.sleep(2)
    
    try:
        if fs_choice == "ntfs":
            logging.info(f"Formatage de {partition} en NTFS...")
            run_command(["mkfs.ntfs", "-f", partition])
        elif fs_choice == "ext4":
            logging.info(f"Formatage de {partition} en EXT4...")
            run_command(["mkfs.ext4", "-F", partition])
        elif fs_choice == "vfat":
            logging.info(f"Formatage de {partition} en VFAT...")
            run_command(["mkfs.vfat", "-F", "32", partition])
        else:
            logging.error(f"Système de fichiers non supporté : {fs_choice}")
            sys.exit(1)

        logging.info(f"Partition {partition} formatée avec succès.")
    except FileNotFoundError:
        logging.error(f"Erreur : Utilitaire de système de fichiers introuvable pour {fs_choice}. Assurez-vous que les outils nécessaires sont installés.")
        sys.exit(2)
    except CalledProcessError as e:
        logging.error(f"Erreur : Échec du formatage de {partition} : {e}")
        sys.exit(1)