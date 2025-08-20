import time
from utils import run_command, get_physical_drives_for_logical_volumes, get_base_disk
from subprocess import CalledProcessError
import re
from disk_erase import erase_disk_hdd, get_disk_serial, is_ssd, erase_disk_crypto
from disk_partition import partition_disk
from disk_format import format_disk
from log_handler import log_info, log_error, log_erase_operation

def process_disk(disk: str, fs_choice: str, passes: int, use_crypto: bool = False, crypto_fill: str = "random", log_func=None) -> None:
    """
    Traiter un seul disque : l'effacer, le partitionner et le formater.
    
    Args:
        disk: Le nom du disque (ex: 'sda')
        fs_choice: Choix du système de fichiers pour le formatage
        passes: Nombre de passes pour l'effacement sécurisé
        use_crypto: Utiliser ou non la méthode d'effacement cryptographique
        crypto_fill: Méthode de remplissage pour l'effacement crypto ('random' ou 'zero')
        log_func: Fonction optionnelle pour l'enregistrement de la progression
    """
    try:
        disk_id = get_disk_serial(disk)
        log_info(f"Traitement de l'identifiant de disque : {disk_id}")
        if log_func:
            log_func(f"Traitement de l'identifiant de disque : {disk_id}")
        
        # Vérifier si le disque est un SSD et enregistrer un avertissement
        if is_ssd(disk) and not use_crypto:
            log_info(f"ATTENTION : {disk_id} est un SSD. L'effacement multi-passes peut ne pas effacer de manière sécurisée toutes les données.")
            if log_func:
                log_func(f"ATTENTION : {disk_id} est un SSD. L'effacement multi-passes peut ne pas effacer de manière sécurisée toutes les données.")
        
        # Effacer le disque en utilisant la méthode sélectionnée
        if use_crypto:
            method_str = f"Effacement cryptographique avec remplissage {crypto_fill}"
            log_info(f"Utilisation de l'effacement cryptographique (remplissage {crypto_fill}) pour l'ID de disque : {disk_id}")
            if log_func:
                log_func(f"Utilisation de l'effacement cryptographique (remplissage {crypto_fill}) pour l'ID de disque : {disk_id}")
            erase_result = erase_disk_crypto(disk, filling_method=crypto_fill, log_func=log_func)
        else:
            method_str = f"{passes} passes d'écrasement"
            log_info(f"Utilisation de l'effacement standard multi-passes pour l'ID de disque : {disk_id}")
            if log_func:
                log_func(f"Utilisation de l'effacement standard multi-passes pour l'ID de disque : {disk_id}")
            erase_result = erase_disk_hdd(disk, passes, log_func=log_func)
        
        log_info(f"Effacement terminé sur l'ID de disque : {disk_id}")
        if log_func:
            log_func(f"Effacement terminé sur l'ID de disque : {disk_id}")
        
        log_info(f"Création de partition sur l'ID de disque : {disk_id}")
        if log_func:
            log_func(f"Création de partition sur l'ID de disque : {disk_id}")
        
        partition_disk(disk)
        
        log_info("Attente de la reconnaissance de la partition...")
        if log_func:
            log_func("Attente de la reconnaissance de la partition...")
        
        time.sleep(5)  # Attendre que le système reconnaisse la nouvelle partition
        
        log_info(f"Formatage de l'ID de disque : {disk_id} avec {fs_choice}")
        if log_func:
            log_func(f"Formatage de l'ID de disque : {disk_id} avec {fs_choice}")
        
        format_disk(disk, fs_choice)
        
        log_erase_operation(disk_id, fs_choice, method_str)
        
        log_info(f"Opérations terminées sur l'ID de disque : {disk_id}")
        if log_func:
            log_func(f"Opérations terminées sur l'ID de disque : {disk_id}")
        
        
    except FileNotFoundError as e:
        log_error(f"Commande requise introuvable : {str(e)}")
        if log_func:
            log_func(f"Commande requise introuvable : {str(e)}")
        raise
    except CalledProcessError as e:
        log_error(f"Échec de l'exécution de la commande pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Échec de l'exécution de la commande pour le disque {disk} : {str(e)}")
        raise
    except PermissionError as e:
        log_error(f"Permission refusée pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Permission refusée pour le disque {disk} : {str(e)}")
        raise
    except OSError as e:
        log_error(f"Erreur OS pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Erreur OS pour le disque {disk} : {str(e)}")
        raise
    except KeyboardInterrupt:
        log_error(f"Traitement du disque {disk} interrompu par l'utilisateur")
        if log_func:
            log_func(f"Traitement du disque {disk} interrompu par l'utilisateur")
        raise
    except ImportError as e:
        log_error(f"Module requis introuvable pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Module requis introuvable pour le disque {disk} : {str(e)}")
        raise
    except AttributeError as e:
        log_error(f"Fonction ou méthode non disponible pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Fonction ou méthode non disponible pour le disque {disk} : {str(e)}")
        raise
    except TypeError as e:
        log_error(f"Type d'argument invalide pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Type d'argument invalide pour le disque {disk} : {str(e)}")
        raise
    except ValueError as e:
        log_error(f"Valeur d'argument invalide pour le disque {disk} : {str(e)}")
        if log_func:
            log_func(f"Valeur d'argument invalide pour le disque {disk} : {str(e)}")
        raise

def get_active_disk():
    """
    Détecter le périphérique actif qui soutient le système de fichiers racine.
    Retourne toujours une liste de noms de disques de base (ex: ['nvme0n1', 'sda']) ou None pour la cohérence.
    Utilise la logique LVM si le périphérique racine est un volume logique (/dev/mapper/),
    sinon utilise la logique de détection de disque régulière incluant la détection des médias de démarrage live.
    Tous les périphériques retournés sont résolus à leur disque de base.
    """
    try:
        # Initialiser l'ensemble des périphériques pour collecter tous les périphériques actifs
        devices = set()
        live_boot_found = False
        
        # Étape 1 : Vérifier /proc/mounts pour tous les périphériques montés
        with open('/proc/mounts', 'r') as f:
            mounts_content = f.read()
            
            # Chercher le montage du système de fichiers racine
            root_device = None
            for line in mounts_content.split('\n'):
                if line.strip() and ' / ' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        root_device = parts[0]
                        break

        # Étape 2 : Gérer les cas spéciaux de démarrage live où la racine n'est pas un vrai périphérique
        if not root_device or root_device in ['rootfs', 'overlay', 'aufs', '/dev/root']:
            
            # En démarrage live, chercher le média de démarrage réel dans /proc/mounts
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 6:
                        device = parts[0]
                        mount_point = parts[1]
                        
                        # Chercher les points de montage communs du démarrage live
                        if any(keyword in mount_point for keyword in ['/run/live', '/lib/live', '/live/', '/cdrom']):
                            match = re.search(r'/dev/([a-zA-Z]+\d*[a-zA-Z]*\d*)', device)
                            if match:
                                device_name = match.group(1)
                                base_device = get_base_disk(device_name)
                                devices.add(base_device)
                                live_boot_found = True
                        
                        # Vérifier aussi les périphériques USB/amovibles
                        elif device.startswith('/dev/') and any(keyword in device for keyword in ['sd', 'nvme', 'mmc']):
                            if '/media' in mount_point or '/mnt' in mount_point or '/run' in mount_point:
                                match = re.search(r'/dev/([a-zA-Z]+\d*[a-zA-Z]*\d*)', device)
                                if match:
                                    device_name = match.group(1)
                                    base_device = get_base_disk(device_name)
                                    devices.add(base_device)
            
            # Si rien trouvé, fallback : utiliser df
            if not devices:
                try:
                    output = run_command(["df", "-h"])
                    lines = output.strip().split('\n')
                    
                    for line in lines[1:]:  # Ignorer l'en-tête
                        parts = line.split()
                        if len(parts) >= 6:
                            device = parts[0]
                            mount_point = parts[5]
                            
                            if device.startswith('/dev/') and any(keyword in device for keyword in ['sd', 'nvme', 'mmc']):
                                match = re.search(r'/dev/([a-zA-Z]+\d*[a-zA-Z]*\d*)', device)
                                if match:
                                    device_name = match.group(1)
                                    base_device = get_base_disk(device_name)
                                    devices.add(base_device)
                except (FileNotFoundError, CalledProcessError) as e:
                    log_error(f"Erreur lors de l'exécution de la commande df : {str(e)}")
        
        else:
            # Étape 3 : Périphérique racine normal
            if '/dev/mapper/' in root_device or '/dev/dm-' in root_device:
                # Résolution LVM - trouver les disques physiques
                active_physical_drives = get_physical_drives_for_logical_volumes([root_device])
                
                for drive in active_physical_drives:
                    base_device = get_base_disk(drive)
                    devices.add(base_device)
                    
            else:
                # Disque régulier - extraire le nom du périphérique avec regex
                match = re.search(r'/dev/([a-zA-Z]+\d*[a-zA-Z]*\d*)', root_device)
                if match:
                    device_name = match.group(1)
                    base_device = get_base_disk(device_name)
                    devices.add(base_device)
            
            # Vérifier aussi les médias de démarrage live
            try:
                output = run_command(["df", "-h"])
                lines = output.strip().split('\n')
                
                for line in lines[1:]:  # Ignorer l'en-tête
                    parts = line.split()
                    if len(parts) >= 6:
                        device = parts[0]
                        mount_point = parts[5]
                        
                        if "/run/live" in mount_point or "/lib/live" in mount_point:
                            match = re.search(r'/dev/([a-zA-Z]+\d*[a-zA-Z]*\d*)', device)
                            if match:
                                device_name = match.group(1)
                                base_device = get_base_disk(device_name)
                                devices.add(base_device)
                                live_boot_found = True
            except (FileNotFoundError, CalledProcessError) as e:
                log_info(f"Impossible de vérifier les périphériques de démarrage live : {str(e)}")

        # Étape 4 : Logique de retour
        if devices:
            device_list = list(devices)
            
            # Si démarrage live trouvé, prioriser ces périphériques
            if live_boot_found:
                final_devices = [dev for dev in device_list if not dev.startswith('/dev/')]
                if final_devices:
                    return final_devices
            
            return device_list
        else:
            log_error("Aucun périphérique actif trouvé")
            return None

    except FileNotFoundError as e:
        log_error(f"Fichier requis introuvable : {str(e)}")
        return None
    except PermissionError as e:
        log_error(f"Permission refusée pour l'accès aux fichiers système : {str(e)}")
        return None
    except OSError as e:
        log_error(f"Erreur OS lors de l'accès aux informations système : {str(e)}")
        return None
    except CalledProcessError as e:
        log_error(f"Erreur lors de l'exécution de la commande : {str(e)}")
        return None
    except (IndexError, ValueError) as e:
        log_error(f"Erreur lors de l'analyse de la sortie de commande : {str(e)}")
        return None
    except re.error as e:
        log_error(f"Erreur de motif regex : {str(e)}")
        return None
    except KeyboardInterrupt:
        log_error("Opération interrompue par l'utilisateur")
        return None
    except UnicodeDecodeError as e:
        log_error(f"Erreur de décodage du contenu du fichier : {str(e)}")
        return None
    except MemoryError:
        log_error("Mémoire insuffisante pour traiter les informations des périphériques")
        return None