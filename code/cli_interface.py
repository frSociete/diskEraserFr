import sys
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from disk_operations import get_active_disk, process_disk
from utils import get_disk_list, choose_filesystem, get_base_disk
from log_handler import log_info, log_error, log_erase_operation, generate_session_pdf, generate_log_file_pdf

# Global session logs for PDF generation
session_logs = []

def add_session_log(message: str) -> None:
    """Add a message to session logs with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    session_logs.append(f"[{timestamp}] {message}")

def print_disk_details(disk):
    """Print detailed information about a disk."""
    try:
        disk_id = get_disk_serial(disk)
        is_disk_ssd = is_ssd(disk)
        active_disks = get_active_disk()
        
        # Get disk information from get_disk_list function including label
        disk_size = "Inconnu"
        disk_model = "Inconnu"
        disk_label = "Aucune étiquette"
        available_disks = get_disk_list()
        for available_disk in available_disks:
            # Handle both possible key formats from get_disk_list
            device_key = available_disk.get("device") or available_disk.get("Appareil")
            if device_key == f"/dev/{disk}":
                disk_size = available_disk.get("size") or available_disk.get("Taille", "Inconnu")
                disk_model = available_disk.get("model", "Inconnu")
                disk_label = available_disk.get("label", "Aucune étiquette")
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
        print(f"  Modèle: {disk_model}")
        print(f"  Étiquette: {disk_label}")
        print(f"  Type: {'Électronique' if is_disk_ssd else 'Mécanique'}")
        print(f"  Statut: {'DISQUE SYSTÈME ACTIF - DANGER!' if is_active else 'Effacement sans risque'}")
        
        if is_disk_ssd:
            print("  AVERTISSEMENT: Ceci est un périphérique électronique. L'effacement sécurisé à passages multiples:")
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
        # Handle both possible key formats from get_disk_list
        disk_names = []
        for disk in available_disks:
            device = disk.get("device") or disk.get("Appareil", "")
            if device:
                disk_names.append(device.replace("/dev/", ""))

        # Display summary table first
        print("\n" + "=" * 100)
        print("                          RÉSUMÉ DES DISQUES DISPONIBLES")
        print("=" * 100)
        print(f"{'Appareil':<12} {'Taille':<10} {'Modèle':<25} {'Étiquette':<20} {'Type':<12} {'Statut'}")
        print("-" * 100)
        
        for disk in disk_names:
            try:
                disk_id = get_disk_serial(disk)
                is_disk_ssd = is_ssd(disk)
                active_disks = get_active_disk()
                
                # Get disk information including label
                disk_size = "Inconnu"
                disk_model = "Inconnu"
                disk_label = "Aucune étiquette"
                for available_disk in available_disks:
                    device_key = available_disk.get("device") or available_disk.get("Appareil")
                    if device_key == f"/dev/{disk}":
                        disk_size = available_disk.get("size") or available_disk.get("Taille", "Inconnu")
                        disk_model = available_disk.get("model", "Inconnu")
                        disk_label = available_disk.get("label", "Aucune étiquette")
                        break
                
                is_active = False
                if active_disks:
                    base_disk = get_base_disk(disk)
                    for active_disk in active_disks:
                        active_base_disk = get_base_disk(active_disk)
                        if base_disk == active_base_disk:
                            is_active = True
                            break
                
                # Truncate long names for table display
                model_display = (disk_model[:23] + "..") if len(disk_model) > 25 else disk_model
                label_display = (disk_label[:18] + "..") if len(disk_label) > 20 else disk_label
                
                disk_type = "SSD" if is_disk_ssd else "HDD"
                status = "ACTIF!" if is_active else "Sûr"
                
                print(f"{disk:<12} {disk_size:<10} {model_display:<25} {label_display:<20} {disk_type:<12} {status}")
                
            except Exception as e:
                print(f"{disk:<12} Erreur lors de la récupération des informations du disque: {str(e)}")
        
        print("-" * 100)

        # Then iterate over disk_names for detailed view
        print("\n" + "=" * 60)
        print("                    INFORMATIONS DÉTAILLÉES DES DISQUES")
        print("=" * 60)
        
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

def confirm_erasure(disk: str, fs_choice: str, method_description: str) -> bool:
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
            print(f"Système de fichiers: {fs_choice}")
            print(f"Méthode: {method_description}")
            print("Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES!")
            
            confirmation = input(f"Êtes-vous sûr de vouloir effacer le disque {disk_id}? (oui/non): ").strip().lower()
            if confirmation == "oui":
                log_erase_operation(disk_id, fs_choice, method_description)

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

def get_disk_confirmations(disks: list[str], fs_choice: str, passes: int, use_crypto: bool, zero_fill: bool) -> list[str]:
    """Get confirmation for each disk with operation details."""
    if use_crypto:
        fill_method = "zéros" if zero_fill else "données aléatoires"
        method_description = f"effacement cryptographique (remplissage avec {fill_method})"
    else:
        method_description = f"effacement standard avec {passes} passage(s)"
    
    return [disk for disk in disks if confirm_erasure(disk, fs_choice, method_description)]

def print_log_menu() -> None:
    """Display and handle log printing options"""
    while True:
        try:
            print("\n" + "=" * 50)
            print("           OPTIONS D'IMPRESSION DES JOURNAUX")
            print("=" * 50)
            print("1. Imprimer le journal de session (session actuelle uniquement)")
            print("2. Imprimer le fichier de journal complet (tous les journaux historiques)")
            print("3. Retourner au menu principal")
            print("-" * 50)
            
            choice = input("Entrez votre choix (1-3): ").strip()
            
            if choice == "1":
                print_session_log_cli()
            elif choice == "2":
                print_complete_log_cli()
            elif choice == "3":
                break
            else:
                print("Choix invalide. Veuillez entrer 1, 2 ou 3.")
                
        except KeyboardInterrupt:
            print("\nRetour au menu principal...")
            break
        except (IOError, OSError) as e:
            print(f"Erreur: {str(e)}")

def print_session_log_cli() -> None:
    """Generate and save session log as PDF (CLI version)"""
    try:
        if not session_logs:
            print("Aucun journal de session disponible à imprimer!")
            return
        
        print("Génération du PDF du journal de session...")
        pdf_path = generate_session_pdf(session_logs)
        
        print(f"PDF du journal de session généré avec succès!")
        print(f"Sauvegardé dans: {pdf_path}")
        add_session_log(f"PDF du journal de session sauvegardé dans: {pdf_path}")
        
    except Exception as e:
        error_msg = f"Erreur lors de la génération du PDF du journal de session: {str(e)}"
        print(error_msg)
        log_error(error_msg)

def print_complete_log_cli() -> None:
    """Generate and save complete log file as PDF (CLI version)"""
    try:
        print("Génération du PDF du journal complet...")
        pdf_path = generate_log_file_pdf()
        
        print(f"PDF du journal complet généré avec succès!")
        print(f"Sauvegardé dans: {pdf_path}")
        add_session_log(f"PDF du journal complet sauvegardé dans: {pdf_path}")
        
    except Exception as e:
        error_msg = f"Erreur lors de la génération du PDF du journal complet: {str(e)}"
        print(error_msg)
        log_error(error_msg)

def cli_process_disk(disk, fs_choice, passes, use_crypto=False, zero_fill=False):
    """
    Process a single disk for the CLI interface with status output.
    
    This function wraps the process_disk function from disk_operations.py
    to provide CLI-specific logging and error handling.
    """
    try:
        # Get the disk identifier for better logging
        disk_id = get_disk_serial(disk)

        process_msg = f"Traitement du disque {disk_id} (/dev/{disk})"
        print(f"\n{process_msg}...")
        add_session_log(process_msg)
        
        # Define a logging function for the CLI
        def log_progress(message):
            print(f"  {message}")
            add_session_log(f"  {message}")
        
        # Indicate if the disk is an SSD and not using crypto
        if is_ssd(disk) and not use_crypto:
            warning_msg = f"ATTENTION: {disk_id} est un SSD - l'effacement à passages multiples peut ne pas être efficace"
            print(f"  {warning_msg}")
            add_session_log(warning_msg)
        
        # Process the disk using the imported function with crypto flag and filling method
        filling_method = "zero" if zero_fill else "random"
        process_disk(disk, fs_choice, passes, use_crypto, log_func=log_progress, crypto_fill=filling_method)
        
        success_msg = f"Toutes les opérations sur le disque {disk_id} ont été complétées avec succès"
        print(success_msg)
        add_session_log(success_msg)
        return True
    except (CalledProcessError, SubprocessError) as e:
        error_msg = f"Erreur lors du traitement du disque /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except IOError as e:
        error_msg = f"Erreur d'E/S lors du traitement du disque /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except OSError as e:
        error_msg = f"Erreur OS lors du traitement du disque /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except ValueError as e:
        error_msg = f"Erreur de valeur lors du traitement du disque /dev/{disk}: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False
    except KeyboardInterrupt:
        error_msg = f"Traitement du disque interrompu pour /dev/{disk}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)
        return False

def run_disk_erasure_operation(args):
    """Run the disk erasure operation workflow"""
    try:
        # First, list disks and select disks to erase
        print("Liste des disques disponibles:")
        disks = select_disks()
        if not disks:
            print("Aucun disque sélectionné. Sortie.")
            return
        
        # Get operation parameters
        fs_choice = args.filesystem or choose_filesystem()
        passes = args.passes
        use_crypto = args.crypto
        zero_fill = args.zero

        print(f"\nSystème de fichiers sélectionné: {fs_choice}")
        add_session_log(f"Système de fichiers sélectionné: {fs_choice}")
        
        if use_crypto:
            fill_method = "zéros" if zero_fill else "données aléatoires"
            method_msg = f"Méthode d'effacement: Effacement cryptographique (remplissage avec {fill_method})"
            print(method_msg)
            add_session_log(method_msg)
        else:
            method_msg = f"Méthode d'effacement: Standard avec {passes} passage(s)"
            print(method_msg)
            add_session_log(method_msg)
        
        # Get confirmation for each disk with detailed operation info
        confirmed_disks = get_disk_confirmations(disks, fs_choice, passes, use_crypto, zero_fill)
        if not confirmed_disks:
            print("Aucun disque confirmé pour effacement. Retour au menu principal.")
            return
        
        print("\nTous les disques confirmés. Démarrage des opérations...\n")
        operation_start_msg = f"Démarrage des opérations d'effacement de disque sur {len(confirmed_disks)} disque(s)"
        log_info(operation_start_msg)
        add_session_log(operation_start_msg)
        
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
                    error_msg = f"Erreur lors du traitement du disque: {str(e)}"
                    log_error(error_msg)
                    add_session_log(error_msg)
        
        completion_msg = f"Opérations terminées sur {completed}/{len(confirmed_disks)} disques."
        print(f"\n{completion_msg}")
        log_info(completion_msg)
        add_session_log(completion_msg)
        
    except KeyboardInterrupt:
        interrupt_msg = "Programme terminé par l'utilisateur (Ctrl+C)"
        print(f"\n{interrupt_msg}")
        add_session_log(interrupt_msg)
    except Exception as e:
        error_msg = f"Erreur lors de l'effacement du disque: {str(e)}"
        print(error_msg)
        log_error(error_msg)
        add_session_log(error_msg)

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
        print("         Effaceur Sécurisé de Disque - Interface en Ligne de Commande")
        print("=" * 60)
        
        # Initialize session log
        start_msg = "Interface CLI lancée"
        add_session_log(start_msg)
        print(f"Session démarrée à {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        while True:
            try:
                print("\n" + "=" * 50)
                print("                MENU PRINCIPAL")
                print("=" * 50)
                print("1. Démarrer l'opération d'effacement de disque")
                print("2. Options d'impression des journaux")
                print("3. Quitter")
                print("-" * 50)
                
                choice = input("Entrez votre choix (1-3): ").strip()
                
                if choice == "1":
                    # Disk erasure operation
                    run_disk_erasure_operation(args)
                
                elif choice == "2":
                    # Print log options
                    print_log_menu()
                
                elif choice == "3":
                    # Exit
                    exit_msg = "Session CLI terminée par l'utilisateur"
                    print(f"\n{exit_msg}")
                    add_session_log(exit_msg)
                    log_info(exit_msg)
                    break
                
                else:
                    print("Choix invalide. Veuillez entrer 1, 2 ou 3.")
                    
            except KeyboardInterrupt:
                interrupt_msg = "Opération du menu principal interrompue par l'utilisateur (Ctrl+C)"
                print(f"\n{interrupt_msg}")
                add_session_log(interrupt_msg)
                continue
                
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