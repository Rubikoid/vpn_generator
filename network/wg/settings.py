import os
import argparse
from sys import argv

from typing import List

file_path = os.path.dirname(os.path.abspath(__file__))


def generate_subparser(parser: argparse.ArgumentParser, name: str, data):
    # parser: argparse.ArgumentParser = subparsers.add_parser(name, help=f"{name} args")
    for k in data:
        parser.add_argument(*map(lambda x: f"--fw_{name}_{x}", k["base"]), **k["args"])


iptables_lib = {
    'input': {
        'up': "iptables -A FORWARD -i %i -j ACCEPT",
        'down': "iptables -D FORWARD -i %i -j ACCEPT",
        'args': []
    },
    'input_ip': {
        'up': "iptables -A FORWARD -i %i -j ACCEPT -s {n.fw_input_ip_ip}",
        'down': "iptables -D FORWARD -i %i -j ACCEPT -s {n.fw_input_ip_ip}",
        'args': [
            {
                "base": ["ip"],
                "args": {
                    "action": "store",
                    "type": str,
                    "help": "Ip for allowing connection",
                }
            }
        ]
    },
    'output': {
        'up': "iptables -A FORWARD -o %i -j ACCEPT",
        'down': "iptables -D FORWARD -o %i -j ACCEPT",
        'args': []
    },
    'output_ip': {
        'up': "iptables -A FORWARD -o %i -j ACCEPT -d {n.fw_output_ip_ip}",
        'down': "iptables -D FORWARD -o %i -j ACCEPT -d {n.fw_output_ip_ip}",
        'args': [
            {
                "base": ["ip"],
                "args": {
                    "action": "store",
                    "type": str,
                    "help": "Ip for allowing connection",
                }
            }
        ]
    },
    'net_masq': {
        'up': "iptables -t nat -A POSTROUTING -o {n.fw_net_masq_interface} -j MASQUERADE",
        'down': "iptables -t nat -D POSTROUTING -o {n.fw_net_masq_interface} -j MASQUERADE",
        'args': [
            {
                "base": ["interface"],
                "args": {
                    "action": "store",
                    "type": str,
                    "help": "Interface for masquerade",
                }
            }
        ]
    }
}


class Settings(object):
    ServerName: str = "gamma.kksctf.ru"
    StartPort: int = 51820
    ClientCount: int = 10
    server_config_base: str = open(os.path.join(file_path, "server_base.conf"), "r").read()
    client_config_base: str = open(os.path.join(file_path, "client_base.conf"), "r").read()
    client_config_part: str = open(os.path.join(file_path, "client_part.conf"), "r").read()
    ip_pool_base: str = "10.20.0.{cid}"
    PostUp: List[str] = []
    PostDown: List[str] = []
    ClientKeepAlive = None
