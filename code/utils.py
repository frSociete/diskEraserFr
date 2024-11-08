import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
        print(e.stderr.decode('utf-8'))
        return None

def list_disks():
    print("Disques disponibles :")
    run_command("lsblk -d -o NAME,SIZE,TYPE | grep disk")
