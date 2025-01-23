#include "disk_erase.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#define BLOCK_SIZE 4096

void write_random_data(const char *device, int passes) {
    int fd = open(device, O_WRONLY);
    if (fd < 0) {
        perror("Error opening device for random write");
        exit(EXIT_FAILURE);
    }

    off_t disk_size = lseek(fd, 0, SEEK_END);
    if (disk_size < 0) {
        perror("Error determining disk size");
        close(fd);
        exit(EXIT_FAILURE);
    }
    lseek(fd, 0, SEEK_SET);

    int urandom_fd = open("/dev/urandom", O_RDONLY);
    if (urandom_fd < 0) {
        perror("Error opening /dev/urandom");
        close(fd);
        exit(EXIT_FAILURE);
    }

    for (int pass = 0; pass < passes; ++pass) {
        printf("Writing random data pass %d to %s...\n", pass + 1, device);
        char *buffer = malloc(BLOCK_SIZE);
        if (!buffer) {
            perror("Memory allocation failed");
            close(fd);
            close(urandom_fd);
            exit(EXIT_FAILURE);
        }

        off_t written = 0;
        while (written < disk_size) {
            size_t to_write = (size_t)(disk_size - written > BLOCK_SIZE ? BLOCK_SIZE : disk_size - written);
            
            // Read secure random data into the buffer
            if (read(urandom_fd, buffer, to_write) != (ssize_t)to_write) {
                perror("Error reading random data from /dev/urandom");
                free(buffer);
                close(fd);
                close(urandom_fd);
                exit(EXIT_FAILURE);
            }

            if (write(fd, buffer, to_write) < 0) {
                perror("Error writing random data");
                free(buffer);
                close(fd);
                close(urandom_fd);
                exit(EXIT_FAILURE);
            }
            written += to_write;
        }
        lseek(fd, 0, SEEK_SET);
        free(buffer);
    }

    close(urandom_fd);
    close(fd);
}

void write_zero_data(const char *device) {
    int fd = open(device, O_WRONLY);
    if (fd < 0) {
        perror("Error opening device for zero write");
        exit(EXIT_FAILURE);
    }

    off_t disk_size = lseek(fd, 0, SEEK_END);
    if (disk_size < 0) {
        perror("Error determining disk size");
        close(fd);
        exit(EXIT_FAILURE);
    }
    lseek(fd, 0, SEEK_SET);

    printf("Writing final zero pass to %s...\n", device);
    char *buffer = calloc(BLOCK_SIZE, 1);
    if (!buffer) {
        perror("Memory allocation failed");
        close(fd);
        exit(EXIT_FAILURE);
    }

    off_t written = 0;
    while (written < disk_size) {
        size_t to_write = (size_t)(disk_size - written > BLOCK_SIZE ? BLOCK_SIZE : disk_size - written);
        if (write(fd, buffer, to_write) < 0) {
            perror("Error writing zero data");
            free(buffer);
            close(fd);
            exit(EXIT_FAILURE);
        }
        written += to_write;
    }
    free(buffer);
    close(fd);
}

void erase_disk(const char *device, int passes) {
    char device_path[256];
    snprintf(device_path, sizeof(device_path), "/dev/%s", device);

    printf("Erasing %s with %d random data passes and a final zero pass...\n", device, passes);

    write_random_data(device_path, passes);
    write_zero_data(device_path);

    printf("Disk %s successfully erased.\n", device);
}
