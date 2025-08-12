import subprocess
import logging
import sys
import re

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command_list: list[str]) -> str:
    try:
        result = subprocess.run(command_list, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except FileNotFoundError:
        logging.error(f"Erreur : Commande introuvable : {' '.join(command_list)}")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error(f"Erreur : Échec d'exécution de la commande : {' '.join(command_list)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Opération interrompue par l'utilisateur (Ctrl+C)")
        print("\nOpération interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)  # Code de sortie standard pour SIGINT

def get_disk_label(device: str) -> str:
    """
    Récupère l'étiquette d'un périphérique disque via lsblk.
    """
    try:
        output = run_command(["lsblk", "-o", "LABEL", "-n", f"/dev/{device}"])
        if output and output.strip():
            labels = [line.strip() for line in output.split('\n') if line.strip()]
            if labels:
                return labels[0]
        return "Aucune étiquette"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Inconnue"

def list_disks() -> str:
    """
    Retourne une chaîne contenant la liste brute des disques détectés.
    """
    try:
        output = run_command(["lsblk", "-d", "-o", "NAME,SIZE,TYPE,MODEL", "-n"])
        if output:
            return output
        else:
            output = run_command(["lsblk", "-d", "-o", "NAME", "-n"])
            if output:
                logging.info(output)
                return output
            else:
                logging.info("Aucun disque détecté. Assurez-vous d'exécuter le programme avec les droits appropriés.")
                return ""
    except FileNotFoundError:
        logging.error("Erreur : Commande `lsblk` introuvable. Installez le paquet `util-linux`.")
        sys.exit(2)
    except subprocess.CalledProcessError:
        logging.error("Erreur : Échec lors de la récupération des informations disque.")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.error("Liste des disques interrompue par l'utilisateur (Ctrl+C)")
        print("\nListe des disques interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)

def get_disk_list() -> list[dict]:
    """
    Retourne une liste de dictionnaires contenant les informations des disques.
    Utilise les clés en anglais pour maintenir la compatibilité avec le reste du code.
    """
    try:
        output = list_disks()
        if not output:
            logging.info("Aucun disque trouvé.")
            return []
        disks = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.strip().split(maxsplit=3)
            device = parts[0]
            if len(parts) >= 2:
                size = parts[1]
                model = parts[3] if len(parts) > 3 else "Inconnu"
                label = get_disk_label(device)
                disks.append({
                    "device": f"/dev/{device}",
                    "size": size,
                    "model": model,
                    "label": label
                })
        return disks
    except FileNotFoundError as e:
        logging.error(f"Erreur : Commande introuvable : {str(e)}")
        return []
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'exécution de la commande : {str(e)}")
        return []
    except (IndexError, ValueError) as e:
        logging.error(f"Erreur lors du traitement des informations disque : {str(e)}")
        return []
    except KeyboardInterrupt:
        logging.error("Liste des disques interrompue par l'utilisateur")
        return []

def choose_filesystem() -> str:
    """
    Demande à l'utilisateur de choisir un système de fichiers.
    """
    while True:
        try:
            print("Choisissez un système de fichiers pour formater le disque :")
            print("1. NTFS")
            print("2. EXT4")
            print("3. VFAT")
            choice = input("Entrez votre choix (1, 2 ou 3) : ").strip()
            if choice == "1":
                return "ntfs"
            elif choice == "2":
                return "ext4"
            elif choice == "3":
                return "vfat"
            else:
                logging.error("Choix invalide. Veuillez sélectionner une option correcte.")
        except KeyboardInterrupt:
            logging.error("Sélection du système de fichiers interrompue par l'utilisateur (Ctrl+C)")
            print("\nSélection du système de fichiers interrompue par l'utilisateur (Ctrl+C)")
            sys.exit(130)
        except EOFError:
            logging.error("Flux d'entrée fermé de manière inattendue")
            print("\nFlux d'entrée fermé de manière inattendue")
            sys.exit(1)

def get_physical_drives_for_logical_volumes(active_devices: list) -> set:
    """
    Associe les volumes logiques à leurs disques physiques sous-jacents.
    """
    if not active_devices:
        return set()
    physical_drives = set()
    try:
        disk_list = get_disk_list()
        physical_device_names = [disk['device'].replace('/dev/', '') for disk in disk_list]
        for physical_device in physical_device_names:
            try:
                output = run_command([
                    "lsblk",
                    f"/dev/{physical_device}",
                    "-o", "NAME",
                    "-l",
                    "-n"
                ])
                device_tree = []
                for line in output.strip().split('\n'):
                    if line.strip():
                        device_name = line.strip()
                        device_tree.append(f"/dev/{device_name}")
                        device_tree.append(device_name)
                for active_device in active_devices:
                    active_variants = [
                        active_device,
                        active_device.replace('/dev/', ''),
                        active_device.replace('/dev/mapper/', '')
                    ]
                    for variant in active_variants:
                        if variant in device_tree:
                            physical_drives.add(physical_device)
                            logging.info(f"Périphérique actif trouvé '{active_device}' sur le disque physique '{physical_device}'")
                            break
                    if physical_device in physical_drives:
                        break
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.error(f"Impossible de lire la hiérarchie pour {physical_device} : {str(e)}")
                continue
    except (AttributeError, TypeError) as e:
        logging.error(f"Erreur lors du traitement des structures de données : {str(e)}")
    except MemoryError:
        logging.error("Mémoire insuffisante pour traiter les volumes logiques")
    except OSError as e:
        logging.error(f"Erreur système lors de la cartographie des volumes logiques : {str(e)}")
    return physical_drives

def get_base_disk(device_name: str) -> str:
    """
    Extrait le nom du disque de base à partir d'un périphérique.
    """
    try:
        if 'nvme' in device_name:
            match = re.match(r'(nvme\d+n\d+)', device_name)
            if match:
                return match.group(1)
        match = re.match(r'([a-zA-Z/]+[a-zA-Z])', device_name)
        if match:
            return match.group(1)
        return device_name
    except (re.error, AttributeError) as e:
        logging.error(f"Erreur de traitement Regex pour '{device_name}' : {str(e)}")
        return device_name
    except TypeError:
        logging.error(f"Type de nom de périphérique invalide : attendu chaîne, reçu {type(device_name)}")
        return str(device_name) if device_name is not None else ""