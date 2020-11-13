import os
import sys
import subprocess


class Settings(object):
    SeverName = "gamma.kksctf.ru"
    StartPort = 51820
    ClientCount = 10
    server_config_base = open("server_base.conf", "r").read()
    client_config_base = open("client_base.conf", "r").read()
    client_config_part = open("client_part.conf", "r").read()
    ip_pool_base = "10.20.{tid}.{cid}"


class teamGenerator(object):
    def __init__(self, tid=None):
        self._team_id = tid or 1

        self.basepath = os.path.join(".", f"team{self._team_id}")

        self.epath = os.path.join(self.basepath, "keys")
        self.cliexppath = os.path.join(self.basepath, f"team{self._team_id}_conf")

        os.makedirs(self.epath, exist_ok=True)
        os.makedirs(self.cliexppath)

    def generate(self):
        server = self.generate_key(self.epath, "server")
        env = { 
            "port": Settings.StartPort + self._team_id - 1,
            "server_ip": Settings.SeverName,
            "subnet": Settings.ip_pool_base.format(tid=self._team_id, cid=0) + "/24", # 0 and 1 reserved
            "team_id": self._team_id,
            "server_private_key": server[0],
            "server_public_key": server[1],
            "server_internal_addr": Settings.ip_pool_base.format(tid=self._team_id, cid=1) + "/24", 
        }
        client_parts = []
        for client_num in range(Settings.ClientCount):
            client = self.generate_key(self.epath, f"client{client_num}")
            env["client_num"] = client_num
            env["client_private_key"] = client[0]
            env["client_public_key"] = client[1]
            env["client_ip"] = Settings.ip_pool_base.format(tid=self._team_id, cid=client_num + 2) + "/32" # 0 and 1 reserved
            env["client_network"] = Settings.ip_pool_base.format(tid=self._team_id, cid=client_num + 2) + "/24" # todo: more networks?
            client_parts.append(Settings.client_config_part.format(**env))
            with open(os.path.join(self.cliexppath, f"client{client_num}.conf"), 'w') as f:
                f.write(Settings.client_config_base.format(**env))
         
        with open(os.path.join(self.basepath, f"server_{self._team_id}.conf"), 'w') as f:
                f.write(Settings.server_config_base.format(**env))
                f.write("\n\n" + "\n".join(client_parts))

        p = subprocess.Popen("tar -cvf " + f"clients_team{self._team_id}.tar ./*", cwd=self.cliexppath, shell=True)
        p.wait()
    
    def generate_key(self, save_path, name):
        _, privkey = self.wg_do(["genkey"])
        with open(os.path.join(save_path, f"{name}-private.key"), 'wb') as f:
                f.write(privkey)
        _, pubkey = self.wg_do(["pubkey"], input=privkey)
        with open(os.path.join(save_path, f"{name}-public.key"), 'wb') as f:
                f.write(pubkey)
        return (privkey.decode().strip(), pubkey.decode().strip())

    def wg_do(self, args, input=b"", cwd=".", shell=False):
        cmdline = ["wg"]
        cmdline.extend(args)
        with subprocess.Popen(cmdline, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, cwd=cwd) as p:
            stdout = p.communicate(input=input)[0]
            return (p.wait(), stdout)


if __name__ == "__main__":
    test = teamGenerator(1)
    test.generate()
