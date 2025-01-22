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

    for (int pass = 0; pass < passes; ++pass) {
        printf("Writing random data pass %d to %s...\n", pass + 1, device);
        char *buffer = malloc(BLOCK_SIZE);
        if (!buffer) {
            perror("Memory allocation failed");
            close(fd);
            exit(EXIT_FAILURE);
        }

        off_t written = 0;
        while (written < disk_size) {
            size_t to_write = (size_t) (disk_size - written > BLOCK_SIZE ? BLOCK_SIZE : disk_size - written);
            for (size_t i = 0; i < to_write; ++i) buffer[i] = rand() % 256;
            if (write(fd, buffer, to_write) < 0) {
                perror("Error writing random data");
                free(buffer);
                close(fd);
                exit(EXIT_FAILURE);
            }
            written += to_write;
        }
        lseek(fd, 0, SEEK_SET);
        free(buffer);
    }
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
        size_t to_write = (size_t) (disk_size - written > BLOCK_SIZE ? BLOCK_SIZE : disk_size - written);
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

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include "disk_erase.h"

void erase_disk(const char *device, int passes) {
    char device_path[256];
    snprintf(device_path, sizeof(device_path), "/dev/%s", device);

    printf("Erasing %s with %d random data passes and a final zero pass...\n", device, passes);

    int fd = open(device_path, O_WRONLY);
    if (fd < 0) {
        fprintf(stderr, "Error opening device %s for random write: %s\n", device_path, strerror(errno));
        exit(EXIT_FAILURE);
    }

    size_t block_size = 4096;
    unsigned char *buffer = malloc(block_size);
    if (!buffer) {
        fprintf(stderr, "Memory allocation failed.\n");
        close(fd);
        exit(EXIT_FAILURE);
    }

    for (int pass = 0; pass < passes; ++pass) {
        printf("Writing random data pass %d to %s...\n", pass + 1, device);

        ssize_t bytes_written;
        while ((bytes_written = write(fd, buffer, block_size)) > 0) {
            if (bytes_written < 0) {
                fprintf(stderr, "Write error on pass %d: %s\n", pass + 1, strerror(errno));
                free(buffer);
                close(fd);
                exit(EXIT_FAILURE);
            }
        }

        // Reset file descriptor position
        if (lseek(fd, 0, SEEK_SET) < 0) {
            fprintf(stderr, "Error resetting position on device %s: %s\n", device_path, strerror(errno));
            free(buffer);
            close(fd);
            exit(EXIT_FAILURE);
        }
    }

    // Write zeros as the final pass
    memset(buffer, 0, block_size);
    printf("Writing final zero pass to %s...\n", device);

    ssize_t bytes_written;
    while ((bytes_written = write(fd, buffer, block_size)) > 0) {
        if (bytes_written < 0) {
            fprintf(stderr, "Write error on final zero pass: %s\n", strerror(errno));
            free(buffer);
            close(fd);
            exit(EXIT_FAILURE);
        }
    }

    free(buffer);
    close(fd);

    printf("Disk %s successfully erased.\n", device);
}

