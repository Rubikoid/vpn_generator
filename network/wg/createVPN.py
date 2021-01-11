import os
import sys
import subprocess

from os.path import join as pjoin
from typing import List, Tuple

from .settings import Settings


class teamGenerator(object):
    team_id: int
    settings: Settings

    basepath: str
    epath: str
    cliexppath: str

    def __init__(self, tid: int = None, base_path: str = ".", settings: Settings = Settings()):
        self.team_id = tid or 1
        self.settings = settings

        self.basepath = pjoin(base_path, f"team{self.team_id}")

        self.epath = pjoin(self.basepath, "keys")
        self.cliexppath = pjoin(self.basepath, f"team{self.team_id}_conf")

        os.makedirs(self.epath, exist_ok=True)
        os.makedirs(self.cliexppath)

    def generate(self):
        server = self.generate_key(self.epath, "server")
        env = {
            "team_id": self.team_id,

            "server_ip": self.settings.ServerName,
            "port": self.settings.StartPort + self.team_id - 1,

            "subnet": self.settings.ip_pool_base.format(tid=self.team_id, cid=0) + "/24",  # 0 and 1 reserved

            "server_private_key": server[0],
            "server_public_key": server[1],

            "server_internal_addr": self.settings.ip_pool_base.format(tid=self.team_id, cid=1) + "/24",

            "client_keep_alive": (f'PersistentKeepalive = {self.settings.ClientKeepAlive}' if self.settings.ClientKeepAlive else ''),

            "server_post_up": "; ".join(self.settings.PostUp),
            "server_post_down": "; ".join(self.settings.PostDown),
        }
        client_parts = []
        for client_num in range(self.settings.ClientCount):
            client = self.generate_key(self.epath, f"client{client_num}")
            env["client_num"] = client_num
            env["client_private_key"] = client[0]
            env["client_public_key"] = client[1]
            env["client_ip"] = self.settings.ip_pool_base.format(tid=self.team_id, cid=client_num + 2) + "/32"  # 0 and 1 reserved
            env["client_network"] = self.settings.ip_pool_base.format(tid=self.team_id, cid=client_num + 2) + "/24"  # todo: more networks?
            client_parts.append(self.settings.client_config_part.format(**env))
            with open(pjoin(self.cliexppath, f"client{client_num}.conf"), 'w') as f:
                f.write(self.settings.client_config_base.format(**env))

        with open(pjoin(self.basepath, f"server_{self.team_id}.conf"), 'w') as f:
            print(env)
            f.write(self.settings.server_config_base.format(**env))
            f.write("\n\n" + "\n".join(client_parts))

        p = subprocess.Popen("tar -cvf " + f"clients_team{self.team_id}.tar ./*", cwd=self.cliexppath, shell=True)
        p.wait()

    def generate_key(self, save_path: str, name: str) -> Tuple[str, str]:
        # private key gen
        _, privkey = self.wg_do(["genkey"])
        with open(pjoin(save_path, f"{name}-private.key"), 'wb') as f:
            f.write(privkey)

        # public key gen
        _, pubkey = self.wg_do(["pubkey"], input=privkey)
        with open(pjoin(save_path, f"{name}-public.key"), 'wb') as f:
            f.write(pubkey)

        return (privkey.decode().strip(), pubkey.decode().strip())

    def wg_do(self, args: List[str], input: bytes = b"", cwd: str = ".", shell: bool = False) -> Tuple[int, bytes]:
        cmdline = ["wg"]
        cmdline.extend(args)
        with subprocess.Popen(cmdline, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, cwd=cwd) as p:
            stdout = p.communicate(input=input)[0]
            return (p.wait(), stdout)


if __name__ == "__main__":
    test = teamGenerator(1)
    test.generate()
