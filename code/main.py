import os
from disk_erase import erase_disk
from disk_partition import partition_disk
from disk_format import format_disk
from utils import list_disks

def main():
    #List available disks
    list_disks()
    
    #Disk selection
    disk = input("Entrez le disque à effacer (ex: sda, sdb) : ")
    
    #Erase disk content
    erase_disk(disk)
    
    #Partition disk after data removal
    partition_disk(disk)
    
    #Filesystem to install on disk
    print("Choisissez un système de fichiers pour formater le disque :")
    print("1. NTFS")
    print("2. EXT4")
    fs_choice = int(input("Entrez votre choix (1 ou 2) : "))
    
    if fs_choice not in [1, 2]:
        print("Choix invalide. Arrêt du programme.")
        return
    
    #Format partition using selected filesystem
    format_disk(disk, fs_choice)
    print("Opération terminée avec succès.")

#Ensure root exécution
if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Ce script doit être exécuté en tant que root !")
    else:
        main()
