from utils import run_command

def erase_disk(disk):
    confirm = input(f"Êtes-vous sûr de vouloir effacer {disk} ? Cette opération est irréversible. (y/n) : ")
    if confirm.lower() == 'y':
        print(f"Effacement de {disk} en utilisant shred...")
        run_command(f"shred -v -n 3 /dev/{disk}")
        print(f"Disque {disk} effacé avec succès.")
    else:
        print("Opération annulée.")
