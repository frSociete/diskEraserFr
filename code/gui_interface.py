import os
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from utils import get_disk_list, get_base_disk
from concurrent.futures import ThreadPoolExecutor, as_completed
from log_handler import (
    log_info, log_error, log_erase_operation,
    session_start, session_end, generate_session_pdf, generate_log_file_pdf
)
from disk_operations import get_active_disk, process_disk
import threading
from typing import Dict, List

class DiskEraserGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Effaceur de Disque Sécurisé")
        self.root.geometry("600x500")
        self.root.attributes("-fullscreen", True)
        self.disk_vars: Dict[str, tk.BooleanVar] = {}
        self.filesystem_var = tk.StringVar(value="ext4")
        self.passes_var = tk.StringVar(value="5")
        self.erase_method_var = tk.StringVar(value="overwrite")
        self.crypto_fill_var = tk.StringVar(value="random")
        self.disks: List[Dict[str, str]] = []
        self.disk_progress: Dict[str, float] = {}
        self.active_disk = get_active_disk()
        self.active_drive_logged = False
        session_start()
        if os.geteuid() != 0:
            messagebox.showerror("Erreur", "Ce programme doit être exécuté en tant qu'administrateur (root) !")
            root.destroy()
            sys.exit(1)
        self.create_widgets()
        self.refresh_disks()

    def create_widgets(self) -> None:
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Effaceur de Disque Sécurisé", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        disk_frame = ttk.LabelFrame(main_frame, text="Sélectionner les Disques à Effacer")
        disk_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

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

        self.disclaimer_var = tk.StringVar(value="")
        self.disclaimer_label = ttk.Label(disk_frame, textvariable=self.disclaimer_var, foreground="red", wraplength=250)
        self.disclaimer_label.pack(side=tk.BOTTOM, pady=5)

        self.ssd_disclaimer_var = tk.StringVar(value="")
        self.ssd_disclaimer_label = ttk.Label(disk_frame, textvariable=self.ssd_disclaimer_var, foreground="blue", wraplength=250)
        self.ssd_disclaimer_label.pack(side=tk.BOTTOM, pady=5)

        refresh_button = ttk.Button(disk_frame, text="Actualiser les Disques", command=self.refresh_disks)
        refresh_button.pack(pady=10)

        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

        method_label = ttk.Label(options_frame, text="Méthode d'Effacement :")
        method_label.pack(anchor="w", pady=(10, 5))
        methods = [
            ("Écrasement Standard", "overwrite"),
            ("Effacement Cryptographique", "crypto")
        ]
        for text, value in methods:
            rb = ttk.Radiobutton(
                options_frame, text=text, value=value,
                variable=self.erase_method_var, command=self.update_method_options
            )
            rb.pack(anchor="w", padx=20)

        self.passes_frame = ttk.Frame(options_frame)
        self.passes_frame.pack(fill=tk.X, pady=10, padx=5)
        passes_label = ttk.Label(self.passes_frame, text="Nombre de passes :")
        passes_label.pack(side=tk.LEFT, padx=5)
        passes_entry = ttk.Entry(self.passes_frame, textvariable=self.passes_var, width=5)
        passes_entry.pack(side=tk.LEFT, padx=5)

        self.crypto_fill_frame = ttk.LabelFrame(options_frame, text="Méthode de Remplissage (Crypto)")
        fill_methods = [("Données Aléatoires", "random"), ("Données Zéro", "zero")]
        for text, value in fill_methods:
            rb = ttk.Radiobutton(self.crypto_fill_frame, text=text, value=value, variable=self.crypto_fill_var)
            rb.pack(anchor="w", padx=20, pady=2)

        fs_label = ttk.Label(options_frame, text="Choisir le Système de Fichiers :")
        fs_label.pack(anchor="w", pady=(10, 5))
        filesystems = [("ext4", "ext4"), ("NTFS", "ntfs"), ("FAT32", "vfat")]
        for text, value in filesystems:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.filesystem_var)
            rb.pack(anchor="w", padx=20)

        exit_button = ttk.Button(options_frame, text="Quitter le Plein Écran", command=self.toggle_fullscreen)
        exit_button.pack(pady=5, padx=10, fill=tk.X)

        start_button = ttk.Button(options_frame, text="Démarrer l'Effacement", command=self.start_erasure)
        start_button.pack(pady=20, padx=10, fill=tk.X)

        log_buttons_frame = ttk.Frame(options_frame)
        log_buttons_frame.pack(pady=5, padx=10, fill=tk.X)
        print_session_button = ttk.Button(log_buttons_frame, text="Imprimer Journal de Session", command=self.print_session_log)
        print_session_button.pack(side=tk.TOP, pady=5, padx=10, fill=tk.X, expand=True)
        print_log_button = ttk.Button(log_buttons_frame, text="Imprimer Journal Complet", command=self.print_complete_log)
        print_log_button.pack(side=tk.BOTTOM, pady=5, padx=10, fill=tk.X, expand=True)
        close_button = ttk.Button(options_frame, text="Quitter", command=self.exit_application)
        close_button.pack(pady=5, padx=10, fill=tk.X)

        progress_frame = ttk.LabelFrame(main_frame, text="Progression")
        progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        self.status_var = tk.StringVar(value="Prêt")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(pady=5)

        log_frame = ttk.LabelFrame(main_frame, text="Journal")
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)
        self.update_method_options()

    def refresh_disks(self) -> None:
        for widget in self.scrollable_disk_frame.winfo_children():
            widget.destroy()
        self.disk_vars = {}
        try:
            self.disks = get_disk_list()
        except Exception as e:
            self.update_gui_log(str(e))
            log_error(str(e))
            self.disks = []
        if not self.disks:
            no_disk_label = ttk.Label(self.scrollable_disk_frame, text="Aucun disque trouvé")
            no_disk_label.pack(pady=10)
            self.disclaimer_var.set("")
            self.ssd_disclaimer_var.set("")
            self.update_gui_log("Aucun disque trouvé.")
            log_info("Aucun disque trouvé lors de l'actualisation des disques")
            return
        try:
            active_device = get_active_disk()
        except Exception as e:
            self.update_gui_log(str(e))
            log_error(str(e))
            active_device = None
        active_physical_drives = set()
        if active_device:
            for dev in active_device:
                try:
                    active_physical_drives.add(get_base_disk(dev))
                except Exception as e:
                    self.update_gui_log(str(e))
                    log_error(str(e))
            if not self.active_drive_logged and active_physical_drives:
                log_info(f"Périphériques physiques actifs : {active_physical_drives}")
                self.active_drive_logged = True
            if active_physical_drives:
                self.disclaimer_var.set(
                    "AVERTISSEMENT : Le disque marqué en rouge contient le système de fichiers actif. "
                    "Effacer ce disque causera une panne du système et une perte de données !"
                )
            else:
                self.disclaimer_var.set("")
        else:
            self.disclaimer_var.set("")
        has_ssd = False
        for disk in self.disks:
            device_name = disk['device'].replace('/dev/', '')
            try:
                if is_ssd(device_name):
                    has_ssd = True
                    break
            except Exception as e:
                self.update_gui_log(str(e))
                log_error(str(e))
        if has_ssd:
            self.ssd_disclaimer_var.set(
                "AVERTISSEMENT : Périphériques SSD détectés. L'effacement multi-passes peut endommager les SSD "
                "et NE PAS réaliser une suppression sécurisée des données à cause du nivellement de l'usure des SSD. "
                "Pour les SSD, utilisez plutôt le mode d'effacement cryptographique."
            )
        else:
            self.ssd_disclaimer_var.set("")
        for disk in self.disks:
            disk_entry_frame = ttk.Frame(self.scrollable_disk_frame)
            disk_entry_frame.pack(fill=tk.X, pady=5, padx=2)
            checkbox_row = ttk.Frame(disk_entry_frame)
            checkbox_row.pack(fill=tk.X)
            var = tk.BooleanVar()
            self.disk_vars[disk['device']] = var
            cb = ttk.Checkbutton(checkbox_row, variable=var)
            cb.pack(side=tk.LEFT)
            device_name = disk['device'].replace('/dev/', '')
            try:
                disk_identifier = get_disk_serial(device_name)
            except Exception:
                disk_identifier = f"{device_name} (Numéro de série indisponible)"
            try:
                is_device_ssd = is_ssd(device_name)
                ssd_indicator = " (État solide)" if is_device_ssd else " (Mécanique)"
            except Exception:
                ssd_indicator = " (Type inconnu)"
            try:
                base_device_name = get_base_disk(device_name)
                is_active = base_device_name in active_physical_drives
            except Exception:
                is_active = False
            active_indicator = " (DISQUE SYSTÈME ACTIF)" if is_active else ""
            disk_label = disk.get('label', 'Inconnu')
            label_indicator = f" [Étiquette : {disk_label}]" if disk_label and disk_label != "No Label" else " [Aucune Étiquette]"
            text_color = "red" if is_active else "blue" if 'is_device_ssd' in locals() and is_device_ssd else "black"
            disk_id_label = ttk.Label(
                checkbox_row, 
                text=f"{disk_identifier}{ssd_indicator}{active_indicator}{label_indicator}",
                foreground=text_color,
                wraplength=300
            )
            disk_id_label.pack(side=tk.LEFT, padx=5, fill=tk.X)
            details_row = ttk.Frame(disk_entry_frame)
            details_row.pack(fill=tk.X, padx=25)
            disk_details_label = ttk.Label(
                details_row,
                text=f"Taille : {disk['size']} - Modèle : {disk['model']}",
                wraplength=300,
                foreground=text_color
            )
            disk_details_label.pack(side=tk.LEFT, fill=tk.X)
            ttk.Separator(self.scrollable_disk_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=2)

    def start_erasure(self) -> None:
        selected_disks = [disk for disk, var in self.disk_vars.items() if var.get()]
        if not selected_disks:
            messagebox.showwarning("Avertissement", "Aucun disque sélectionné !")
            return
        active_disk_selected = False
        for disk in selected_disks:
            disk_name = disk.replace('/dev/', '')
            if self.active_disk and any(active_disk in disk_name for active_disk in self.active_disk):
                active_disk_selected = True
                break
        if active_disk_selected:
            if not messagebox.askyesno(
                "DANGER - DISQUE SYSTÈME SÉLECTIONNÉ", 
                "AVERTISSEMENT : Vous avez sélectionné le DISQUE SYSTÈME ACTIF !\n\n"
                "Effacer ce disque va PLANTER votre système et causer une PERTE DE DONNÉES PERMANENTE !\n\n"
                "Êtes-vous absolument sûr de vouloir continuer ?",
                icon="warning"
            ):
                return
        erase_method = self.erase_method_var.get()
        ssd_selected = False
        if erase_method == "overwrite":
            for disk in selected_disks:
                disk_name = disk.replace('/dev/', '')
                try:
                    if is_ssd(disk_name):
                        ssd_selected = True
                        break
                except Exception:
                    continue
            if ssd_selected:
                if not messagebox.askyesno(
                    "AVERTISSEMENT - PÉRIPHÉRIQUE SSD SÉLECTIONNÉ", 
                    "AVERTISSEMENT : Vous avez sélectionné un ou plusieurs périphériques SSD !\n\n"
                    "Utiliser un effacement multi-passes sur les SSD peut :\n"
                    "• Endommager le SSD en causant une usure excessive\n"
                    "• Échouer à effacer les données de manière sécurisée à cause du nivellement de l'usure des SSD\n"
                    "• Ne pas réécrire tous les secteurs à cause du sur-approvisionnement\n\n"
                    "Pour les SSD, utilisez l'effacement cryptographique \n\n"
                    "Voulez-vous toujours continuer ?", icon="warning"
                ):
                    return
        disk_identifiers = []
        for disk in selected_disks:
            disk_name = disk.replace('/dev/', '')
            try:
                disk_identifier = get_disk_serial(disk_name)
            except Exception:
                disk_identifier = f"{disk_name} (Numéro de série indisponible)"
            disk_identifiers.append(disk_identifier)
            fs_choice = self.filesystem_var.get()
            if erase_method == "crypto":
                fill_method = self.crypto_fill_var.get()
                method_description = f"effacement cryptographique avec remplissage {fill_method}"
            else:
                method_description = f"écrasement standard {self.passes_var.get()}-passes"
            try:
                log_erase_operation(disk_identifier, fs_choice, method_description)
            except Exception:
                pass
        disk_list = "\n".join(disk_identifiers)
        if erase_method == "crypto":
            fill_method = self.crypto_fill_var.get()
            method_info = f"en utilisant l'effacement cryptographique avec remplissage {fill_method}"
        else:
            method_info = f"avec écrasement {self.passes_var.get()} passes"
        if not messagebox.askyesno(
            "Confirmer l'Effacement", 
            f"AVERTISSEMENT : Vous êtes sur le point d'effacer de manière sécurisée les disques suivants {method_info} :\n\n{disk_list}\n\n"
            "Cette opération NE PEUT PAS être annulée et TOUTES LES DONNÉES SERONT PERDUES !\n\n"
            "Êtes-vous absolument sûr de vouloir continuer ?"
        ):
            return
        if not messagebox.askyesno(
            "AVERTISSEMENT FINAL",
            "CECI EST VOTRE AVERTISSEMENT FINAL !\n\n"
            "Tous les disques sélectionnés seront complètement effacés.\n\n"
            "Voulez-vous procéder ?"
        ):
            return
        fs_choice = self.filesystem_var.get()
        passes = 1
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
        self.status_var.set("Démarrage du processus d'effacement...")
        try:
            threading.Thread(target=self.progress_state, args=(selected_disks, fs_choice, passes, erase_method), daemon=True).start()
        except (RuntimeError, OSError) as e:
            messagebox.showerror("Erreur", str(e))
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
                self.disk_progress = {disk: 0 for disk in disks}
                futures = {executor.submit(self.process_disk_wrapper, disk, fs_choice, passes, erase_method): disk for disk in disks}
                for future in as_completed(futures):
                    disk = futures[future]
                    try:
                        future.result()
                        completed_disks += 1
                        self.update_progress((completed_disks / total_disks) * 100)
                        self.status_var.set(f"Terminé {completed_disks}/{total_disks} disques")
                    except Exception as e:
                        self.update_gui_log(str(e))
                        log_error(str(e))
        except Exception as e:
            self.update_gui_log(str(e))
            log_error(str(e))
        complete_msg = "Processus d'effacement terminé"
        self.status_var.set(complete_msg)
        log_info(complete_msg)
        try:
            messagebox.showinfo("Terminé", "L'opération d'effacement de disque est terminée !")
        except Exception as e:
            self.update_gui_log(str(e))
            log_error(str(e))

    def process_disk_wrapper(self, disk: str, fs_choice: str, passes: int, erase_method: str) -> None:
        disk_name = disk.replace('/dev/', '')
        try:
            disk_id = get_disk_serial(disk_name)
            self.status_var.set(f"Effacement {disk_id}...")
        except Exception:
            self.status_var.set(f"Effacement {disk_name}...")
        def gui_log_callback(message: str) -> None:
            self.update_gui_log(message)
        try:
            use_crypto = (erase_method == "crypto")
            crypto_fill = self.crypto_fill_var.get() if use_crypto else "random"
            process_disk(disk_name, fs_choice, passes, use_crypto, crypto_fill, log_func=gui_log_callback)
        except Exception as e:
            self.update_gui_log(str(e))

    def update_progress(self, value: float) -> None:
        try:
            self.progress_var.set(value)
            self.root.update_idletasks()
        except Exception as e:
            self.update_gui_log(str(e))
            log_error(str(e))

    def update_gui_log(self, message: str) -> None:
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
        except Exception as e:
            pass  # Log errors only if critical

    def print_session_log(self) -> None:
        try:
            self.status_var.set("Génération du PDF du journal de session...")
            pdf_path = generate_session_pdf()
            messagebox.showinfo("PDF Généré", f"PDF du journal de session généré avec succès !\nEnregistré dans : {pdf_path}")
            self.update_gui_log(f"PDF du journal de session enregistré dans : {pdf_path}")
            self.status_var.set("PDF du journal de session généré")
        except Exception as e:
            self.update_gui_log(str(e))
            messagebox.showerror("Erreur", str(e))
            log_error(str(e))
            self.status_var.set("Prêt")

    def print_complete_log(self) -> None:
        try:
            self.status_var.set("Génération du PDF du journal complet...")
            pdf_path = generate_log_file_pdf()
            messagebox.showinfo("PDF Généré", f"PDF du journal complet généré avec succès !\nEnregistré dans : {pdf_path}")
            self.update_gui_log(f"PDF du journal complet enregistré dans : {pdf_path}")
            self.status_var.set("PDF du journal complet généré")
        except Exception as e:
            self.update_gui_log(str(e))
            messagebox.showerror("Erreur", str(e))
            log_error(str(e))
            self.status_var.set("Prêt")

    def update_method_options(self) -> None:
        method = self.erase_method_var.get()
        self.crypto_fill_frame.pack(fill=tk.X, pady=10, padx=5, after=self.passes_frame)
        for child in self.crypto_fill_frame.winfo_children():
            try:
                child.configure(state="normal" if method == "crypto" else "disabled")
            except tk.TclError:
                pass
        for child in self.passes_frame.winfo_children():
            if isinstance(child, ttk.Entry):
                try:
                    child.configure(state="disabled" if method == "crypto" else "normal")
                except tk.TclError:
                    pass

    def exit_application(self) -> None:
        exit_message = "Application fermée par l'utilisateur via le bouton Quitter"
        log_info(exit_message)
        self.update_gui_log(exit_message)
        session_end()
        self.root.destroy()

    def toggle_fullscreen(self) -> None:
        try:
            is_fullscreen = self.root.attributes("-fullscreen")
            self.root.attributes("-fullscreen", not is_fullscreen)
        except tk.TclError:
            pass

def run_gui_mode() -> None:
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
