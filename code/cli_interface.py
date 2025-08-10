import sys
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from disk_operations import get_active_disk, process_disk
from utils import get_disk_list, choose_filesystem, get_base_disk
from log_handler import (log_info, log_error, log_erase_operation, 
                        generate_session_pdf, generate_log_file_pdf, 
                        session_start, session_end, get_current_session_logs)

def print_disk_details(disk):
    """Affiche les informations détaillées d'un disque."""
    try:
        disk_id = get_disk_serial(disk)
        is_disk_ssd = is_ssd(disk)
        active_disks = get_active_disk()
        
        # Récupérer les informations du disque depuis la fonction get_disk_list incluant l'étiquette
        disk_size = "Inconnu"
        disk_model = "Inconnu"
        disk_label = "Sans étiquette"
        available_disks = get_disk_list()
        for available_disk in available_disks:
            if available_disk["device"] == f"/dev/{disk}":
                disk_size = available_disk["size"]
                disk_model = available_disk.get("model", "Inconnu")
                disk_label = available_disk.get("label", "Sans étiquette")
                break
        
        is_active = False
        if active_disks:
            # get_active_disk() retourne maintenant toujours une liste de noms de disques physiques avec LVM déjà résolu
            base_disk = get_base_disk(disk)
            for active_disk in active_disks:
                active_base_disk = get_base_disk(active_disk)
                if base_disk == active_base_disk:
                    is_active = True
                    break
        
        print(f"Disque : /dev/{disk}")
        print(f"  Série/ID : {disk_id}")
        print(f"  Taille : {disk_size}")
        print(f"  Modèle : {disk_model}")
        print(f"  Étiquette : {disk_label}")
        print(f"  Type : {'SSD' if is_disk_ssd else 'Mécanique'}")
        print(f"  Statut : {'DISQUE SYSTÈME ACTIF - DANGER!' if is_active else 'Sûr à effacer'}")
        
        if is_disk_ssd:
            print("  AVERTISSEMENT : Ceci est un disque SSD. L'effacement sécurisé multi-passes :")
            print("    • Peut endommager le SSD en causant une usure excessive")
            print("    • Peut ne pas effacer toutes les données de manière sécurisée à cause du nivellement d'usure")
            print("    • Peut ne pas réécrire tous les secteurs à cause du surprovisionnement")
            print("    • Pour les SSD, l'effacement cryptographique est recommandé")
        
        if is_active:
            print("  DANGER : Ceci est le DISQUE SYSTÈME ACTIF ! L'effacer rendra votre système inutilisable.")
            print("          Le système plantera si vous continuez avec l'effacement de ce disque.")
            
        return disk_id, is_disk_ssd, is_active
    except (SubprocessError, FileNotFoundError) as e:
        print(f"Erreur lors de l'obtention des détails du disque : {str(e)}")
        log_error(f"Erreur lors de l'obtention des détails du disque pour {disk} : {str(e)}")
        return f"inconnu_{disk}", False, False
    except (OSError, IOError) as e:
        print(f"Erreur système lors de l'obtention des détails du disque : {str(e)}")
        log_error(f"Erreur système lors de l'obtention des détails du disque pour {disk} : {str(e)}")
        return f"inconnu_{disk}", False, False
    except (AttributeError, KeyError, IndexError) as e:
        print(f"Erreur de structure de données lors de l'obtention des détails du disque : {str(e)}")
        log_error(f"Erreur de structure de données lors de l'obtention des détails du disque pour {disk} : {str(e)}")
        return f"inconnu_{disk}", False, False
    except (TypeError, ValueError) as e:
        print(f"Erreur de type de données lors de l'obtention des détails du disque : {str(e)}")
        log_error(f"Erreur de type de données lors de l'obtention des détails du disque pour {disk} : {str(e)}")
        return f"inconnu_{disk}", False, False

def select_disks() -> list[str]:
    """
    Permet à l'utilisateur de sélectionner les disques à effacer depuis la ligne de commande, avec des informations détaillées.
    """
    try:
        available_disks = get_disk_list()
        disk_names = [disk["device"].replace("/dev/", "") for disk in available_disks]

        # Afficher d'abord le tableau de synthèse
        print("\n" + "=" * 80)
        print("                          RÉSUMÉ DES DISQUES DISPONIBLES")
        print("=" * 80)
        print(f"{'Périphérique':<12} {'Taille':<8} {'Modèle':<20} {'Étiquette':<15} {'Type':<12} {'Statut'}")
        print("-" * 80)
        
        for disk in disk_names:
            try:
                disk_id = get_disk_serial(disk)
                is_disk_ssd = is_ssd(disk)
                active_disks = get_active_disk()
                
                # Récupérer les informations du disque incluant l'étiquette
                disk_size = "Inconnu"
                disk_model = "Inconnu"
                disk_label = "Sans étiquette"
                for available_disk in available_disks:
                    if available_disk["device"] == f"/dev/{disk}":
                        disk_size = available_disk["size"]
                        disk_model = available_disk.get("model", "Inconnu")
                        disk_label = available_disk.get("label", "Sans étiquette")
                        break
                
                is_active = False
                if active_disks:
                    base_disk = get_base_disk(disk)
                    for active_disk in active_disks:
                        active_base_disk = get_base_disk(active_disk)
                        if base_disk == active_base_disk:
                            is_active = True
                            break
                
                # Tronquer les noms longs pour l'affichage du tableau
                model_display = (disk_model[:18] + "..") if len(disk_model) > 20 else disk_model
                label_display = (disk_label[:13] + "..") if len(disk_label) > 15 else disk_label
                
                disk_type = "SSD" if is_disk_ssd else "HDD"
                status = "ACTIF!" if is_active else "Sûr"
                
                print(f"{disk:<12} {disk_size:<8} {model_display:<20} {label_display:<15} {disk_type:<12} {status}")
                
            except (SubprocessError, OSError, IOError) as e:
                print(f"{disk:<12} Erreur système lors de la récupération des informations du disque : {str(e)}")
            except (FileNotFoundError, PermissionError) as e:
                print(f"{disk:<12} Erreur d'accès lors de la récupération des informations du disque : {str(e)}")
            except (AttributeError, KeyError, IndexError, TypeError, ValueError) as e:
                print(f"{disk:<12} Erreur de données lors de la récupération des informations du disque : {str(e)}")
        
        print("-" * 80)

        # Puis itérer sur disk_names pour la vue détaillée
        print("\n" + "=" * 60)
        print("                    INFORMATIONS DÉTAILLÉES DES DISQUES")
        print("=" * 60)
        
        for disk in disk_names:
            print("\n" + "-" * 50)
            print_disk_details(disk)
            
        print("\n" + "-" * 50)
        print("\nAVERTISSEMENT : Cet outil va COMPLÈTEMENT EFFACER les disques sélectionnés. TOUTES LES DONNÉES SERONT PERDUES !")
        print("AVERTISSEMENT : Si certains de ces disques sont des SSD, utiliser plusieurs passes peut endommager le SSD.")
        print("Pour les SSD, l'effacement cryptographique est recommandé.\n")
        
        selected_disks = input("Entrez les disques à effacer (séparés par des virgules, ex : sda,sdb) : ").strip()
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
                print(f"Format de nom de disque invalide : {disk}. Ignoré.")
        
        return valid_disks
        
    except KeyboardInterrupt:
        log_error("Sélection de disque interrompue par l'utilisateur (Ctrl+C)")
        sys.exit(130)
    except (IOError, OSError) as e:
        log_error(f"Erreur système lors de la sélection de disque : {str(e)}")
        return []
    except (AttributeError, TypeError) as e:
        log_error(f"Erreur de traitement des données lors de la sélection de disque : {str(e)}")
        return []

def get_erasure_method():
    """Obtient le choix de la méthode d'effacement de l'utilisateur"""
    while True:
        try:
            print("\n" + "=" * 50)
            print("            SÉLECTION DE LA MÉTHODE D'EFFACEMENT")
            print("=" * 50)
            print("1. Réécriture standard (passages multiples)")
            print("2. Effacement cryptographique (recommandé pour les SSD)")
            print("-" * 50)
            
            choice = input("Sélectionnez la méthode d'effacement (1-2) : ").strip()
            
            if choice == "1":
                return False, "random"  # use_crypto=False, crypto_fill n'a pas d'importance
            elif choice == "2":
                # Obtenir la méthode de remplissage crypto
                while True:
                    print("\n" + "=" * 40)
                    print("     MÉTHODE DE REMPLISSAGE CRYPTOGRAPHIQUE")
                    print("=" * 40)
                    print("1. Données aléatoires (recommandé)")
                    print("2. Données zéro")
                    print("-" * 40)
                    
                    fill_choice = input("Sélectionnez la méthode de remplissage (1-2) : ").strip()
                    
                    if fill_choice == "1":
                        return True, "random"  # use_crypto=True, crypto_fill="random"
                    elif fill_choice == "2":
                        return True, "zero"   # use_crypto=True, crypto_fill="zero"
                    else:
                        print("Choix invalide. Veuillez entrer 1 ou 2.")
            else:
                print("Choix invalide. Veuillez entrer 1 ou 2.")
                
        except KeyboardInterrupt:
            print("\nOpération annulée.")
            sys.exit(130)
        except (EOFError, IOError) as e:
            print(f"\nErreur d'entrée : {str(e)}")
            print("Opération annulée.")
            sys.exit(1)

def get_passes():
    """Obtient le nombre de passes pour la méthode de réécriture"""
    while True:
        try:
            passes_input = input("Entrez le nombre de passes pour la réécriture (défaut : 3) : ").strip()
            if not passes_input:
                return 3
            
            passes = int(passes_input)
            if passes < 1:
                print("Le nombre de passes doit être au moins 1.")
                continue
            elif passes > 20:
                print("Avertissement : Plus de 20 passes peut prendre beaucoup de temps.")
                confirm = input("Continuer ? (o/n) : ").strip().lower()
                if confirm not in ['o', 'oui']:
                    continue
            
            return passes
            
        except ValueError:
            print("Entrée invalide. Veuillez entrer un nombre valide.")
        except KeyboardInterrupt:
            print("\nOpération annulée.")
            sys.exit(130)
        except (EOFError, IOError) as e:
            print(f"\nErreur d'entrée : {str(e)}")
            print("Opération annulée.")
            sys.exit(1)

def confirm_erasure(disk: str, fs_choice: str, method_description: str) -> bool:
    """
    Obtient la confirmation pour effacer un disque spécifique avec des avertissements détaillés.
    """
    while True:
        try:
            print("\n" + "-" * 50)
            disk_id, is_disk_ssd, is_active = print_disk_details(disk)
            print("-" * 50)
            
            if is_disk_ssd and "réécriture" in method_description.lower():
                print("\nAVERTISSEMENT : Ce disque est un SSD. La réécriture multi-passes peut ne pas être efficace.")
                print("         Considérez utiliser l'effacement cryptographique à la place.")
                
            if is_active:
                print("\nDANGER : Ceci est le DISQUE SYSTÈME ACTIF ! L'effacer rendra votre système inutilisable.")
                print("        Le système va PLANTER si vous continuez avec l'effacement de ce disque.")
                
            print(f"\nVous êtes sur le point d'EFFACER DÉFINITIVEMENT le disque {disk_id} (/dev/{disk}).")
            print(f"Système de fichiers : {fs_choice}")
            print(f"Méthode : {method_description}")
            print("Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES !")
            
            confirmation = input(f"Êtes-vous sûr de vouloir effacer le disque {disk_id} ? (oui/non) : ").strip().lower()
            if confirmation == "oui":
                # Pour les disques système actifs, exiger une seconde confirmation
                if is_active:
                    second_confirm = input("DERNIER AVERTISSEMENT : Vous êtes sur le point d'effacer le DISQUE SYSTÈME ACTIF. Tapez 'DÉTRUIRE' pour confirmer : ").strip()
                    return second_confirm == "DÉTRUIRE"
                return True
            elif confirmation == "non":
                return False
            print("Entrée invalide. Entrez 'oui' ou 'non'.")
        except KeyboardInterrupt:
            log_error("Confirmation d'effacement interrompue par l'utilisateur (Ctrl+C)")
            sys.exit(130)
        except (EOFError, IOError) as e:
            log_error(f"Erreur d'entrée lors de la confirmation d'effacement : {str(e)}")
            return False

def get_disk_confirmations(disks: list[str], fs_choice: str, passes: int, use_crypto: bool, crypto_fill: str) -> list[str]:
    """Obtient la confirmation pour chaque disque avec les détails de l'opération."""
    if use_crypto:
        fill_method = "zéros" if crypto_fill == "zero" else "données aléatoires"
        method_description = f"effacement cryptographique (remplissage avec {fill_method})"
    else:
        method_description = f"réécriture standard en {passes} passes"
    
    return [disk for disk in disks if confirm_erasure(disk, fs_choice, method_description)]

def print_log_menu() -> None:
    """Affiche et gère les options d'impression des journaux"""
    while True:
        try:
            print("\n" + "=" * 50)
            print("            OPTIONS D'IMPRESSION DES JOURNAUX")
            print("=" * 50)
            print("1. Imprimer le journal de session (session actuelle uniquement)")
            print("2. Imprimer le fichier journal complet (tous les journaux historiques)")
            print("3. Retourner au menu principal")
            print("-" * 50)
            
            choice = input("Entrez votre choix (1-3) : ").strip()
            
            if choice == "1":
                print_session_log_cli()
            elif choice == "2":
                print_complete_log_cli()
            elif choice == "3":
                break
            else:
                print("Choix invalide. Veuillez entrer 1, 2, ou 3.")
                
        except KeyboardInterrupt:
            print("\nRetour au menu principal...")
            break
        except (EOFError, IOError, OSError) as e:
            print(f"Erreur d'entrée/sortie : {str(e)}")

def print_session_log_cli() -> None:
    """Génère et sauvegarde le journal de session en PDF (version CLI)"""
    try:
        # Utiliser la fonction mise à jour depuis log_handler
        session_logs = get_current_session_logs()
        if not session_logs:
            print("Aucun journal de session disponible à imprimer !")
            return
        
        print("Génération du PDF du journal de session...")
        pdf_path = generate_session_pdf()
        
        print(f"PDF du journal de session généré avec succès !")
        print(f"Sauvegardé dans : {pdf_path}")
        log_info(f"PDF du journal de session sauvegardé dans : {pdf_path}")
        
    except (FileNotFoundError, PermissionError) as e:
        error_msg = f"Erreur d'accès fichier lors de la génération du PDF du journal de session : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (IOError, OSError) as e:
        error_msg = f"Erreur système lors de la génération du PDF du journal de session : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (ImportError, AttributeError) as e:
        error_msg = f"Erreur de module/dépendance lors de la génération du PDF du journal de session : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (TypeError, ValueError) as e:
        error_msg = f"Erreur de traitement des données lors de la génération du PDF du journal de session : {str(e)}"
        print(error_msg)
        log_error(error_msg)

def print_complete_log_cli() -> None:
    """Génère et sauvegarde le fichier journal complet en PDF (version CLI)"""
    try:
        print("Génération du PDF du journal complet...")
        pdf_path = generate_log_file_pdf()
        
        print(f"PDF du journal complet généré avec succès !")
        print(f"Sauvegardé dans : {pdf_path}")
        log_info(f"PDF du journal complet sauvegardé dans : {pdf_path}")
        
    except (FileNotFoundError, PermissionError) as e:
        error_msg = f"Erreur d'accès fichier lors de la génération du PDF du journal complet : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (IOError, OSError) as e:
        error_msg = f"Erreur système lors de la génération du PDF du journal complet : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (ImportError, AttributeError) as e:
        error_msg = f"Erreur de module/dépendance lors de la génération du PDF du journal complet : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (TypeError, ValueError) as e:
        error_msg = f"Erreur de traitement des données lors de la génération du PDF du journal complet : {str(e)}"
        print(error_msg)
        log_error(error_msg)

def cli_process_disk(disk, fs_choice, passes, use_crypto=False, crypto_fill="random"):
    """
    Traite un seul disque pour l'interface CLI avec sortie de statut.
    
    Cette fonction encapsule la fonction process_disk depuis disk_operations.py
    pour fournir une journalisation et gestion d'erreur spécifiques à CLI.
    """
    try:
        # Obtenir l'identifiant du disque pour une meilleure journalisation
        disk_id = get_disk_serial(disk)
        process_msg = f"Traitement du disque {disk_id} (/dev/{disk})"
        print(f"\n{process_msg}...")
        log_info(process_msg)
        
        # Définir une fonction de journalisation pour la CLI
        def log_progress(message):
            print(f"  {message}")
        
        # Indiquer si le disque est un SSD et n'utilise pas la crypto
        if is_ssd(disk) and not use_crypto:
            warning_msg = f"AVERTISSEMENT : {disk_id} est un SSD - l'effacement multi-passes peut ne pas être efficace"
            print(f"  {warning_msg}")
            log_info(warning_msg)
        
        # Traiter le disque en utilisant la fonction importée avec le flag crypto et la méthode de remplissage
        process_disk(disk, fs_choice, passes, use_crypto, crypto_fill, log_func=log_progress)
        
        success_msg = f"Toutes les opérations terminées avec succès sur le disque {disk_id}"
        print(success_msg)
        log_info(success_msg)
        return True
    except (CalledProcessError, SubprocessError) as e:
        error_msg = f"Erreur d'exécution de commande lors du traitement du disque /dev/{disk} : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return False
    except (IOError, OSError) as e:
        error_msg = f"Erreur système lors du traitement du disque /dev/{disk} : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return False
    except (FileNotFoundError, PermissionError) as e:
        error_msg = f"Erreur d'accès lors du traitement du disque /dev/{disk} : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return False
    except (ValueError, TypeError) as e:
        error_msg = f"Erreur de validation des données lors du traitement du disque /dev/{disk} : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return False
    except (ImportError, AttributeError) as e:
        error_msg = f"Erreur de module/dépendance lors du traitement du disque /dev/{disk} : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        return False
    except KeyboardInterrupt:
        error_msg = f"Traitement de disque interrompu pour /dev/{disk}"
        print(error_msg)
        log_error(error_msg)
        return False

def run_disk_erasure_operation(args=None):
    """Exécute le workflow d'opération d'effacement de disque"""
    try:
        # D'abord, lister les disques et sélectionner les disques à effacer
        print("Liste des disques disponibles : ")
        disks = select_disks()
        if not disks:
            print("Aucun disque sélectionné. Retour au menu principal.")
            return
        
        # Obtenir les paramètres d'opération
        if args and args.filesystem:
            fs_choice = args.filesystem
        else:
            fs_choice = choose_filesystem()
            
        # Obtenir la méthode d'effacement
        if args and hasattr(args, 'crypto') and args.crypto:
            use_crypto = True
            crypto_fill = "zero" if (hasattr(args, 'zero') and args.zero) else "random"
            passes = 1  # Pas utilisé pour crypto
        else:
            use_crypto, crypto_fill = get_erasure_method()
            if use_crypto:
                passes = 1  # Pas utilisé pour crypto
            else:
                if args and args.passes:
                    passes = args.passes
                else:
                    passes = get_passes()
        
        print(f"Système de fichiers sélectionné : {fs_choice}")
        log_info(f"Système de fichiers sélectionné : {fs_choice}")
        
        if use_crypto:
            fill_method = "zéros" if crypto_fill == "zero" else "données aléatoires"
            method_msg = f"Méthode d'effacement : Effacement cryptographique (remplissage avec {fill_method})"
            print(method_msg)
            log_info(method_msg)
        else:
            method_msg = f"Méthode d'effacement : Standard avec {passes} passes"
            print(method_msg)
            log_info(method_msg)
        
        # Ensuite, obtenir la confirmation pour chaque disque avec les infos détaillées de l'opération
        confirmed_disks = get_disk_confirmations(disks, fs_choice, passes, use_crypto, crypto_fill)
        if not confirmed_disks:
            print("Aucun disque confirmé pour l'effacement. Retour au menu principal.")
            return
        
        print("\nTous les disques confirmés. Démarrage des opérations...\n")
        operation_start_msg = f"Démarrage des opérations d'effacement de disque sur {len(confirmed_disks)} disque(s)"
        log_info(operation_start_msg)
        
        with ThreadPoolExecutor() as executor:
            # Utiliser notre fonction cli_process_disk avec le flag crypto et l'option crypto_fill
            futures = [executor.submit(cli_process_disk, disk, fs_choice, passes, use_crypto, crypto_fill) for disk in confirmed_disks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        completed += 1
                except (RuntimeError, ValueError, TypeError) as e:
                    error_msg = f"Erreur d'exécution de thread lors du traitement du disque : {str(e)}"
                    log_error(error_msg)
                except (TimeoutError, InterruptedError) as e:
                    error_msg = f"Erreur de timeout/interruption de thread lors du traitement du disque : {str(e)}"
                    log_error(error_msg)
        
        completion_msg = f"Opérations terminées sur {completed}/{len(confirmed_disks)} disques."
        print(f"\n{completion_msg}")
        log_info(completion_msg)
        
    except KeyboardInterrupt:
        interrupt_msg = "Opération d'effacement de disque interrompue par l'utilisateur (Ctrl+C)"
        print(f"\n{interrupt_msg}")
        log_error(interrupt_msg)
    except (AttributeError, TypeError) as e:
        error_msg = f"Erreur de configuration/argument lors de l'opération d'effacement de disque : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (ImportError, ModuleNotFoundError) as e:
        error_msg = f"Erreur d'importation de module lors de l'opération d'effacement de disque : {str(e)}"
        print(error_msg)
        log_error(error_msg)
    except (OSError, IOError) as e:
        error_msg = f"Erreur système lors de l'opération d'effacement de disque : {str(e)}"
        print(error_msg)
        log_error(error_msg)

def run_cli_mode(args):
    """
    Exécute la version interface en ligne de commande avec des informations détaillées sur les disques.
    """
    try:
        # Vérifier les privilèges root
        if os.geteuid() != 0:
            print("Erreur : Ce programme doit être exécuté en tant que root !")
            sys.exit(1)
            
        print("=" * 60)
        print("         EFFACEUR DE DISQUE SÉCURISÉ - INTERFACE EN LIGNE DE COMMANDE")
        print("=" * 60)
        
        # Démarrer la journalisation de session
        session_start()
        
        # Initialiser le journal de session
        start_msg = "Session CLI démarrée"
        log_info(start_msg)
        print(f"Session démarrée le {time.strftime('%d/%m/%Y à %H:%M:%S')}")
        
        while True:
            try:
                print("\n" + "=" * 50)
                print("                MENU PRINCIPAL")
                print("=" * 50)
                print("1. Démarrer l'opération d'effacement de disque")
                print("2. Options d'impression des journaux")
                print("3. Quitter")
                print("-" * 50)
                
                choice = input("Entrez votre choix (1-3) : ").strip()
                
                if choice == "1":
                    # Opération d'effacement de disque
                    run_disk_erasure_operation(args)
                
                elif choice == "2":
                    # Options d'impression des journaux
                    print_log_menu()
                
                elif choice == "3":
                    # Quitter
                    exit_msg = "Session CLI terminée par l'utilisateur"
                    print(f"\n{exit_msg}")
                    log_info(exit_msg)
                    break
                
                else:
                    print("Choix invalide. Veuillez entrer 1, 2, ou 3.")
                    
            except KeyboardInterrupt:
                interrupt_msg = "Opération du menu principal interrompue par l'utilisateur (Ctrl+C)"
                print(f"\n{interrupt_msg}")
                log_error(interrupt_msg)
                continue
            except (EOFError, IOError) as e:
                input_error_msg = f"Erreur d'entrée dans le menu principal : {str(e)}"
                print(f"\n{input_error_msg}")
                log_error(input_error_msg)
                continue
                
    except KeyboardInterrupt:
        final_interrupt_msg = "Programme terminé par l'utilisateur (Ctrl+C)"
        print(f"\n{final_interrupt_msg}")
        log_error(final_interrupt_msg)
        sys.exit(130)
    except (IOError, OSError) as e:
        error_msg = f"Erreur système : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    except (ValueError, TypeError) as e:
        error_msg = f"Erreur de validation des données : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    except (SubprocessError, CalledProcessError) as e:
        error_msg = f"Erreur d'exécution de commande : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    except (ImportError, ModuleNotFoundError) as e:
        error_msg = f"Erreur d'importation de module : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    except (AttributeError, NameError) as e:
        error_msg = f"Erreur de configuration/référence : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    except (PermissionError, FileNotFoundError) as e:
        error_msg = f"Erreur d'accès/fichier : {str(e)}"
        print(error_msg)
        log_error(error_msg)
        sys.exit(1)
    finally:
        # S'assurer que la session se termine correctement
        session_end()