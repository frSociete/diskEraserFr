import os
from disk_erase import erase_disk
from disk_partition import partition_disk
from disk_format import format_disk
from utils import list_disks
from argparse import ArgumentParser

def main(fs_choice):
    #List available disks
    list_disks()
    
    #Disk selection
    disk = input("Entrez le disque à effacer (ex: sda, sdb) : ").strip()
    
    #Erase disk content
    erase_disk(disk)
    
    #Partition disk after data removal
    partition_disk(disk)
    
    #Filesystem to install on disk
    if not fs_choice:
        print("Choisissez un système de fichiers pour formater le disque :")
        print("1. NTFS")
        print("2. EXT4")
        choice = input("Entrez votre choix (1 ou 2) : ").strip()
        
        if choice == "1":
            fs_choice = "ntfs"
        elif choice == "2":
            fs_choice = "ext4"
        else:
            print("Choix invalide. Arrêt du programme.")
            return
    
    #Format partition using selected filesystem
    format_disk(disk, fs_choice)
    print("Opération terminée avec succès.")

def sudo_check(args):
    if os.geteuid() != 0:
        print("Ce script doit être exécuté en tant que root !")
    else:
        main(args.f)

def _parse_args():
    parser = ArgumentParser(description="Script d'effacement et de formatage sécurisé de disques.")
    parser.add_argument(
        '-f', 
        help="Choisissez le système de fichiers à appliquer (ext4 ou ntfs).",
        choices=['ext4', 'ntfs'], 
        required=False
    )
    return parser.parse_args()

def app():
    args = _parse_args()
    sudo_check(args)

# Vérifie que le script est exécuté directement
if __name__ == "__main__":
    app()
