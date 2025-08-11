import os
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from utils import get_disk_list, get_base_disk
from concurrent.futures import ThreadPoolExecutor, as_completed
from log_handler import log_info, log_error, log_erase_operation, session_start, session_end, generate_session_pdf, generate_log_file_pdf
from disk_operations import get_active_disk, process_disk
import threading
from typing import Dict, List

class DiskEraserGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Effaceur de Disque Sécurisé")
        self.root.geometry("600x500")
        # Set fullscreen mode to True
        self.root.attributes("-fullscreen", True)
        self.disk_vars: Dict[str, tk.BooleanVar] = {}
        self.filesystem_var = tk.StringVar(value="ext4")
        self.passes_var = tk.StringVar(value="5")
        self.erase_method_var = tk.StringVar(value="overwrite")  # Default to overwrite method
        self.crypto_fill_var = tk.StringVar(value="random")  # Default fill method for crypto erasure
        self.disks: List[Dict[str, str]] = []
        self.disk_progress: Dict[str, float] = {}
        self.active_disk = get_active_disk()
        
        # Track if active drive message was logged
        self.active_drive_logged = False
        
        # Start session logging - this will now automatically capture all log messages
        session_start()
        
        # Check for root privileges
        if os.geteuid() != 0:
            messagebox.showerror("Erreur", "Ce programme doit être exécuté en tant qu'administrateur (root) !")
            root.destroy()
            sys.exit(1)
        
        self.create_widgets()
        self.refresh_disks()
    
    def create_widgets(self) -> None:
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Effaceur de Disque Sécurisé", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Left frame - Disk selection
        disk_frame = ttk.LabelFrame(main_frame, text="Sélectionner les Disques à Effacer")
        disk_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable frame for disks
        self.disk_canvas = tk.Canvas(disk_frame)
        scrollbar = ttk.Scrollbar(disk_frame, orient="vertical", command=self.disk_canvas.yview)
        self.scrollable_disk_frame = ttk.Frame(self.disk_canvas)
        
        self.scrollable_disk_frame.bind(
            "<Configure>",
            lambda e: self.disk_canvas.configure(scrollregion=self.disk_canvas.bbox("all"))
        )
        
        self.disk_canvas.create_window((0, 0), window=self.scrollable_disk_frame, anchor="nw")
        self.disk_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.disk_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add disclaimer label at the bottom of disk frame
        self.disclaimer_var = tk.StringVar(value="")
        self.disclaimer_label = ttk.Label(disk_frame, textvariable=self.disclaimer_var, foreground="red", wraplength=250)
        self.disclaimer_label.pack(side=tk.BOTTOM, pady=5)
        
        # Add SSD warning disclaimer at the bottom of disk frame
        self.ssd_disclaimer_var = tk.StringVar(value="")
        self.ssd_disclaimer_label = ttk.Label(disk_frame, textvariable=self.ssd_disclaimer_var, foreground="blue", wraplength=250)
        self.ssd_disclaimer_label.pack(side=tk.BOTTOM, pady=5)
        
        # Refresh button
        refresh_button = ttk.Button(disk_frame, text="Actualiser les Disques", command=self.refresh_disks)
        refresh_button.pack(pady=10)
        
        # Right frame - Options
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Erasure method options
        method_label = ttk.Label(options_frame, text="Méthode d'Effacement :")
        method_label.pack(anchor="w", pady=(10, 5))
        
        methods = [("Écrasement Standard", "overwrite"), ("Effacement Cryptographique", "crypto")]
        for text, value in methods:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.erase_method_var, 
                                command=self.update_method_options)
            rb.pack(anchor="w", padx=20)
        
        # Passes (for overwrite method)
        self.passes_frame = ttk.Frame(options_frame)
        self.passes_frame.pack(fill=tk.X, pady=10, padx=5)
        
        passes_label = ttk.Label(self.passes_frame, text="Nombre de passes :")
        passes_label.pack(side=tk.LEFT, padx=5)
        
        passes_entry = ttk.Entry(self.passes_frame, textvariable=self.passes_var, width=5)
        passes_entry.pack(side=tk.LEFT, padx=5)
        
        # Crypto fill method options (for crypto method)
        self.crypto_fill_frame = ttk.LabelFrame(options_frame, text="Méthode de Remplissage (Crypto)")
        # Initially hidden, will be shown when crypto method is selected
        
        fill_methods = [("Données Aléatoires", "random"), ("Données Zéro", "zero")]
        for text, value in fill_methods:
            rb = ttk.Radiobutton(self.crypto_fill_frame, text=text, value=value, variable=self.crypto_fill_var)
            rb.pack(anchor="w", padx=20, pady=2)
        
        # Filesystem options
        fs_label = ttk.Label(options_frame, text="Choisir le Système de Fichiers :")
        fs_label.pack(anchor="w", pady=(10, 5))
        
        filesystems = [("ext4", "ext4"), ("NTFS", "ntfs"), ("FAT32", "vfat")]
        for text, value in filesystems:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.filesystem_var)
            rb.pack(anchor="w", padx=20)
        
        # Exit fullscreen button
        exit_button = ttk.Button(options_frame, text="Quitter le Plein Écran", command=self.toggle_fullscreen)
        exit_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Start button
        start_button = ttk.Button(options_frame, text="Démarrer l'Effacement", command=self.start_erasure)
        start_button.pack(pady=20, padx=10, fill=tk.X)

        # Print log buttons frame
        log_buttons_frame = ttk.Frame(options_frame)
        log_buttons_frame.pack(pady=5, padx=10, fill=tk.X)
        
        # Print session log button
        print_session_button = ttk.Button(log_buttons_frame, text="Imprimer Journal de Session", 
                                         command=self.print_session_log)
        print_session_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        # Print complete log button
        print_log_button = ttk.Button(log_buttons_frame, text="Imprimer Journal Complet", 
                                     command=self.print_complete_log)
        print_log_button.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.X, expand=True)

        # Exit program button
        close_button = ttk.Button(options_frame, text="Quitter", command=self.exit_application)
        close_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progression")
        progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_var = tk.StringVar(value="Prêt")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Journal")
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Protocol for window close event
        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        
        # Initial method options update
        self.update_method_options()
    
    def print_session_log(self) -> None:
        """Generate and save session log as PDF"""
        try:
            self.status_var.set("Génération du PDF du journal de session...")
            pdf_path = generate_session_pdf()
            
            success_msg = f"PDF du journal de session généré avec succès !\nEnregistré dans : {pdf_path}"
            messagebox.showinfo("PDF Généré", success_msg)
            self.update_gui_log(f"PDF du journal de session enregistré dans : {pdf_path}")
            self.status_var.set("PDF du journal de session généré")
            
        except (ImportError, ModuleNotFoundError) as e:
            error_msg = f"Bibliothèque PDF non disponible : {str(e)}"
            messagebox.showerror("Erreur de Bibliothèque", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except (IOError, OSError) as e:
            error_msg = f"Erreur de système de fichiers lors de la génération du PDF du journal de session : {str(e)}"
            messagebox.showerror("Erreur de Fichier", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except PermissionError as e:
            error_msg = f"Permission refusée lors de la génération du PDF du journal de session : {str(e)}"
            messagebox.showerror("Erreur de Permission", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except MemoryError:
            error_msg = "Mémoire insuffisante pour générer le PDF du journal de session"
            messagebox.showerror("Erreur de Mémoire", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except (ValueError, TypeError) as e:
            error_msg = f"Erreur de format de données lors de la génération du PDF du journal de session : {str(e)}"
            messagebox.showerror("Erreur de Données", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
    
    def print_complete_log(self) -> None:
        """Generate and save complete log file as PDF"""
        try:
            self.status_var.set("Génération du PDF du journal complet...")
            pdf_path = generate_log_file_pdf()
            
            success_msg = f"PDF du journal complet généré avec succès !\nEnregistré dans : {pdf_path}"
            messagebox.showinfo("PDF Généré", success_msg)
            self.update_gui_log(f"PDF du journal complet enregistré dans : {pdf_path}")
            self.status_var.set("PDF du journal complet généré")
            
        except (ImportError, ModuleNotFoundError) as e:
            error_msg = f"Bibliothèque PDF non disponible : {str(e)}"
            messagebox.showerror("Erreur de Bibliothèque", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except (IOError, OSError) as e:
            error_msg = f"Erreur de système de fichiers lors de la génération du PDF du journal complet : {str(e)}"
            messagebox.showerror("Erreur de Fichier", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except PermissionError as e:
            error_msg = f"Permission refusée lors de la génération du PDF du journal complet : {str(e)}"
            messagebox.showerror("Erreur de Permission", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except FileNotFoundError as e:
            error_msg = f"Fichier journal non trouvé lors de la génération du PDF du journal complet : {str(e)}"
            messagebox.showerror("Fichier Non Trouvé", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except MemoryError:
            error_msg = "Mémoire insuffisante pour générer le PDF du journal complet"
            messagebox.showerror("Erreur de Mémoire", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except (ValueError, TypeError) as e:
            error_msg = f"Erreur de format de données lors de la génération du PDF du journal complet : {str(e)}"
            messagebox.showerror("Erreur de Données", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
    
    def update_method_options(self) -> None:
        """Update UI based on the selected erasure method"""
        method = self.erase_method_var.get()

        # Always show the crypto fill options frame
        self.crypto_fill_frame.pack(fill=tk.X, pady=10, padx=5, after=self.passes_frame)

        # Enable or disable widgets inside crypto_fill_frame
        for child in self.crypto_fill_frame.winfo_children():
            try:
                if method == "crypto":
                    child.configure(state="normal")
                else:
                    child.configure(state="disabled")
            except tk.TclError as e:
                # Some widgets (like labels) may not support 'state'
                # Log the specific widget type that doesn't support state configuration
                widget_type = type(child).__name__
                self.update_gui_log(f"Le widget {widget_type} ne prend pas en charge la configuration d'état : {str(e)}")

        # Enable or disable passes entry
        for child in self.passes_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                try:
                    if method == "crypto":
                        child.configure(state="disabled")
                    else:
                        child.configure(state="normal")
                except tk.TclError as e:
                    error_msg = f"Erreur de configuration de l'état du widget d'entrée : {str(e)}"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)

    def exit_application(self) -> None:
        """Log and close the application when Exit is clicked"""
        exit_message = "Application fermée par l'utilisateur via le bouton Quitter"
        log_info(exit_message)
        self.update_gui_log(exit_message)
        session_end()
        self.root.destroy()
    
    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode"""
        try:
            is_fullscreen = self.root.attributes("-fullscreen")
            self.root.attributes("-fullscreen", not is_fullscreen)
        except tk.TclError as e:
            error_msg = f"Erreur lors du basculement en mode plein écran : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)

    def refresh_disks(self) -> None:
        # Clear existing disk checkboxes
        for widget in self.scrollable_disk_frame.winfo_children():
            widget.destroy()
        
        self.disk_vars = {}
        
        # Get list of disks using the common function
        try:
            self.disks = get_disk_list()
        except (CalledProcessError, SubprocessError) as e:
            error_msg = f"Erreur lors de l'obtention de la liste des disques : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.disks = []
        except FileNotFoundError as e:
            error_msg = f"Commande utilitaire de disque requise non trouvée : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.disks = []
        except (IOError, OSError) as e:
            error_msg = f"Erreur système d'accès aux informations du disque : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.disks = []
        
        if not self.disks:
            no_disk_label = ttk.Label(self.scrollable_disk_frame, text="Aucun disque trouvé")
            no_disk_label.pack(pady=10)
            self.disclaimer_var.set("")
            self.ssd_disclaimer_var.set("")
            self.update_gui_log("Aucun disque trouvé.")
            log_info("Aucun disque trouvé lors de l'actualisation des disques")
            return
        
        # Get active device(s) - now always returns a list or None with LVM resolution built-in
        try:
            active_device = get_active_disk()
        except (CalledProcessError, SubprocessError) as e:
            error_msg = f"Erreur de détection du disque actif : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            active_device = None
        except FileNotFoundError as e:
            error_msg = f"Commande requise non trouvée pour la détection du disque actif : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            active_device = None
        except (IOError, OSError) as e:
            error_msg = f"Erreur système de détection du disque actif : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
            active_device = None
        
        active_physical_drives = set()
        
        if active_device:
            # get_active_disk() now always returns a list of physical disk names with LVM already resolved
            for dev in active_device:
                try:
                    active_physical_drives.add(get_base_disk(dev))
                except (ValueError, TypeError) as e:
                    error_msg = f"Erreur lors du traitement du nom de périphérique {dev} : {str(e)}"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)
            
            # Only log once per session
            if not self.active_drive_logged and active_physical_drives:
                log_info(f"Périphériques physiques actifs : {active_physical_drives}")
                self.active_drive_logged = True
            
            # Set disclaimer if we found an active disk
            if active_physical_drives:
                self.disclaimer_var.set(
                    "AVERTISSEMENT : Le disque marqué en rouge contient le système de fichiers actif. "
                    "Effacer ce disque causera une panne du système et une perte de données !"
                )
            else:
                self.disclaimer_var.set("")
        else:
            self.disclaimer_var.set("")
        
        # Check if any SSDs are present and set the SSD disclaimer
        has_ssd = False
        for disk in self.disks:
            device_name = disk['device'].replace('/dev/', '')
            try:
                if is_ssd(device_name):
                    has_ssd = True
                    break
            except (CalledProcessError, SubprocessError) as e:
                error_msg = f"Erreur lors de la vérification si {device_name} est un SSD : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            except FileNotFoundError as e:
                error_msg = f"Commande requise non trouvée pour la détection SSD : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
                
        if has_ssd:
            self.ssd_disclaimer_var.set(
                "AVERTISSEMENT : Périphériques SSD détectés. L'effacement multi-passes peut endommager les SSD "
                "et NE PAS réaliser une suppression sécurisée des données à cause du nivellement de l'usure des SSD. "
                "Pour les SSD, utilisez plutôt le mode d'effacement cryptographique."
            )
        else:
            self.ssd_disclaimer_var.set("")
        
        # Create checkboxes for each disk
        for disk in self.disks:
            # Create a container frame for each disk entry
            disk_entry_frame = ttk.Frame(self.scrollable_disk_frame)
            disk_entry_frame.pack(fill=tk.X, pady=5, padx=2)
            
            # Top row with checkbox
            checkbox_row = ttk.Frame(disk_entry_frame)
            checkbox_row.pack(fill=tk.X)
            
            var = tk.BooleanVar()
            self.disk_vars[disk['device']] = var
            
            cb = ttk.Checkbutton(checkbox_row, variable=var)
            cb.pack(side=tk.LEFT)
            
            # Get disk information
            device_name = disk['device'].replace('/dev/', '')
            
            # Get disk identifier with error handling
            try:
                disk_identifier = get_disk_serial(device_name)
            except (CalledProcessError, SubprocessError) as e:
                disk_identifier = f"{device_name} (Numéro de série indisponible)"
                error_msg = f"Erreur lors de l'obtention du numéro de série pour {device_name} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            except FileNotFoundError as e:
                disk_identifier = f"{device_name} (Commande de numéro de série non trouvée)"
                error_msg = f"Commande requise non trouvée pour obtenir le numéro de série de {device_name} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            
            # Check if SSD with error handling
            try:
                is_device_ssd = is_ssd(device_name)
                ssd_indicator = " (État solide)" if is_device_ssd else " (Mécanique)"
            except (CalledProcessError, SubprocessError) as e:
                ssd_indicator = " (Type inconnu)"
                error_msg = f"Erreur lors de la détermination du type de lecteur pour {device_name} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            except FileNotFoundError as e:
                ssd_indicator = " (Détection de type indisponible)"
                error_msg = f"Commande requise non trouvée pour la détection du type de lecteur de {device_name} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            
            # Determine if this is the active disk
            try:
                base_device_name = get_base_disk(device_name)
                is_active = base_device_name in active_physical_drives
            except (ValueError, TypeError) as e:
                is_active = False
                error_msg = f"Erreur lors de la détermination du périphérique de base pour {device_name} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            
            active_indicator = " (DISQUE SYSTÈME ACTIF)" if is_active else ""
            
            # Get disk label from the updated utils
            disk_label = disk.get('label', 'Inconnu')
            label_indicator = f" [Étiquette : {disk_label}]" if disk_label and disk_label != "No Label" else " [Aucune Étiquette]"
            
            # Set text color
            text_color = "red" if is_active else "blue" if 'is_device_ssd' in locals() and is_device_ssd else "black"
            
            # Create disk identifier label with wrapping
            disk_id_label = ttk.Label(
                checkbox_row, 
                text=f"{disk_identifier}{ssd_indicator}{active_indicator}{label_indicator}",
                foreground=text_color,
                wraplength=300
            )
            disk_id_label.pack(side=tk.LEFT, padx=5, fill=tk.X)
            
            # Create a second row for disk details that will wrap if needed
            details_row = ttk.Frame(disk_entry_frame)
            details_row.pack(fill=tk.X, padx=25)
            
            # Create disk details label
            disk_details_label = ttk.Label(
                details_row,
                text=f"Taille : {disk['size']} - Modèle : {disk['model']}",
                wraplength=300,
                foreground=text_color
            )
            disk_details_label.pack(side=tk.LEFT, fill=tk.X)
            
            # Add a separator between disk entries for better visual separation
            ttk.Separator(self.scrollable_disk_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)   
    
    def start_erasure(self) -> None:
        # Get selected disks
        selected_disks = [disk for disk, var in self.disk_vars.items() if var.get()]
        
        if not selected_disks:
            messagebox.showwarning("Avertissement", "Aucun disque sélectionné !")
            return
        
        # Check if active disk is selected
        active_disk_selected = False
        for disk in selected_disks:
            disk_name = disk.replace('/dev/', '')
            if self.active_disk and any(active_disk in disk_name for active_disk in self.active_disk):
                active_disk_selected = True
                break

        # Additional warning for active disk
        if active_disk_selected:
            if not messagebox.askyesno("DANGER - DISQUE SYSTÈME SÉLECTIONNÉ", 
                                      "AVERTISSEMENT : Vous avez sélectionné le DISQUE SYSTÈME ACTIF !\n\n"
                                      "Effacer ce disque va PLANTER votre système et causer une PERTE DE DONNÉES PERMANENTE !\n\n"
                                      "Êtes-vous absolument sûr de vouloir continuer ?",
                                      icon="warning"):
                return
        
        # Get erasure method
        erase_method = self.erase_method_var.get()
        
        # Check if any SSDs are selected and show a warning for overwrite method
        ssd_selected = False
        if erase_method == "overwrite":
            for disk in selected_disks:
                disk_name = disk.replace('/dev/', '')
                try:
                    if is_ssd(disk_name):
                        ssd_selected = True
                        break
                except (CalledProcessError, SubprocessError) as e:
                    error_msg = f"Erreur lors de la vérification du statut SSD pour {disk_name} : {str(e)}"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)
                except FileNotFoundError as e:
                    error_msg = f"Commande de détection SSD non trouvée pour {disk_name} : {str(e)}"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)
                    
            if ssd_selected:
                if not messagebox.askyesno("AVERTISSEMENT - PÉRIPHÉRIQUE SSD SÉLECTIONNÉ", 
                                          "AVERTISSEMENT : Vous avez sélectionné un ou plusieurs périphériques SSD !\n\n"
                                          "Utiliser un effacement multi-passes sur les SSD peut :\n"
                                          "• Endommager le SSD en causant une usure excessive\n"
                                          "• Échouer à effacer les données de manière sécurisée à cause du nivellement de l'usure des SSD\n"
                                          "• Ne pas réécrire tous les secteurs à cause du sur-approvisionnement\n\n"
                                          "Pour les SSD, utilisez l'effacement cryptographique \n\n"
                                          "Voulez-vous toujours continuer ?",
                                          icon="warning"):
                    return
        
        # Get disk identifiers and log each erasure operation
        disk_identifiers = []
        for disk in selected_disks:
            disk_name = disk.replace('/dev/', '')
            try:
                disk_identifier = get_disk_serial(disk_name)
            except (CalledProcessError, SubprocessError) as e:
                disk_identifier = f"{disk_name} (Numéro de série indisponible)"
                error_msg = f"Erreur lors de l'obtention du numéro de série pour la journalisation : {disk_name}: {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            except FileNotFoundError as e:
                disk_identifier = f"{disk_name} (Commande de numéro de série non trouvée)"
                error_msg = f"Commande de détection du numéro de série non trouvée pour la journalisation : {disk_name}: {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            
            disk_identifiers.append(disk_identifier)
            
            # Log detailed erasure operation for each disk
            fs_choice = self.filesystem_var.get()
            if erase_method == "crypto":
                fill_method = self.crypto_fill_var.get()
                method_description = f"effacement cryptographique avec remplissage {fill_method}"
            else:
                method_description = f"écrasement standard {self.passes_var.get()}-passes"
            
            try:
                log_erase_operation(disk_identifier, fs_choice, method_description)
            except (IOError, OSError) as e:
                error_msg = f"Erreur lors de la journalisation de l'opération d'effacement pour {disk_identifier} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
            except (ValueError, TypeError) as e:
                error_msg = f"Données invalides pour la journalisation de l'opération d'effacement pour {disk_identifier} : {str(e)}"
                self.update_gui_log(error_msg)
                log_error(error_msg)
        
        # Confirm erasure
        disk_list = "\n".join(disk_identifiers)
        
        # Add method-specific information to confirmation dialog
        if erase_method == "crypto":
            fill_method = self.crypto_fill_var.get()
            method_info = f"en utilisant l'effacement cryptographique avec remplissage {fill_method}"
        else:
            method_info = f"avec écrasement {self.passes_var.get()} passes"
        
        if not messagebox.askyesno("Confirmer l'Effacement", 
                                  f"AVERTISSEMENT : Vous êtes sur le point d'effacer de manière sécurisée les disques suivants {method_info} :\n\n{disk_list}\n\n"
                                  "Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES !\n\n"
                                  "Êtes-vous absolument sûr de vouloir continuer ?"):
            return
        
        # Double-check confirmation with a different dialog
        if not messagebox.askyesno("AVERTISSEMENT FINAL", 
                                  "CECI EST VOTRE AVERTISSEMENT FINAL !\n\n"
                                  "Tous les disques sélectionnés seront complètement effacés.\n\n"
                                  "Voulez-vous procéder ?"):
            return
        
        # Get options
        fs_choice = self.filesystem_var.get()
        
        # For overwrite method, validate passes
        passes = 1  # Default value
        if erase_method == "overwrite":
            try:
                passes = int(self.passes_var.get())
                if passes < 1:
                    messagebox.showerror("Erreur", "Le nombre de passes doit être au moins 1")
                    return
            except ValueError:
                messagebox.showerror("Erreur", "Le nombre de passes doit être un entier valide")
                return
            except OverflowError:
                messagebox.showerror("Erreur", "Le nombre de passes est trop grand")
                return
        
        # Start processing in a separate thread
        self.status_var.set("Démarrage du processus d'effacement...")
        try:
            threading.Thread(target=self.progress_state, args=(selected_disks, fs_choice, passes, erase_method), daemon=True).start()
        except RuntimeError as e:
            error_msg = f"Erreur lors du démarrage du thread d'effacement : {str(e)}"
            messagebox.showerror("Erreur de Thread", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
        except OSError as e:
            error_msg = f"Erreur système lors du démarrage du processus d'effacement : {str(e)}"
            messagebox.showerror("Erreur Système", error_msg)
            self.update_gui_log(error_msg)
            log_error(error_msg)
            self.status_var.set("Prêt")
    
    def progress_state(self, disks: List[str], fs_choice: str, passes: int, erase_method: str) -> None:
        if erase_method == "crypto":
            fill_method = self.crypto_fill_var.get()
            method_str = f"effacement cryptographique avec remplissage {fill_method}"
        else:
            method_str = f"écrasement standard {passes}-passes"
        
        start_msg = f"Démarrage de l'effacement sécurisé de {len(disks)} disque(s) en utilisant {method_str}"
        fs_msg = f"Système de fichiers sélectionné : {fs_choice}"
        
        self.update_gui_log(start_msg)
        log_info(start_msg)
        
        self.update_gui_log(fs_msg)
        log_info(fs_msg)
        
        total_disks = len(disks)
        completed_disks = 0
        
        try:
            with ThreadPoolExecutor() as executor:
                # Create a dictionary to track progress for each disk
                self.disk_progress = {disk: 0 for disk in disks}
                
                # Submit all disk tasks
                futures = {executor.submit(self.process_disk_wrapper, disk, fs_choice, passes, erase_method): disk for disk in disks}
                
                # Process results as they complete
                for future in as_completed(futures):
                    disk = futures[future]
                    try:
                        future.result()
                        completed_disks += 1
                        self.update_progress((completed_disks / total_disks) * 100)
                        self.status_var.set(f"Terminé {completed_disks}/{total_disks} disques")
                    except (CalledProcessError, FileNotFoundError, PermissionError, OSError) as e:
                        error_msg = f"Erreur lors du traitement du disque {disk} : {str(e)}"
                        self.update_gui_log(error_msg)
                        log_error(error_msg)
                    except KeyboardInterrupt:
                        error_msg = "Opération interrompue par l'utilisateur"
                        self.update_gui_log(error_msg)
                        log_error(error_msg)
                    except MemoryError:
                        error_msg = f"Mémoire insuffisante lors du traitement du disque {disk}"
                        self.update_gui_log(error_msg)
                        log_error(error_msg)
                    except RuntimeError as e:
                        error_msg = f"Erreur d'exécution lors du traitement du disque {disk} : {str(e)}"
                        self.update_gui_log(error_msg)
                        log_error(error_msg)
                    except (ValueError, TypeError) as e:
                        error_msg = f"Erreur de données invalides lors du traitement du disque {disk} : {str(e)}"
                        self.update_gui_log(error_msg)
                        log_error(error_msg)
        
        except RuntimeError as e:
            error_msg = f"Erreur avec l'exécuteur de pool de threads : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
        except OSError as e:
            error_msg = f"Erreur système pendant le traitement des disques : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
        except MemoryError:
            error_msg = "Mémoire insuffisante pour les opérations de pool de threads"
            self.update_gui_log(error_msg)
            log_error(error_msg)
        
        complete_msg = "Processus d'effacement terminé"
        self.status_var.set(complete_msg)
        log_info(complete_msg)
        try:
            messagebox.showinfo("Terminé", "L'opération d'effacement de disque est terminée !")
        except tk.TclError as e:
            error_msg = f"Erreur lors de l'affichage du dialogue de fin : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
    
    def process_disk_wrapper(self, disk: str, fs_choice: str, passes: int, erase_method: str) -> None:
        """
        Wrapper for process_disk from disk_operations.py that updates GUI status
        """
        # Extract disk name (remove /dev/)
        disk_name = disk.replace('/dev/', '')
        
        # Get the disk ID for status updates
        try:
            disk_id = get_disk_serial(disk_name)
            self.status_var.set(f"Effacement {disk_id}...")
        except (CalledProcessError, SubprocessError) as e:
            self.update_gui_log(f"Erreur lors de l'obtention du numéro de série du disque : {str(e)}")
            self.status_var.set(f"Effacement {disk_name}...")
        except FileNotFoundError as e:
            self.update_gui_log(f"Commande requise non trouvée : {str(e)}")
            self.status_var.set(f"Effacement {disk_name}...")
        except PermissionError as e:
            self.update_gui_log(f"Erreur de permission : {str(e)}")
            self.status_var.set(f"Effacement {disk_name}...")
        except OSError as e:
            self.update_gui_log(f"Erreur du système d'exploitation : {str(e)}")
            self.status_var.set(f"Effacement {disk_name}...")
        
        # Define GUI log callback for process_disk (only for display, not session logs)
        def gui_log_callback(message: str) -> None:
            self.update_gui_log(message)
        
        try:
            # Call process_disk from disk_operations
            use_crypto = (erase_method == "crypto")
            crypto_fill = self.crypto_fill_var.get() if use_crypto else "random"
            process_disk(disk_name, fs_choice, passes, use_crypto, crypto_fill, log_func=gui_log_callback)
            
        except CalledProcessError as e:
            self.update_gui_log(f"Erreur de processus : {str(e)}")
            raise
        except FileNotFoundError as e:
            self.update_gui_log(f"Commande requise non trouvée : {str(e)}")
            raise
        except PermissionError as e:
            self.update_gui_log(f"Erreur de permission : {str(e)}")
            raise
        except OSError as e:
            self.update_gui_log(f"Erreur du système d'exploitation : {str(e)}")
            raise
        except KeyboardInterrupt:
            self.update_gui_log("Opération interrompue par l'utilisateur")
            raise
        except MemoryError:
            self.update_gui_log(f"Mémoire insuffisante lors du traitement {disk_name}")
            raise
        except (ValueError, TypeError) as e:
            self.update_gui_log(f"Erreur de paramètre invalide pour {disk_name} : {str(e)}")
            raise
        except RuntimeError as e:
            self.update_gui_log(f"Erreur d'exécution lors du traitement {disk_name} : {str(e)}")
            raise
    
    def update_progress(self, value: float) -> None:
        try:
            self.progress_var.set(value)
            self.root.update_idletasks()
        except tk.TclError as e:
            error_msg = f"Erreur lors de la mise à jour de la barre de progression : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
        except (ValueError, TypeError) as e:
            error_msg = f"Valeur de progression invalide : {str(e)}"
            self.update_gui_log(error_msg)
            log_error(error_msg)
    
    def update_gui_log(self, message: str) -> None:
        """Update the GUI log window with a message (for display only)."""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"

            # Update log in the GUI
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        except tk.TclError as e:
            # If GUI log fails, at least try to log the error
            error_msg = f"Erreur lors de la mise à jour du journal GUI : {str(e)}"
            try:
                log_error(error_msg)
            except (IOError, OSError):
                # If even logging fails, we can't do much more
                pass
        except (ValueError, TypeError) as e:
            error_msg = f"Données invalides pour la mise à jour du journal GUI : {str(e)}"
            try:
                log_error(error_msg)
            except (IOError, OSError):
                pass
        except OSError as e:
            error_msg = f"Erreur système lors de la mise à jour du journal GUI : {str(e)}"
            try:
                log_error(error_msg)
            except (IOError, OSError):
                pass

def run_gui_mode() -> None:
    """Run the GUI version"""
    try:
        root = tk.Tk()
        app = DiskEraserGUI(root)
        root.mainloop()
    except tk.TclError as e:
        print(f"Erreur d'initialisation de l'interface graphique : {str(e)}")
        log_error(f"Erreur d'initialisation de l'interface graphique : {str(e)}")
        sys.exit(1)
    except (ImportError, ModuleNotFoundError) as e:
        print(f"Bibliothèque d'interface graphique requise non disponible : {str(e)}")
        log_error(f"Bibliothèque d'interface graphique requise non disponible : {str(e)}")
        sys.exit(1)
    except MemoryError:
        print("Mémoire insuffisante pour démarrer l'interface graphique")
        log_error("Mémoire insuffisante pour démarrer l'interface graphique")
        sys.exit(1)
    except OSError as e:
        print(f"Erreur système lors du démarrage de l'interface graphique : {str(e)}")
        log_error(f"Erreur système lors du démarrage de l'interface graphique : {str(e)}")
        sys.exit(1)