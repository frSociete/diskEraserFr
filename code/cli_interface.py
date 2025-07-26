import sys
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from disk_operations import get_active_disk, process_disk
from utils import get_disk_list, choose_filesystem, get_base_disk
from log_handler import log_info, log_error

def print_disk_details(disk):
    """Print detailed information about a disk."""
    try:
        disk_id = get_disk_serial(disk)
        is_disk_ssd = is_ssd(disk)
        active_disks = get_active_disk()
        
        # Get disk size from get_disk_list function
        disk_size = "Inconnu"
        available_disks = get_disk_list()
        for available_disk in available_disks:
            if available_disk["device"] == f"/dev/{disk}":
                disk_size = available_disk["size"]
                break
        
        is_active = False
        if active_disks:
            # get_active_disk() now always returns a list of physical disk names with LVM already resolved
            base_disk = get_base_disk(disk)
            for active_disk in active_disks:
                active_base_disk = get_base_disk(active_disk)
                if base_disk == active_base_disk:
                    is_active = True
                    break
        

        print(f"Disque: /dev/{disk}")
        print(f"  Numéro de série/ID: {disk_id}")
        print(f"  Taille: {disk_size}")
        print(f"  Type: {'SSD' if is_disk_ssd else 'HDD'}")
        print(f"  Statut: {'DISQUE SYSTÈME ACTIF - DANGER!' if is_active else 'Effacement sans risque'}")
        
        if is_disk_ssd:
            print("  AVERTISSEMENT: Ceci est un périphérique SSD. L'effacement sécurisé à passages multiples:")
            print("    • Peut endommager le SSD en provoquant une usure excessive")
            print("    • Peut ne pas effacer en toute sécurité toutes les données en raison de la répartition d'usure du SSD")
            print("    • Peut ne pas réécrire tous les secteurs en raison du sur-provisionnement")
            print("    • Les outils d'effacement sécurisés fournis par le fabricant sont recommandés")
        
        if is_active:
            print("  DANGER: C'est le DISQUE SYSTÈME ACTIF! Son effacement rendra votre système inutilisable.")
            print("          Le système va planter si vous procédez à l'effacement de ce disque.")
            
        return disk_id, is_disk_ssd, is_active
    except (SubprocessError, FileNotFoundError) as e:
        print(f"Erreur lors de l'obtention des détails du disque: {str(e)}")
        log_error(f"Erreur lors de l'obtention des détails pour {disk}: {str(e)}")
        return f"inconnu_{disk}", False, False

def select_disks() -> list[str]:
    """
    Let the user select disks to erase from the command line, with detailed information.
    """
    try:

        available_disks = get_disk_list()
        disk_names = [disk["device"].replace("/dev/", "") for disk in available_disks]

        # Then iterate over disk_names
        for disk in disk_names:
            print("\n" + "-" * 50)
            print_disk_details(disk)
            
        print("\n" + "-" * 50)
        print("\nATTENTION: Cet outil va COMPLÈTEMENT EFFACER les disques sélectionnés. TOUTES LES DONNÉES SERONT PERDUES!")
        print("ATTENTION: Si l'un de ces disques est un SSD, l'utilisation de cet outil avec plusieurs passages peut endommager le SSD.")
        print("Pour les SSD, les outils d'effacement sécurisés fournis par le fabricant sont recommandés.\n")
        
        selected_disks = input("Entrez les disques à effacer (séparés par des virgules, ex: sda,sdb): ").strip()
        disk_names = [disk.strip() for disk in selected_disks.split(",") if disk.strip()]
        
        valid_disks = []
        for disk in disk_names:
            if re.match(r'^[a-zA-Z]+[0-9]*$', disk):
                disk_path = f"/dev/{disk}"
                if os.path.exists(disk_path):
                    valid_disks.append(disk)
                else:
                    print(f"Disque {disk_path} introuvable. Ignoré.")
            else:
                print(f"Format de nom de disque invalide: {disk}. Ignoré.")
        
        return valid_disks
        
    except KeyboardInterrupt:
        log_error("Sélection de disque interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)
    except IOError as e:
        log_error(f"Erreur d'E/S: {str(e)}")
        return []

def confirm_erasure(disk: str) -> bool:
    """
    Get confirmation to erase a specific disk with detailed warnings.
    """
    while True:
        try:
            print("\n" + "-" * 50)
            disk_id, is_disk_ssd, is_active = print_disk_details(disk)
            print("-" * 50)
            
            if is_disk_ssd:
                print("\nATTENTION: Ce disque est un SSD. L'effacement sécurisé n'est pas garanti.")
                print("           Les passages multiples peuvent endommager le SSD.")
                
            if is_active:
                print("\nDANGER: C'est le DISQUE SYSTÈME ACTIF! Son effacement rendra votre système inutilisable.")
                print("        Le système va PLANTER si vous procédez à l'effacement de ce disque.")
                
            print(f"\nVous êtes sur le point d'EFFACER DÉFINITIVEMENT le disque {disk_id} (/dev/{disk}).")
            print("Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES!")
            
            confirmation = input(f"Êtes-vous sûr de vouloir effacer le disque {disk_id}? (oui/non): ").strip().lower()
            if confirmation == "oui":
                # For active system disks, require a second confirmation
                if is_active:
                    second_confirm = input("AVERTISSEMENT FINAL: Vous êtes sur le point d'effacer le DISQUE SYSTÈME ACTIF. Tapez 'DÉTRUIRE' pour confirmer: ").strip()
                    return second_confirm == "DÉTRUIRE"
                return True
            elif confirmation == "non":
                return False
            print("Entrée invalide. Entrez 'oui' ou 'non'.")
        except KeyboardInterrupt:
            log_error("Confirmation d'effacement interrompue par l'utilisateur (Ctrl+C)")
            sys.exit(130)

def get_disk_confirmations(disks: list[str]) -> list[str]:
    """Get confirmation for each disk."""
    return [disk for disk in disks if confirm_erasure(disk)]

def cli_process_disk(disk, fs_choice, passes, use_crypto=False, zero_fill=False):
    """
    Process a single disk for the CLI interface with status output.
    
    This function wraps the process_disk function from disk_operations.py
    to provide CLI-specific logging and error handling.
    """
    try:
        # Get the disk identifier for better logging
        disk_id = get_disk_serial(disk)
        print(f"\nTraitement du disque {disk_id} (/dev/{disk})...")
        
        # Define a logging function for the CLI
        def log_progress(message):
            print(f"  {message}")
        
        # Indicate if the disk is an SSD and not using crypto
        if is_ssd(disk) and not use_crypto:
            print(f"  ATTENTION: {disk_id} est un SSD - l'effacement à passages multiples peut ne pas être efficace")
        
        # Process the disk using the imported function with crypto flag and filling method
        filling_method = "zero" if zero_fill else "random"
        process_disk(disk, fs_choice, passes, use_crypto, log_func=log_progress, crypto_fill=filling_method)
        
        print(f"Toutes les opérations sur le disque {disk_id} ont été complétées avec succès")
        return True
    except (CalledProcessError, SubprocessError) as e:
        print(f"Erreur lors du traitement du disque /dev/{disk}: {str(e)}")
        log_error(f"Erreur lors du traitement du disque /dev/{disk}: {str(e)}")
        return False
    except IOError as e:
        print(f"Erreur d'E/S lors du traitement du disque /dev/{disk}: {str(e)}")
        log_error(f"Erreur d'E/S lors du traitement du disque /dev/{disk}: {str(e)}")
        return False
    except OSError as e:
        print(f"Erreur OS lors du traitement du disque /dev/{disk}: {str(e)}")
        log_error(f"Erreur OS lors du traitement du disque /dev/{disk}: {str(e)}")
        return False
    except ValueError as e:
        print(f"Erreur de valeur lors du traitement du disque /dev/{disk}: {str(e)}")
        log_error(f"Erreur de valeur lors du traitement du disque /dev/{disk}: {str(e)}")
        return False
    except KeyboardInterrupt:
        print(f"Traitement du disque interrompu pour /dev/{disk}")
        log_error(f"Traitement du disque interrompu pour /dev/{disk}")
        return False

def run_cli_mode(args):
    """
    Run the command-line interface version with detailed disk information.
    """
    try:
        # Check for root privileges
        if os.geteuid() != 0:
            print("Erreur: Ce programme doit être exécuté en tant que root!")
            sys.exit(1)
            
        print("=" * 60)
        print("         EFFACEUR DE DISQUE SÉCURISÉ - INTERFACE EN LIGNE DE COMMANDE")
        print("=" * 60)
        
        # First, list disks and select disks to erase
        print("Liste des disques disponibles: ")
        disks = select_disks()
        if not disks:
            print("Aucun disque sélectionné. Sortie.")
            return
        
        # Then, get confirmation for each disk
        confirmed_disks = get_disk_confirmations(disks)
        if not confirmed_disks:
            print("Aucun disque confirmé pour effacement. Sortie.")
            return
        
        # Finally, choose filesystem and number of passes
        fs_choice = args.filesystem or choose_filesystem()
        passes = args.passes
        use_crypto = args.crypto
        zero_fill = args.zero
        
        print(f"Système de fichiers sélectionné: {fs_choice}")
        
        if use_crypto:
            fill_method = "zéros" if zero_fill else "données aléatoires"
            print(f"Méthode d'effacement: Effacement cryptographique (remplissage avec {fill_method})")
        else:
            print(f"Méthode d'effacement: Standard avec {passes} passages")
        
        print("\nTous les disques confirmés. Démarrage des opérations...\n")
        log_info(f"Démarrage des opérations d'effacement de disque sur {len(confirmed_disks)} disque(s)")
        
        with ThreadPoolExecutor() as executor:
            # Use our cli_process_disk function with the crypto flag and zero_fill option
            futures = [executor.submit(cli_process_disk, disk, fs_choice, passes, use_crypto, zero_fill) for disk in confirmed_disks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except (RuntimeError, ValueError) as e:
                    log_error(f"Erreur lors du traitement du disque: {str(e)}")
        
        print(f"\nOpérations terminées sur {completed}/{len(confirmed_disks)} disques.")
        log_info(f"Opérations terminées sur {completed}/{len(confirmed_disks)} disques.")
        
    except KeyboardInterrupt:
        log_error("Programme terminé par l'utilisateur (Ctrl+C)")
        sys.exit(130)
    except IOError as e:
        log_error(f"Erreur d'E/S: {str(e)}")
        sys.exit(1)
    except OSError as e:
        log_error(f"Erreur OS: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Erreur de valeur: {str(e)}")
        sys.exit(1)
    except SubprocessError as e:
        log_error(f"Erreur de sous-processus: {str(e)}")
        sys.exit(1)