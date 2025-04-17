import os
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from subprocess import CalledProcessError, SubprocessError
from disk_erase import get_disk_serial, is_ssd
from utils import get_disk_list
from concurrent.futures import ThreadPoolExecutor, as_completed
from log_handler import log_info, log_error, blank
from disk_operations import get_active_disk, process_disk
import threading

class DiskEraserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Disk Eraser")
        self.root.geometry("600x500")
        # Set fullscreen mode to True
        self.root.attributes("-fullscreen", True)
        self.disk_vars = {}
        self.filesystem_var = tk.StringVar(value="ext4")
        self.passes_var = tk.StringVar(value="5")
        self.erase_method_var = tk.StringVar(value="overwrite")  # Default to overwrite method
        self.crypto_fill_var = tk.StringVar(value="random")  # Default fill method for crypto erasure
        self.disks = []
        self.disk_progress = {}
        self.active_disk = get_active_disk()
        
        # Check for root privileges
        if os.geteuid() != 0:
            messagebox.showerror("Error", "This program must be run as root!")
            root.destroy()
            sys.exit(1)
        
        self.create_widgets()
        self.refresh_disks()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Secure Disk Eraser", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Left frame - Disk selection
        disk_frame = ttk.LabelFrame(main_frame, text="Select Disks to Erase")
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
        self.ssd_disclaimer_label = ttk.Label(disk_frame, textvariable=self.ssd_disclaimer_var, foreground="red", wraplength=250)
        self.ssd_disclaimer_label.pack(side=tk.BOTTOM, pady=5)
        
        # Refresh button
        refresh_button = ttk.Button(disk_frame, text="Refresh Disks", command=self.refresh_disks)
        refresh_button.pack(pady=10)
        
        # Right frame - Options
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        # Erasure method options
        method_label = ttk.Label(options_frame, text="Erasure Method:")
        method_label.pack(anchor="w", pady=(10, 5))
        
        methods = [("Standard Overwrite", "overwrite"), ("Cryptographic Erasure", "crypto")]
        for text, value in methods:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.erase_method_var, 
                                command=self.update_method_options)
            rb.pack(anchor="w", padx=20)
        
        # Passes (for overwrite method)
        self.passes_frame = ttk.Frame(options_frame)
        self.passes_frame.pack(fill=tk.X, pady=10, padx=5)
        
        passes_label = ttk.Label(self.passes_frame, text="Number of passes:")
        passes_label.pack(side=tk.LEFT, padx=5)
        
        passes_entry = ttk.Entry(self.passes_frame, textvariable=self.passes_var, width=5)
        passes_entry.pack(side=tk.LEFT, padx=5)
        
        # Crypto fill method options (for crypto method)
        self.crypto_fill_frame = ttk.LabelFrame(options_frame, text="Fill Method (Crypto)")
        # Initially hidden, will be shown when crypto method is selected
        
        fill_methods = [("Random Data", "random"), ("Zero Data", "zero")]
        for text, value in fill_methods:
            rb = ttk.Radiobutton(self.crypto_fill_frame, text=text, value=value, variable=self.crypto_fill_var)
            rb.pack(anchor="w", padx=20, pady=2)
        
        # Filesystem options
        fs_label = ttk.Label(options_frame, text="Choose Filesystem:")
        fs_label.pack(anchor="w", pady=(10, 5))
        
        filesystems = [("ext4", "ext4"), ("NTFS", "ntfs"), ("FAT32", "vfat")]
        for text, value in filesystems:
            rb = ttk.Radiobutton(options_frame, text=text, value=value, variable=self.filesystem_var)
            rb.pack(anchor="w", padx=20)
        
        # Exit fullscreen button
        exit_button = ttk.Button(options_frame, text="Exit Fullscreen", command=self.toggle_fullscreen)
        exit_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Start button
        start_button = ttk.Button(options_frame, text="Start Erasure", command=self.start_erasure)
        start_button.pack(pady=20, padx=10, fill=tk.X)

        # Exit program button
        close_button = ttk.Button(options_frame, text="Exit", command=self.exit_application)
        close_button.pack(pady=5, padx=10, fill=tk.X)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress")
        progress_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Log")
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
    
    def update_method_options(self):
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

    def exit_application(self):
        """Log and close the application when Exit is clicked"""
        exit_message = "Application closed by user via Exit button"
        log_info(exit_message)
        self.update_gui_log(exit_message)
        blank()  # Add separator in log file
        self.root.destroy()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        is_fullscreen = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_fullscreen)
    
        
    def refresh_disks(self):
        # Clear existing disk checkboxes
        for widget in self.scrollable_disk_frame.winfo_children():
            widget.destroy()
        
        self.disk_vars = {}
        
        # Get list of disks using the common function
        self.disks = get_disk_list()
        
        if not self.disks:
            no_disk_label = ttk.Label(self.scrollable_disk_frame, text="No disks found")
            no_disk_label.pack(pady=10)
            self.disclaimer_var.set("")
            self.ssd_disclaimer_var.set("")
            self.update_gui_log("No disks found.")
            return
            
        # Set disclaimer if we found an active disk
        if self.active_disk:
            self.disclaimer_var.set(f"WARNING: Disk marked in red contains the active filesystem. Erasing this disk will cause system failure and data loss!")
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
            self.ssd_disclaimer_var.set("WARNING: SSD devices detected. Multiple-pass erasure may damage SSDs and NOT achieve secure data deletion due to SSD wear leveling. For SSDs, use manufacturer-provided secure erase tools instead.")
        else:
            self.ssd_disclaimer_var.set("")
        
        # Create checkboxes for each disk
        for disk in self.disks:
            frame = ttk.Frame(self.scrollable_disk_frame)
            frame.pack(fill=tk.X, pady=2)
            
            var = tk.BooleanVar()
            self.disk_vars[disk['device']] = var
            
            cb = ttk.Checkbutton(frame, variable=var)
            cb.pack(side=tk.LEFT)
            
            # Disk identifier label with size info
            device_name = disk['device'].replace('/dev/', '')
            disk_identifier = get_disk_serial(device_name)
            is_device_ssd = is_ssd(device_name)
            ssd_indicator = " (SSD)" if is_device_ssd else " (HDD)"
            
            # Set the text color to red if this is the active disk
            is_active = self.active_disk and any(disk in device_name for disk in self.active_disk)

            text_color = "red" if is_active else "red" if is_device_ssd else "black"
            active_indicator = " (ACTIVE SYSTEM DISK)" if is_active else ""
            
            disk_label = ttk.Label(
                frame, 
                text=f"{disk_identifier}{ssd_indicator}{active_indicator} ({disk['size']}) - {disk['model']}",
                foreground=text_color
            )
            disk_label.pack(side=tk.LEFT, padx=5)
    
    def start_erasure(self):
        # Get selected disks
        selected_disks = [disk for disk, var in self.disk_vars.items() if var.get()]
        
        if not selected_disks:
            messagebox.showwarning("Warning", "No disks selected!")
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
            if not messagebox.askyesno("DANGER - SYSTEM DISK SELECTED", 
                                      "WARNING: You have selected the ACTIVE SYSTEM DISK!\n\n"
                                      "Erasing this disk will CRASH your system and cause PERMANENT DATA LOSS!\n\n"
                                      "Are you absolutely sure you want to continue?",
                                      icon="warning"):
                return
        
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
                                          "For SSDs, manufacturer-provided secure erase tools are recommended.\n\n"
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
        method_info = "using cryptographic erasure" if erase_method == "crypto" else f"with {self.passes_var.get()} pass overwrite"
        
        if not messagebox.askyesno("Confirm Erasure", 
                                  f"WARNING: You are about to securely erase the following disks {method_info}:\n\n{disk_list}\n\n"
                                  "This operation CANNOT be undone and ALL DATA WILL BE LOST!\n\n"
                                  "Are you absolutely sure you want to continue?"):
            return
        
        # Double-check confirmation with a different dialog
        if not messagebox.askyesno("FINAL WARNING", 
                                  "THIS IS YOUR FINAL WARNING!\n\n"
                                  "All selected disks will be completely erased.\n\n"
                                  "Do you want to proceed?"):
            return
        
        # Get options
        fs_choice = self.filesystem_var.get()
        
        # For overwrite method, validate passes
        passes = 1  # Default value
        if erase_method == "overwrite":
            try:
                passes = int(self.passes_var.get())
                if passes < 1:
                    messagebox.showerror("Error", "Number of passes must be at least 1")
                    return
            except ValueError:
                messagebox.showerror("Error", "Number of passes must be a valid integer")
                return
        
        # Start processing in a separate thread
        self.status_var.set("Starting erasure process...")
        threading.Thread(target=self.progress_state, args=(selected_disks, fs_choice, passes, erase_method), daemon=True).start()
    
    def progress_state(self, disks, fs_choice, passes, erase_method):
        method_str = "cryptographic erasure" if erase_method == "crypto" else f"standard {passes}-pass overwrite"
        self.update_gui_log(f"Starting secure erasure of {len(disks)} disk(s) using {method_str}")
        log_info(f"Starting secure erasure of {len(disks)} disk(s) using {method_str}")
        self.update_gui_log(f"Selected filesystem: {fs_choice}")
        log_info(f"Selected filesystem: {fs_choice}")
        
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
                    self.status_var.set(f"Completed {completed_disks}/{total_disks} disks")
                except (CalledProcessError, FileNotFoundError, PermissionError, OSError) as e:
                    error_msg = f"Error processing disk {disk}: {str(e)}"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)
                except KeyboardInterrupt:
                    error_msg = "Operation interrupted by user"
                    self.update_gui_log(error_msg)
                    log_error(error_msg)
            
        self.status_var.set("Erasure process completed")
        messagebox.showinfo("Complete", "Disk erasure operation has completed!")
    
    def process_disk_wrapper(self, disk, fs_choice, passes, erase_method):
        """
        Wrapper for process_disk from disk_operations.py that updates GUI status
        """
        # Extract disk name (remove /dev/)
        disk_name = disk.replace('/dev/', '')
        
        # Get the disk ID for status updates
        try:
            disk_id = get_disk_serial(disk_name)
            self.status_var.set(f"Erasing {disk_id}...")
        except Exception:
            self.status_var.set(f"Erasing {disk_name}...")
        
        # Define GUI log callback for process_disk
        def gui_log_callback(message):
            self.update_gui_log(message)
        
        try:
            # Call process_disk from disk_operations
            use_crypto = (erase_method == "crypto")
            process_disk(disk_name, fs_choice, passes, use_crypto, log_func=gui_log_callback)
            
        except Exception as e:
            # Forward any exceptions to the caller
            raise e
    
    def update_progress(self, value):
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def update_gui_log(self, message):
        """Update only the GUI log window with a message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # Update log in the GUI
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

def run_gui_mode():
    """Run the GUI version"""
    root = tk.Tk()
    app = DiskEraserGUI(root)
    root.mainloop()