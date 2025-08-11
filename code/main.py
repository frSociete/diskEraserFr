#!/usr/bin/env python3
import os
import sys
from argparse import ArgumentParser
from cli_interface import run_cli_mode
from gui_interface import run_gui_mode

def main():
    parser = ArgumentParser(description="Outil sécurisé d'effacement de disque")
    parser.add_argument('--cli', action='store_true', help="Exécuter en mode ligne de commande au lieu de l'interface graphique")
    parser.add_argument('-f', '--filesystem', choices=['ext4', 'ntfs', 'vfat'], help="Type de système de fichiers à utiliser")
    parser.add_argument('-p', '--passes', type=int, default=5, help="Nombre de passes pour l'effacement")
    parser.add_argument('--crypto', action='store_true', help="Utiliser l'effacement cryptographique à la place de la méthode multi-passes standard")
    parser.add_argument('--zero', action='store_true', help="Remplir le disque chiffré avec des zéros au lieu de données aléatoires")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("Ce programme doit être exécuté avec les privilèges administrateur (root) !")
        sys.exit(1)

    if args.cli:
        run_cli_mode(args)
    else:
        run_gui_mode()

if __name__ == "__main__":
    main()