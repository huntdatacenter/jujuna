#!/usr/bin/env python3

import re
import sys
import json
import base64


def decode_address(address):
    hex_ip, hex_port = address.split(':')
    ip = '.'.join([str(item) for item in reversed(list(base64.b16decode(hex_ip)))])
    port = int.from_bytes(base64.b16decode(hex_port), byteorder='big')
    return ip, port


def sockets():
    with open('/proc/net/tcp', 'r') as f:
        lines = []
        for line in f:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            lines.append(line.split())

    sock_list = []
    header = lines[0]

    for line in lines[1:]:
        line_struct = {}
        for idx, head in enumerate(header):
            line_struct[head] = line[idx]
        sock_list.append(line_struct)

    data_list = []
    for item in sock_list:
        data_item = {}
        data_item['local_ip'], data_item['local_port'] = decode_address(item['local_address'])
        data_item['rem_ip'], data_item['rem_port'] = decode_address(item['rem_address'])
        data_list.append(data_item)

    return data_list


def main():
    data = {
        'sockets': sockets(),
    }

    print(json.dumps(data))
    sys.exit(0)


if __name__ == "__main__":
    main()
