#!/usr/bin/env python3

import json
import sys
import os
import stat


def main():
    if len(sys.argv) != 2:
        raise Exception('Specify exactly one filepath.')
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        raise Exception("Path '{}' does not exist.".format(filepath))

    file_stat = os.stat(filepath)

    file_vars = {
        'st_mode': file_stat.st_mode,
        'st_ino': file_stat.st_ino,
        'st_dev': file_stat.st_dev,
        'st_nlink': file_stat.st_nlink,
        'st_uid': file_stat.st_uid,
        'st_gid': file_stat.st_gid,
        'st_size': file_stat.st_size,
        'st_atime': file_stat.st_atime,
        'st_mtime': file_stat.st_mtime,
        'st_ctime': file_stat.st_ctime,
        'is_dir': stat.S_ISDIR(file_stat.st_mode),
        'is_chr': stat.S_ISCHR(file_stat.st_mode),
        'is_blk': stat.S_ISBLK(file_stat.st_mode),
        'is_reg': stat.S_ISREG(file_stat.st_mode),
        'is_fifo': stat.S_ISFIFO(file_stat.st_mode),
        'is_lnk': stat.S_ISLNK(file_stat.st_mode),
        'is_sock': stat.S_ISSOCK(file_stat.st_mode),
        'imode': stat.S_IMODE(file_stat.st_mode),
        'ifmt': stat.S_IFMT(file_stat.st_mode),
    }

    print(json.dumps(file_vars))
    sys.exit(0)


if __name__ == "__main__":
    main()
