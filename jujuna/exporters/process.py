#!/usr/bin/env python3

import os
import json
import sys


def main():
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    pnames = {}
    for pid in pids:
        pname_raw = open(os.path.join('/proc', pid, 'cmdline'), 'rb').read()
        pname = pname_raw.decode('utf-8').replace('\x00', ' ').strip().split(' ')
        pnames[pname[0]] = {
            'pid': pid,
            'params': pname[1:] if len(pname) > 1 else [],
        }

    print(json.dumps(pnames))
    sys.exit(0)


if __name__ == "__main__":
    main()
