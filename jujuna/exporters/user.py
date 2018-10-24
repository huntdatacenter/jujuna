#!/usr/bin/env python3

import json
import sys
import pwd
import grp


def main():

    user_data = {}

    for user in pwd.getpwall():
        user_data[user[0]] = {
            'uid': user[2],
            'gid': user[3],
            'group': grp.getgrgid(user[3])[0],
            'gecos': user[4],
            'dir': user[5],
            'shell': user[6],
        }

    print(json.dumps(user_data))
    sys.exit(0)


if __name__ == "__main__":
    main()
