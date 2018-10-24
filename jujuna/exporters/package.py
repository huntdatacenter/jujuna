#!/usr/bin/env python3

import json
import sys
import apt


def main():
    pkg_data = {}

    cache = apt.Cache()
    installed = {}
    for mypkg in apt.Cache():
        if cache[mypkg.name].is_installed:
            installed[mypkg.name] = {
                'id': mypkg.id,
                'name': mypkg.name,
                'shortname': mypkg.shortname,
                'versions': list(dict(mypkg.versions).keys())
            }

    pkg_data = {
        'installed': installed
    }

    print(json.dumps(pkg_data))
    sys.exit(0)


if __name__ == "__main__":
    main()
