#!/usr/bin/env python3

import json
import sys


def main():
    mount_data = {}
    with open('/proc/mounts', 'r') as mountfile:
        mount_lines = mountfile.read().split('\n')[:-1]
        for mount_line in mount_lines:
            mount_items = mount_line.split(' ')
            mount_parsed = {
                'mountpoint': mount_items[1],
                'fs': mount_items[2],
                'params': mount_items[3].split(','),
            }
            if '/' not in mount_items[0]:
                if mount_items[0] not in mount_data:
                    mount_data[mount_items[0]] = []
                mount_data[mount_items[0]].append(mount_parsed)
            else:
                mount_data[mount_items[0]] = mount_parsed

    print(json.dumps(mount_data))
    sys.exit(0)


if __name__ == "__main__":
    main()
