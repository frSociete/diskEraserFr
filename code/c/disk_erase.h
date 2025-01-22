#ifndef DISK_ERASE_H
#define DISK_ERASE_H

void write_random_data(const char *device, int passes);
void write_zero_data(const char *device);
void erase_disk(const char *device, int passes);

#endif // DISK_ERASE_H
