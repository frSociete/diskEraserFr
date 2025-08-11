import subprocess
import logging
import sys
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_disk_serial(device: str) -> str:
    """
    Obtenir un identifiant stable du disque en utilisant udevadm pour extraire 
    le WWN ou le numéro de série d'un périphérique non monté.
    """
    try:
        # Essayer d'obtenir le WWN (World Wide Name) directement depuis udevadm
        output = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name=/dev/{device}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode()

        # Rechercher le WWN dans la sortie d'udevadm
        wwn_match = re.search(r'ID_WWN=(\S+)', output)
        if wwn_match:
            return wwn_match.group(1)

        # Si le WWN n'est pas trouvé, utiliser le numéro de série en fallback
        serial_match = re.search(r'ID_SERIAL_SHORT=(\S+)', output)
        if serial_match:
            return serial_match.group(1)
        
        # Obtenir le modèle comme fallback si le numéro de série n'est pas disponible
        model_match = re.search(r'ID_MODEL=(\S+)', output)
        if model_match:
            return f"{model_match.group(1)}_{device}"
            
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Erreur lors de la requête sur {device} : {e}")
    except KeyboardInterrupt:
        logging.error("Identification du disque interrompue par l'utilisateur (Ctrl+C)")
        print("\nIdentification du disque interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)

    # Si tout échoue, retourner un identifiant par défaut
    return f"INCONNU_{device}"

def is_ssd(device: str) -> bool:
    try:
        output = subprocess.run(
            ["cat", f"/sys/block/{device}/queue/rotational"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output.stdout.decode().strip() == "0"
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logging.warning(f"Vérification SSD échouée pour {device} : {e}")
        # Ne pas quitter, juste retourner False par défaut
        return False
    except KeyboardInterrupt:
        logging.error("Vérification SSD interrompue par l'utilisateur (Ctrl+C)")
        print("\nVérification SSD interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)

def erase_disk_hdd(device: str, passes: int, log_func=None) -> str:
    try:
        # Conversion de type pour s'assurer des types corrects
        device = str(device)
        passes = int(passes)

        # Obtenir l'identifiant stable du disque avant l'effacement
        disk_serial = get_disk_serial(device)

        if is_ssd(device):
            logging.warning(f"Attention : {device} semble être un SSD. Plusieurs passes peuvent ne pas être efficaces.")
            # Continuer avec l'effacement au lieu de retourner

        logging.info(f"Effacement de {device} en utilisant shred avec {passes} passes...")
        # Enregistrer aussi dans l'interface graphique si log_func est fourni
        if log_func:
            log_func(f"Effacement de {device} en utilisant shred avec {passes} passes...")
        
        # Créer un sous-processus avec stdout redirigé pour capturer la sortie de shred
        shred_process = subprocess.Popen(
            ["shred", "-n", f"{passes}", "-v", f"/dev/{device}"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )

        # Lire la sortie en temps réel
        while True:
            try:
                output = shred_process.stdout.readline()
                if output == '' and shred_process.poll() is not None:
                    break
                if output:
                    # Si une fonction de log est fournie (comme dans l'interface graphique), l'utiliser
                    # Sinon, afficher sur stdout
                    if log_func:
                        log_func(output.strip())
                    else:
                        print(output.strip())
            except KeyboardInterrupt:
                # Terminer le processus shred si l'utilisateur interrompt
                shred_process.terminate()
                logging.error("Effacement du disque interrompu par l'utilisateur (Ctrl+C)")
                print("\nEffacement du disque interrompu par l'utilisateur (Ctrl+C)")
                sys.exit(130)

        # Vérifier le code de retour
        if shred_process.returncode != 0:
            raise subprocess.CalledProcessError(shred_process.returncode, "shred")

        # Enregistrer l'effacement de la table de partitions dans le fichier de log et l'interface graphique
        wipe_message = f"Effacement de la table de partitions de {device} avec dd..."
        logging.info(wipe_message)
        if log_func:
            log_func(wipe_message)
            
        # Exécuter la commande dd
        subprocess.run(["dd", "if=/dev/zero", f"of=/dev/{device}", "bs=1M", "count=10"], check=True)

        # Enregistrer le message de succès dans le fichier de log et l'interface graphique
        success_message = f"Disque {device} effacé avec succès."
        logging.info(success_message)
        if log_func:
            log_func(success_message)
            
        return disk_serial
    except FileNotFoundError:
        error_message = "Erreur : Commande requise introuvable."
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur : Échec de l'effacement de {device} : {e}"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(1)
    except KeyboardInterrupt:
        error_message = "Effacement du disque interrompu par l'utilisateur (Ctrl+C)"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        print(f"\n{error_message}")
        sys.exit(130)

def erase_disk_crypto(device: str, filling_method: str = "random", log_func=None) -> bool:
    """
    Effacer de manière sécurisée un disque en utilisant l'effacement cryptographique :
    chiffrer tout le disque avec une clé aléatoire, puis supprimer la clé rendant
    les données irrécupérables.
    
    Args:
        device (str): Nom du périphérique (sans préfixe /dev/, ex: 'sda')
        filling_method (str): Méthode de remplissage - "random" ou "zero"
        log_func (callable, optional): Fonction pour enregistrer la sortie en temps réel (ex: pour interface graphique)
        
    Returns:
        str: Numéro de série du disque ou identifiant
        
    Raises:
        Diverses exceptions si le processus d'effacement échoue
    """
    try:
        # Obtenir l'identifiant stable du disque avant l'effacement
        disk_serial = get_disk_serial(device)
        
        # Enregistrer le message de début
        start_message = f"Démarrage de l'effacement cryptographique de {device}..."
        logging.info(start_message)
        if log_func:
            log_func(start_message)
        
        # Étape 1 : Créer une clé de chiffrement aléatoire et la stocker temporairement
        key_creation_msg = "Génération d'une clé de chiffrement aléatoire..."
        logging.info(key_creation_msg)
        if log_func:
            log_func(key_creation_msg)
            
        # Créer un fichier clé temporaire avec des données aléatoires
        subprocess.run(
            ["dd", "if=/dev/urandom", "of=/tmp/temp_keyfile", "bs=512", "count=8"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Étape 2 : Utiliser cryptsetup pour chiffrer tout le disque avec LUKS
        encrypt_msg = f"Chiffrement de {device} avec LUKS en utilisant une clé aléatoire..."
        logging.info(encrypt_msg)
        if log_func:
            log_func(encrypt_msg)
            
        # Créer un conteneur LUKS (cela détruira toutes les données sur le périphérique)
        cryptsetup_process = subprocess.Popen(
            ["cryptsetup", "-q", "--batch-mode", "luksFormat", 
             f"/dev/{device}", "/tmp/temp_keyfile"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Lire la sortie en temps réel
        while True:
            try:
                output = cryptsetup_process.stdout.readline()
                if output == '' and cryptsetup_process.poll() is not None:
                    break
                if output:
                    if log_func:
                        log_func(output.strip())
                    else:
                        print(output.strip())
            except KeyboardInterrupt:
                cryptsetup_process.terminate()
                logging.error("Chiffrement interrompu par l'utilisateur (Ctrl+C)")
                print("\nChiffrement interrompu par l'utilisateur (Ctrl+C)")
                sys.exit(130)
        
        # Vérifier le code de retour
        if cryptsetup_process.returncode != 0:
            raise subprocess.CalledProcessError(cryptsetup_process.returncode, "cryptsetup")
        
        # Étape 3 : Remplir le volume chiffré avec des zéros ou des données aléatoires pour plus de sécurité
        fill_msg = "Ouverture du périphérique chiffré pour le remplir avec des données..."
        logging.info(fill_msg)
        if log_func:
            log_func(fill_msg)
            
        # Ouvrir le périphérique chiffré
        subprocess.run(
            ["cryptsetup", "open", "--key-file", "/tmp/temp_keyfile", 
             f"/dev/{device}", f"temp_{device}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # CORRIGÉ : Gérer correctement la sélection de la méthode de remplissage
        if filling_method == "random":
            fill_data_msg = "Remplissage du périphérique chiffré avec des données aléatoires (cela peut prendre du temps)..."
            logging.info(fill_data_msg)
            if log_func:
                log_func(fill_data_msg)
                
            fill_process = subprocess.Popen(
                ["dd", "if=/dev/urandom", f"of=/dev/mapper/temp_{device}", 
                "bs=4M", "status=progress"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
        else:  # méthode de remplissage "zero"
            fill_data_msg = "Remplissage du périphérique chiffré avec des zéros (cela peut prendre du temps)..."
            logging.info(fill_data_msg)
            if log_func:
                log_func(fill_data_msg)
                
            fill_process = subprocess.Popen(
                ["dd", "if=/dev/zero", f"of=/dev/mapper/temp_{device}", 
                "bs=4M", "status=progress"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
        # Lire la sortie en temps réel pour afficher la progression
        while True:
            try:
                output = fill_process.stdout.readline()
                if output == '' and fill_process.poll() is not None:
                    break
                if output:
                    if log_func:
                        log_func(output.strip())
                    else:
                        print(output.strip())
            except KeyboardInterrupt:
                fill_process.terminate()
                logging.error("Opération de remplissage interrompue par l'utilisateur (Ctrl+C)")
                print("\nOpération de remplissage interrompue par l'utilisateur (Ctrl+C)")
                # S'assurer de fermer le périphérique mapper avant de quitter
                subprocess.run(["cryptsetup", "close", f"temp_{device}"], 
                               check=False)
                sys.exit(130)
        
        # Étape 4 : Fermer le périphérique chiffré
        close_msg = "Fermeture du périphérique chiffré..."
        logging.info(close_msg)
        if log_func:
            log_func(close_msg)
            
        subprocess.run(
            ["cryptsetup", "close", f"temp_{device}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Étape 5 : Supprimer de manière sécurisée le fichier clé
        key_delete_msg = "Effacement sécurisé de la clé de chiffrement..."
        logging.info(key_delete_msg)
        if log_func:
            log_func(key_delete_msg)
            
        subprocess.run(
            ["shred", "-u", "-z", "-n", "3", "/tmp/temp_keyfile"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Étape 6 : Optionnellement, écraser l'en-tête LUKS pour empêcher toute chance de récupération
        header_msg = "Écrasement de l'en-tête LUKS pour empêcher toute possibilité de récupération de clé..."
        logging.info(header_msg)
        if log_func:
            log_func(header_msg)
            
        subprocess.run(
            ["dd", "if=/dev/urandom", f"of=/dev/{device}", "bs=1M", "count=10"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Enregistrer le message de succès avec la méthode de remplissage correcte
        fill_method_str = "données aléatoires" if filling_method == "random" else "données zéro"
        success_message = f"Disque {device} effacé avec succès en utilisant la méthode cryptographique avec remplissage de {fill_method_str}."
        logging.info(success_message)
        if log_func:
            log_func(success_message)
            
        return disk_serial
        
    except FileNotFoundError as e:
        error_message = f"Erreur : Commande requise introuvable : {e}"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur : Échec de l'effacement cryptographique de {device} : {e}"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        sys.exit(1)
    except KeyboardInterrupt:
        error_message = "Effacement cryptographique interrompu par l'utilisateur (Ctrl+C)"
        logging.error(error_message)
        if log_func:
            log_func(error_message)
        print(f"\n{error_message}")
        sys.exit(130)
    finally:
        # Nettoyage en cas d'erreurs
        try:
            # Vérifier si le périphérique mapper existe et le fermer s'il existe
            result = subprocess.run(
                ["dmsetup", "info", f"temp_{device}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if result.returncode == 0:
                subprocess.run(["cryptsetup", "close", f"temp_{device}"], check=False)
                
            # Supprimer le fichier clé s'il existe encore
            if Path("/tmp/temp_keyfile").exists():
                subprocess.run(["shred", "-u", "-z", "-n", "3", "/tmp/temp_keyfile"], check=False)
        except subprocess.SubprocessError as e:
            logging.error(f"Erreur de sous-processus lors du nettoyage : {e}")
        except FileNotFoundError as e:
            logging.error(f"Commande requise introuvable lors du nettoyage : {e}")
        except PermissionError as e:
            logging.error(f"Erreur de permission lors du nettoyage : {e}")
        except OSError as e:
            logging.error(f"Erreur OS lors du nettoyage : {e}")