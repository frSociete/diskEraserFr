# Disk Eraser - Outil de Nettoyage et Formatage Sécurisé de Disques 💽

<div style="display: flex; align-items: center;">
  <img src="./img/background" alt="Logo" width="120" style="margin-right: 20px;">
  <p>
    <b>Disk Eraser</b> est un outil pour effacer de manière sécurisée les données des périphériques de stockage tout en offrant la possibilité de formater avec le système de fichiers de votre choix (EXT4, NTFS ou VFAT). Il prend en charge l'effacement parallèle des disques avec des passages d'écrasement configurables pour une désinfection approfondie des données.
  </p>
</div>

## Méthodes d'Effacement Sécurisé

### Pour les Disques Durs (HDD) : Passes Multiples d'Écrasement
- Recommandé pour les disques durs mécaniques traditionnels
- Utilise plusieurs passages de données aléatoires suivis d'un passage à zéro
- Empêche la récupération des données par analyse physique des résidus magnétiques

### Pour les SSD : Effacement Cryptographique
- Recommandé pour les disques SSD et le stockage flash
- Les options incluent :
  - **Remplissage de Données Aléatoires** : Écrase avec des données aléatoires cryptographiquement sécurisées
  - **Remplissage à Zéro** : Effacement rapide en écrivant des zéros à tous les emplacements adressables
- Fonctionne avec ATA Secure Erase pour les appareils compatibles


> ⚠️ **AVERTISSEMENT DE COMPATIBILITÉ SSD**
> 
> Bien que cet outil puisse détecter et fonctionner avec les SSD, veuillez noter :
> 
> - **Répartition d'Usure des SSD** : Rend les méthodes traditionnelles d'écrasement moins efficaces
> - **Sur-provisionnement** : L'espace réservé caché peut conserver des données
> - **Durée de Vie de l'Appareil** : Les passages multiples peuvent réduire la longévité du SSD
> 
> Pour les SSD, les méthodes d'effacement cryptographique sont recommandées plutôt que les passages multiples d'écrasement.


⚠️ **AVERTISSEMENT DE COMPATIBILITÉ DES CLÉS USB**

Le noyau Linux marque souvent incorrectement les clés USB comme des périphériques rotatifs, ce qui peut considérablement impacter les performances lors des opérations d'effacement. Il s'agit d'un problème connu du noyau affectant les périphériques de stockage USB.

**Pour corriger ce problème lorsque vous N'utilisez PAS l'ISO personnalisée**, créez la règle udev suivante :
Cette règle est disponible sur stackexchange : [Solution de stackexchange](https://unix.stackexchange.com/questions/439109/set-usb-flash-drive-as-non-rotational-drive)

1. Créez le fichier `/etc/udev/rules.d/usb-flash.rules` avec les privilèges root :
```bash
sudo nano /etc/udev/rules.d/usb-flash.rules
```

2. Ajoutez le contenu suivant :
```bash
# Tente de détecter les clés USB et les définir comme non-rotatives
# c.f. https://mpdesouza.com/blog/kernel-adventures-are-usb-sticks-rotational-devices/
# Le périphérique est déjà marqué comme non-rotatif, on l'ignore
ATTR{queue/rotational}=="0", GOTO="skip"
# Le périphérique a un certain type de support de file d'attente, probablement un vrai disque dur
ATTRS{queue_type}!="none", GOTO="skip"
# Inverse le bit rotatif sur ce périphérique amovible et donne des signaux audibles d'avoir trouvé une correspondance
ATTR{removable}=="1", SUBSYSTEM=="block", SUBSYSTEMS=="usb", ACTION=="add", ATTR{queue/rotational}="0"
ATTR{removable}=="1", SUBSYSTEM=="block", SUBSYSTEMS=="usb", ACTION=="add", RUN+="/bin/beep -f 70 -r 2"
LABEL="skip"
```

3. Rechargez les règles udev et redémarrez le service udev :
```bash
sudo udevadm control --reload-rules
sudo systemctl restart systemd-udevd
```

4. Reconnectez vos clés USB pour appliquer les nouvelles règles.

**Note** : Les images ISO personnalisées incluent déjà ces règles d'optimisation.


---

## Fonctionnalités ✨

- **Double Interface** : Modes CLI et GUI pour plus de flexibilité
- **SUpport LVM**: Prise en charge des volumes LVM dans la détection des disques physiques
- **Détection Intelligente des Appareils** : Identifie automatiquement les SSD et HDD
- **Méthodes d'Effacement Sécurisé** :
  - Passages multiples d'écrasement pour les HDD
  - Effacement cryptographique pour les SSD (aléatoire ou remplissage à zéro)
- **Fonctionnalités de Sécurité** : Détecte les disques système actifs et nécessite une confirmation
- **Traitement Parallèle** : Efface plusieurs disques simultanément
- **Configuration Post-Effacement** : Partitionnement et formatage automatiques
- **Formats Flexibles** : Prend en charge les systèmes de fichiers NTFS, EXT4 et VFAT
- **Options de Déploiement Multiples** : Exécution en tant que code Python, commande Linux ou ISO amorçable


<div style="display: flex; align-items: center;">
  <img src="./img/gui" alt="GUI" width="600" style="margin-right: 20px;">
</div>
---

## Prérequis 📋

- **Privilèges root** (requis pour l'accès aux disques)
- **Python 3** avec **Tkinter** (pour le mode GUI)
- **Connaissances de base en gestion de disque** - cet outil **efface définitivement les données** ⚠️

---

## Installation et Utilisation 🚀

### Utilisation du Code Python 🐍

```bash
git clone https://github.com/frSociete/diskEraserFr.git
cd diskEraser/code/python
sudo python3 main.py         # Mode GUI (par défaut)
sudo python3 main.py --cli   # Mode ligne de commande
```

### Installation en tant que Commande Linux 💻

```bash
sudo mkdir -p /usr/local/bin/diskeraser
sudo cp diskEraser/code/python/*.py /usr/local/bin/diskeraser
sudo chmod +x /usr/local/bin/diskeraser/main.py
sudo ln -s /usr/local/bin/diskeraser/main.py /usr/local/bin/diskeraser

# Puis exécutez :
sudo diskeraser           # Mode GUI
sudo diskeraser --cli     # Mode CLI
```

### Utilisation de l'ISO Amorçable 💿


=======
1. **Créer ou télécharger l'ISO** :
   ```bash
   cd diskEraser/iso && make
   ```

   Ou téléchargez la version précompilée en français : [Disk Eraser Fr ISO v5.3](https://archive.org/download/diskEraser-v5.3/diskEraserFr-v5.3.iso)


2. **Flasher sur USB** :
   ```bash
   sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
   ```

3. **Démarrer depuis l'USB** et suivre les instructions à l'écran

---

## Options en Ligne de Commande ⌨️

```bash
# Options de formatage
-f ext4|ntfs|vfat, --filesystem ext4|ntfs|vfat

# Nombre de passes d'effacement
-p NOMBRE, --passes NOMBRE

# Mode d'interface
--cli           # Utiliser l'interface en ligne de commande

# Exemples :
python3 main.py -f ext4 -p 3      # GUI, EXT4, 3 passes
python3 main.py --cli -f ntfs     # CLI, NTFS, passes par défaut
```

---

## Structure du Projet 📁

```
project/
├── README.md               # Documentation
├── code/                   # Scripts Python
│   ├── disk_erase.py       # Module d'effacement
│   ├── disk_format.py      # Module de formatage
│   ├── disk_operations.py  # Opérations sur disque
│   ├── disk_partition.py   # Module de partitionnement
│   ├── gui_interface.py    # Interface GUI
│   ├── cli_interface.py    # Interface CLI
│   ├── log_handler.py      # Fonctionnalité de journalisation
│   ├── main.py             # Logique principale du programme
│   └── utils.py            # Fonctions utilitaires
├── iso/                    # Ressources de création d'ISO
│   ├── forgeIsoKde.sh       # Générateur d'ISO avec KDE
│   ├── forgeIsoXfce.sh       # Générateur d'ISO avec XFCE4
│   └── makefile            # Automatisation de construction
├── setup.sh                # Installateur de dépendances
└── LICENSE                 # Licence CC 4.0
```

---

## Notes de Sécurité ⚠️

- **Perte de Données** : Cet outil **efface définitivement** les données. Sauvegardez d'abord les informations importantes.
- **Accès Root** : Exécutez avec les privilèges appropriés (root/sudo).
- **Types de Stockage** : Différentes méthodes d'effacement sont optimisées pour différentes technologies de stockage :
  - Pour les HDD : Passes multiples d'écrasement
  - Pour les SSD : Effacement cryptographique (aléatoire ou remplissage à zéro)
- **Protection du Système** : L'outil détecte et avertit des disques système actifs.

---

## Licence ⚖️

Ce projet est sous licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

![Licence Creative Commons](https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png)

Vous êtes libre de :
- **Partager** : Copier et redistribuer le matériel
- **Adapter** : Remixer, transformer et développer le matériel


Selon les conditions suivantes :
- **Attribution** : Fournir le crédit approprié
- **Pas d'Utilisation Commerciale** : Pas d'utilisation à des fins commerciales
- **Partage à l'Identique** : Distribuer les modifications sous la même licence
