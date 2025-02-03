#ifndef DISK_ERASE_H
#define DISK_ERASE_H

int is_ssd(const char *device);
void erase_disk(const char *device, int passes);

#endif