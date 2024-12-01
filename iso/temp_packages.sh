#!/bin/bash

cd ./bootable_iso/tmp_packages/
sudo apt-get download linux-image-$(uname -r) initramfs-tools
