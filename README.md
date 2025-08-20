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
> - **Répartition d'Usure des SSD** : Rend les méthodes traditionnelles d'écrasement moins efficaces
> - **Sur-provisionnement** : L'espace réservé caché peut conserver des données
> - **Durée de Vie de l'Appareil** : Les passages multiples peuvent réduire la longévité du SSD
>
> Pour les SSD, il est recommandé d'utiliser l'effacement cryptographique plutôt que les passages multiples d'écrasement.

***

⚠️ **AVERTISSEMENT DE COMPATIBILITÉ DES CLÉS USB**

Le noyau Linux marque souvent incorrectement les clés USB comme des périphériques rotatifs, ce qui peut impacter les performances lors des effacements sur USB.

**Pour corriger ce problème (hors ISO officielle), créez la règle suivante :**

```bash
sudo nano /etc/udev/rules.d/usb-flash.rules
# ... puis copiez le contenu proposé dans la documentation ...
sudo udevadm control --reload-rules
sudo systemctl restart systemd-udevd
```
Reconnectez vos clés USB pour appliquer les règles.

***

## Fonctionnalités ✨

- **Double Interface** : Modes CLI et GUI pour plus de flexibilité
- **Détection Intelligente des Disques** : Identifie automatiquement les SSD et HDD
- **Support LVM** : Prise en charge des volumes LVM dans la détection des disques physiques
- **Méthodes d’Effacement Sécurisé** :
   - Passes multiples d'écrasement (HDD)
   - Effacement cryptographique (SSD, aléatoire ou zéro)
- **Fonctionnalités de Sécurité** : Détecte les disques système actifs et nécessite une confirmation
- **Traitement Parallèle** : Effacement simultané de plusieurs disques
- **Post-Effacement** : Partitionnement et formatage automatiques
- **Formats Flexibles** : EXT4, NTFS, VFAT pris en charge
- **Déploiement** : Exécution comme script Python, commande Linux ou ISO bootable
- **Journalisation Complète** :
   - Suivi en temps réel de la progression
   - Gestion fine des erreurs
   - Audit détaillé (session, historique)
   - Export PDF des logs pour archivage et conformité

<div style="display: flex; align-items: center;">
  <img src="./img/gui" alt="GUI" width="600" style="margin-right: 20px;">
</div>

***

## Prérequis 📋

- **Privilèges root** (accès disque)
- **Python 3** avec **Tkinter** pour le mode GUI
- **Notions de gestion de disque** – cet outil **efface définitivement les données** ⚠️

***

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

### Utilisation de l’ISO amorçable 💿

1. **Créer ou télécharger l'ISO** :
   ```bash
   cd diskEraser/iso && make
   ```
   Ou téléchargez la version précompilée en français :  
   [Disk Eraser Fr ISO v5.3](https://archive.org/download/diskEraser-v5.3/diskEraserFr-v5.3.iso)

2. **Flashez sur une clé USB :**
   ```bash
   sudo dd if=secure_disk_eraser.iso of=/dev/sdX bs=4M status=progress
   ```

3. **Démarrez sur l’USB** et suivez les instructions à l’écran.

***

## Options en Ligne de Commande ⌨️

```bash
# Système de fichiers
-f ext4|ntfs|vfat, --filesystem ext4|ntfs|vfat

# Nombre de passes (HDD)
-p NOMBRE, --passes NOMBRE

# Interface (CLI ou GUI)
--cli          # Mode ligne de commande

# Exemples :
python3 main.py -f ext4 -p 3      # GUI, EXT4, 3 passes
python3 main.py --cli -f ntfs     # CLI, NTFS, passes par défaut
```

***

## Structure du Projet 📁

```
project/
├── README.md
├── code/
│   ├── disk_erase.py
│   ├── disk_format.py
│   ├── disk_operations.py
│   ├── disk_partition.py
│   ├── gui_interface.py
│   ├── cli_interface.py
│   ├── log_handler.py
│   ├── main.py
│   └── utils.py
├── iso/
│   ├── forgeIsoKde.sh
│   ├── forgeIsoXfce.sh
│   └── makefile
├── setup.sh
└── LICENSE
```

***

## Notes de Sécurité ⚠️

- **Perte de Données** : Cet outil efface *définitivement* les données. Sauvegardez d’abord !
- **Accès root requis**
- **Typologie des Stockages** : Optimisé pour différents supports :
   - HDD : écrasement multi-passes
   - SSD : effacement cryptographique
- **Protection système** : Avertissement et détection des disques système actifs
- **Audit** : Conservation des logs pour vérification et analyse

***

## Licence ⚖️

Projet sous licence [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/).

![Licence Creative Commons](https://i.creativecommons.org/l/by-nc-sa/4. libre de :
- **Partager** : Copier et redistribuer le matériel
- **Adapter** : Remixer, transformer, faire évoluer sous même licence

Selon :
- **Attribution** obligatoire
- **Pas d’utilisation commerciale**
- **Partage dans les mêmes conditions**