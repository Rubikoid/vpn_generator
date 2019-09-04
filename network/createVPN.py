import os
import sys
import subprocess


class Settings(object):
    SeverName = "vpn.rubikoid.ru"
    StartPort = 5000
    ClientCount = 10
    easy_rsa_vars = {
        "EASYRSA_REQ_COUNTRY": "RU",
        "EASYRSA_REQ_PROVINCE": "Moscow",
        "EASYRSA_REQ_CITY": "Moscow",
        "EASYRSA_REQ_ORG": "KKS",
        "EASYRSA_REQ_EMAIL": "rubikoid@rubikoid.ru",
        "EASYRSA_REQ_OU": "KKS",
        "EASYRSA_KEY_SIZE": "2048",
    }
    server_config_base = open("server_base.conf", "r").read()
    client_config_base = open("client_base.conf", "r").read()
    ip_pool_generator = "10.20.{tid}.0"


class teamGenerator(object):
    def __init__(self, tid=None):
        self._team_id = tid or 1

        self.epath = os.path.join(".", "CAs", f"ca_team{self._team_id}")
        self.exppath = os.path.join(".", "ovpn_data", f"team{self._team_id}")
        self.cliexppath = os.path.join(self.exppath, "clients")

        os.makedirs(os.path.join(".", "CAs"), exist_ok=True)
        os.makedirs(self.exppath)
        os.makedirs(self.cliexppath)

    def generateKeys(self):
        p = subprocess.Popen(["make-cadir", self.epath])
        p.wait()

        os.rename(os.path.join(self.epath, "vars"), os.path.join(self.epath, "vars.old"))
        with open(os.path.join(self.epath, "vars"), 'w') as fvars:
            fvars.write("\n".join(f"set_var {i}\t\"{v}\"" for i, v in Settings.easy_rsa_vars.items()))

        self.easyRsaDo(["init-pki"])
        self.easyRsaDo(["--batch", f"--req-cn={Settings.SeverName}", "build-ca", "nopass"])
        self.easyRsaDo(["gen-crl"])

        # server
        srv_name = f"server_team{self._team_id}"
        self.easyRsaDo(["--batch", f"--req-cn={srv_name}", "gen-req", srv_name, "nopass"])
        self.easyRsaDo(["--batch", "sign-req", "server", srv_name])

        # client
        for i in range(Settings.ClientCount):
            cli_name = f"client_team{self._team_id}_{i}"
            self.easyRsaDo(["--batch", f"--req-cn={cli_name}", "gen-req", cli_name, "nopass"])
            self.easyRsaDo(["--batch", "sign-req", "client", cli_name])

        p = subprocess.Popen(["openvpn", "--genkey", "--secret", "pki/ta.key"], cwd=self.epath)
        p.wait()

    def generateDH(self):
        self.easyRsaDo(["gen-dh"])

    def generateConfigs(self):
        ca_data = open(os.path.join(self.epath, "pki", "ca.crt"), 'r').read()
        ta_key = open(os.path.join(self.epath, "pki", "ta.key"), 'r').read()
        dh_data = open(os.path.join(self.epath, "pki", "dh.pem"), 'r').read()

        # server
        srv_cert = open(os.path.join(self.epath, "pki", "issued", f"server_team{self._team_id}.crt"), 'r').read()
        srv_key = open(os.path.join(self.epath, "pki", "private", f"server_team{self._team_id}.key"), 'r').read()

        env = {
            "ca_data": ca_data,
            "tls_data": ta_key,
            "dh_data": dh_data,
            "srv_cert_data": srv_cert,
            "srv_key_data": srv_key,
            "server_port": Settings.StartPort + self._team_id - 1,
            "server_ip": Settings.SeverName,
            "ip_pool": Settings.ip_pool_generator.format(tid=self._team_id),
            "team_id": self._team_id
        }

        with open(os.path.join(self.exppath, "server.ovpn"), 'w') as f:
            f.write(Settings.server_config_base.format(**env))

        for i in range(Settings.ClientCount):
            client_cert = open(os.path.join(self.epath, "pki", "issued", f"client_team{self._team_id}_{i}.crt"), 'r').read()
            client_key = open(os.path.join(self.epath, "pki", "private", f"client_team{self._team_id}_{i}.key"), 'r').read()
            env["cl_cert_data"] = client_cert
            env["cl_key_data"] = client_key
            with open(os.path.join(self.cliexppath, f"client_team{self._team_id}_{i}.ovpn"), 'w') as f:
                f.write(Settings.client_config_base.format(**env))

        p = subprocess.Popen(["tar", "cvf", f"clients_team{self._team_id}.tar", "./clients"], cwd=self.exppath)
        p.wait()

    def easyRsaDo(self, args):
        cmdline = ["./easyrsa"]
        cmdline.extend(args)
        p = subprocess.Popen(cmdline, cwd=self.epath)
        return p.wait()


if __name__ == "__main__":
    test = teamGenerator(1)
    test.generateKeys()
    test.generateDH()
    test.generateConfigs()
