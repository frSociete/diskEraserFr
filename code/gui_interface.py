import os
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from utils import get_disk_list, get_physical_drives_for_logical_volumes, get_base_disk
from concurrent.futures import ThreadPoolExecutor, as_completed
from log_handler import log_info, log_error, blank
from disk_operations import get_active_disk, process_disk
import threading
from typing import Optional, Dict, List, Callable, Any

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
        
        # Check for root privileges
        if os.geteuid() != 0:
            messagebox.showerror("Erreur", "Ce programme doit être exécuté en tant que root !")
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
        disk_frame = ttk.LabelFrame(main_frame, text="Sélectionner les disques à effacer")
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
        refresh_button = ttk.Button(disk_frame, text="Actualiser les disques", command=self.refresh_disks)
        refresh_button.pack(pady=10)
        
        # Right frame - Options
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Erasure method options
        method_label = ttk.Label(options_frame, text="Méthode d'effacement :")
        method_label.pack(anchor="w", pady=(10, 5))
        
        methods = [("Écrasement standard", "overwrite"), ("Effacement cryptographique", "crypto")]
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
        self.crypto_fill_frame = ttk.LabelFrame(options_frame, text="Méthode de remplissage (Crypto)")
        # Initially hidden, will be shown when crypto method is selected
        
        fill_methods = [("Données aléatoires", "random"), ("Données zéro", "zero")]
        for text, value in fill_methods:
            rb = ttk.Radiobutton(self.crypto_fill_frame, text=text, value=value, variable=self.crypto_fill_var)
            rb.pack(anchor="w", padx=20, pady=2)
        
        # Filesystem options
        fs_label = ttk.Label(options_frame, text="Choisir système de fichiers :")
        fs_label.pack(anchor="w", pady=(10, 5))
        
        filesystems = [("ext4", "ext4"), ("NTFS", "ntfs"), ("FAT32", "vfat")]
        for text, value in filesystems:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.filesystem_var)
            rb.pack(anchor="w", padx=20)
        
        # Exit fullscreen button
        exit_button = ttk.Button(options_frame, text="Quitter plein écran", command=self.toggle_fullscreen)
        exit_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Start button
        start_button = ttk.Button(options_frame, text="Démarrer l'effacement", command=self.start_erasure)
        start_button.pack(pady=20, padx=10, fill=tk.X)

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
            except tk.TclError:
                # Some widgets (like labels) may not support 'state'
                pass

        # Enable or disable passes entry
        for child in self.passes_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                if method == "crypto":
                    child.configure(state="disabled")
                else:
                    child.configure(state="normal")

    def exit_application(self) -> None:
        """Log and close the application when Exit is clicked"""
        exit_message = "Application fermée par l'utilisateur via le bouton Quitter"
        log_info(exit_message)
        self.update_gui_log(exit_message)
        blank()  # Add separator in log file
        self.root.destroy()
    
    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode"""
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)

    def refresh_disks(self) -> None:
        # Clear existing disk checkboxes
        for widget in self.scrollable_disk_frame.winfo_children():
            widget.destroy()
        
        self.disk_vars = {}
        
        # Get list of disks using the common function
        self.disks = get_disk_list()
        
        if not self.disks:
            no_disk_label = ttk.Label(self.scrollable_disk_frame, text="Aucun disque trouvé")
            no_disk_label.pack(pady=10)
            self.disclaimer_var.set("")
            self.ssd_disclaimer_var.set("")
            self.update_gui_log("Aucun disque trouvé.")
            return
        
        # Get active device(s) - now always returns a list or None with LVM resolution built-in
        active_device = get_active_disk()
        active_physical_drives = set()
        
        if active_device:
            # get_active_disk() now always returns a list of physical disk names with LVM already resolved
            for dev in active_device:
                active_physical_drives.add(get_base_disk(dev))
            log_info(f"Active physical devices: {active_physical_drives}")
            
        # Set disclaimer if we found an active disk
        if active_physical_drives:
            self.disclaimer_var.set(f"ATTENTION : Le disque marqué en rouge contient le système de fichiers actif. L'effacement de ce disque est bloqué pour éviter une défaillance du système et une perte de données !")

        else:
            self.disclaimer_var.set("")
        
        # Check if any SSDs are present and set the SSD disclaimer
        has_ssd = False
        for disk in self.disks:
            device_name = disk['device'].replace('/dev/', '')
            if is_ssd(device_name):
                has_ssd = True
                break
                
        if has_ssd:
            self.ssd_disclaimer_var.set("ATTENTION : Périphériques SSD détectés. L'effacement en plusieurs passes peut endommager les SSD et NE PAS réussir à supprimer les données en toute sécurité en raison de la répartition d'usure des SSD. Pour les SSD, utilisez le mode d'effacement cryptographique.")

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
            
            var = tk.BooleanVar(value=False)
            self.disk_vars[disk['device']] = var
            
            
            # Get disk information
            device_name = disk['device'].replace('/dev/', '')
            disk_identifier = get_disk_serial(device_name)
            is_device_ssd = is_ssd(device_name)
            ssd_indicator = " (Solid_state)" if is_device_ssd else " (Mechanical)"
            
            # Determine if this is the active disk
            base_device_name = get_base_disk(device_name)
            is_active = base_device_name in active_physical_drives
            active_indicator = " (DISQUE SYSTÈME ACTIF)" if is_active else ""
            
            # Set text color
            text_color = "red" if is_active else "blue" if is_device_ssd else "black"

            # Create the checkbox and set state based on if it's an active disk
            cb = ttk.Checkbutton(checkbox_row, variable=var, state="disabled" if is_active else "normal")
            # Make sure we can't select the active disk
            if is_active:
                var.set(False)
                cb.configure(state="disabled")
            cb.pack(side=tk.LEFT)
            
            # Create disk identifier label with wrapping
            disk_id_label = ttk.Label(
                checkbox_row, 
                text=f"{disk_identifier}{ssd_indicator}{active_indicator}",
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
                text=f"Size: {disk['size']} - Model: {disk['model']}",
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

        
        # Get erasure method
        erase_method = self.erase_method_var.get()
        
        # Check if any SSDs are selected and show a warning for overwrite method
        ssd_selected = False
        if erase_method == "overwrite":
            for disk in selected_disks:
                disk_name = disk.replace('/dev/', '')
                if is_ssd(disk_name):
                    ssd_selected = True
                    break
                    
            if ssd_selected:
                if not messagebox.askyesno("WARNING - SSD DEVICE SELECTED", 
                                          "WARNING: You have selected one or more SSD devices!\n\n"
                                          "Using multiple-pass erasure on SSDs can:\n"
                                          "• Damage the SSD by causing excessive wear\n"
                                          "• Fail to securely erase data due to SSD wear leveling\n"
                                          "• Not overwrite all sectors due to over-provisioning\n\n"
                                          "For SSDs, use cryptographic erasure \n\n"
                                          "Do you still want to continue?",
                                          icon="warning"):
                    return
        
        # Get disk identifiers
        disk_identifiers = []
        for disk in selected_disks:
            disk_name = disk.replace('/dev/', '')
            disk_identifiers.append(get_disk_serial(disk_name))
        
        # Confirm erasure
        disk_list = "\n".join(disk_identifiers)
        
        # Add method-specific information to confirmation dialog
        method_info = "en utilisant l'effacement cryptographique" if erase_method == "crypto" else f"avec un écrasement en {self.passes_var.get()} passes"
        
        if not messagebox.askyesno("Confirmer l'effacement", 
                                  f"ATTENTION : Vous êtes sur le point d'effacer de manière sécurisée les disques suivants {method_info} :\n\n{disk_list}\n\n"
                                  "Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES !\n\n"
                                  "Êtes-vous absolument sûr de vouloir continuer ?"):
            return
        
        # Double-check confirmation with a different dialog
        if not messagebox.askyesno("AVERTISSEMENT FINAL", 
                                  "CECI EST VOTRE DERNIER AVERTISSEMENT !\n\n"
                                  "Tous les disques sélectionnés seront complètement effacés.\n\n"
                                  "Voulez-vous poursuivre ?"):
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
        
        # Start processing in a separate thread
        self.status_var.set("Démarrage du processus d'effacement...")
        threading.Thread(target=self.progress_state, args=(selected_disks, fs_choice, passes, erase_method), daemon=True).start()
    
    def progress_state(self, disks: List[str], fs_choice: str, passes: int, erase_method: str) -> None:
        method_str = "effacement cryptographique" if erase_method == "crypto" else f"écrasement standard en {passes} passes"
        self.update_gui_log(f"Démarrage de l'effacement sécurisé de {len(disks)} disque(s) en utilisant {method_str}")
        log_info(f"Démarrage de l'effacement sécurisé de {len(disks)} disque(s) en utilisant {method_str}")
        self.update_gui_log(f"Système de fichiers sélectionné : {fs_choice}")
        log_info(f"Système de fichiers sélectionné : {fs_choice}")
        
        total_disks = len(disks)
        completed_disks = 0
        
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
            
        self.status_var.set("Processus d'effacement terminé")
        messagebox.showinfo("Terminé", "L'opération d'effacement des disques est terminée !")
    
    def process_disk_wrapper(self, disk: str, fs_choice: str, passes: int, erase_method: str) -> None:
        """
        Wrapper for process_disk from disk_operations.py that updates GUI status
        """
        # Extract disk name (remove /dev/)
        disk_name = disk.replace('/dev/', '')
        
        # Get the disk ID for status updates
        try:
            disk_id = get_disk_serial(disk_name)
            self.status_var.set(f"Effacement de {disk_id}...")
        except (CalledProcessError, SubprocessError) as e:
            self.update_gui_log(f"Erreur lors de l'obtention du numéro de série du disque : {str(e)}")
            self.status_var.set(f"Effacement de {disk_name}...")
        except FileNotFoundError as e:
            self.update_gui_log(f"Commande requise non trouvée : {str(e)}")
            self.status_var.set(f"Effacement de {disk_name}...")
        except PermissionError as e:
            self.update_gui_log(f"Erreur de permission : {str(e)}")
            self.status_var.set(f"Effacement de {disk_name}...")
        except OSError as e:
            self.update_gui_log(f"Erreur OS : {str(e)}")
            self.status_var.set(f"Effacement de {disk_name}...")
        
        # Define GUI log callback for process_disk
        def gui_log_callback(message: str) -> None:
            self.update_gui_log(message)
        
        try:
            # Call process_disk from disk_operations
            use_crypto = (erase_method == "crypto")
            process_disk(disk_name, fs_choice, passes, use_crypto, log_func=gui_log_callback)
            
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
            self.update_gui_log(f"Erreur OS : {str(e)}")
            raise
        except KeyboardInterrupt:
            self.update_gui_log("Opération interrompue par l'utilisateur")
            raise
    
    def update_progress(self, value: float) -> None:
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def update_gui_log(self, message: str) -> None:
        """Update only the GUI log window with a message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # Update log in the GUI
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

def run_gui_mode() -> None:
    """Run the GUI version"""
    root = tk.Tk()
    app = DiskEraserGUI(root)
    root.mainloop()