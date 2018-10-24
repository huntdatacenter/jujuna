#!/usr/bin/env python3

import json
import sys
import dbus


def main():
    bus = dbus.SystemBus()
    systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    manager = dbus.Interface(systemd1, dbus_interface='org.freedesktop.systemd1.Manager')

    units_list = manager.ListUnits()

    services = {}

    for unit in units_list:
        if unit[0].endswith('.service'):
            unit_name = unit[0].replace('.service', '')

            services[unit_name] = {
                'name': unit[0],
                'description': unit[1],
                'loaded': unit[2],
                'active': unit[3],
                'status': unit[4],
            }

    systemd_data = {
        'services': services,
    }

    print(json.dumps(systemd_data))
    sys.exit(0)


if __name__ == "__main__":
    main()
