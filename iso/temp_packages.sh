#!/bin/bash

mkdir -p /tmp/kernel-packages
cd /tmp/kernel-packages
sudo apt-get download linux-image-$(uname -r) initramfs-tools
