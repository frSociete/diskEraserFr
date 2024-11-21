import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {command}")
        print(e.stderr.decode('utf-8'))
        return None

def list_disks():
    print("Liste des disques disponibles :")
    try:
        output = run_command("lsblk -d -o NAME,SIZE,TYPE | grep disk")
        if output:
            print(output)
        else:
            print("Aucun disque détecté. Assurez-vous que le programme est exécuté avec les permissions appropriées.")
    except Exception as e:
        print(f"Une erreur s'est produite lors de la récupération des disques : {e}")
