#!/usr/bin/env python3

import re
import sys
import json
import base64
import ipaddress


def decode_address(address):
    hex_ip, hex_port = address.split(':')
    ip_join, ipv6 = (':', True) if len(hex_ip) == 32 else ('.', False)
    if ipv6:
        ipv6_string = ":".join([hex_ip[i:i + 4] for i in range(0, 32, 4)])
        ip = ipaddress.ip_address(ipv6_string).exploded
    else:
        ip_items = [str(item) for item in reversed(list(base64.b16decode(hex_ip)))]
        ip = ip_join.join(ip_items)
    port = int.from_bytes(base64.b16decode(hex_port), byteorder='big')
    return ip, port


def _read_tcp(path='/proc/net/tcp'):
    lines = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            lines.append(line.split())
    sock_list = []
    header = lines[0]
    for line in lines[1:]:
        line_struct = {}
        for idx, head in enumerate(header):
            key = 'remote_address' if head == 'rem_address' else head
            line_struct[key] = line[idx]
        sock_list.append(line_struct)
    return sock_list


def sockets():
    sock_list = []
    sock_list.extend(_read_tcp())
    sock_list.extend(_read_tcp('/proc/net/tcp6'))

    data_list = []
    for item in sock_list:
        data_item = {}
        data_item['local_ip'], data_item['local_port'] = decode_address(item['local_address'])
        data_item['rem_ip'], data_item['rem_port'] = decode_address(item['remote_address'])
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
