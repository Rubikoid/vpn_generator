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
        "EASYRSA_REQ_EMAIL": "rubikoid@kksctf.ru",
        "EASYRSA_REQ_OU": "KKS",
        "EASYRSA_KEY_SIZE": "2048",
    }
    server_config_base = open("server_base.conf", "r").read()
    client_config_base = open("client_base.conf", "r").read()


class teamGenerator(object):
    def __init__(self, tid=None):
        self._team_id = tid or 1

        self.epath = os.path.join(".", "CAs", f"ca_team{self._team_id}")
        self.exppath = os.path.join(".", "ovpn_data", f"team{self._team_d}")
        self.cliexppath = os.path.join(self.exppath, "clients")

        os.makedirs(os.path.join(".", "CAs"))
        os.makedirs(self.exppath)
        os.makedirs(self.cliexppath)

    def generateKeys(self):
        p = subprocess.Popen(["make-cadir", self.epath])
        p.wait()

        os.rename(os.path.join(self.epath, "vars"), os.path.join(self.epath, "vars.old"))
        with open(os.path.join(self.epath, "vars"), 'w') as fvars:
            fvars.write("\n".join(f"set_var {i}\t\"{v}\"" for i, v in Settings.easy_rsa_vars))

        self.easyRsaDo(["init-pki"])
        self.easyRsaDo(["--batch", "build-ca", f"--req-cn={Settings.SeverName}", "nopass"])
        self.easyRsaDo(["gen-crl"])

        # server
        self.easyRsaDo(["--batch", "gen-req", f"server_team{self._team_id}", "nopass"])
        self.easyRsaDo(["--batch", "sign-req", "server", f"server_team{self._team_id}"])

        # client
        for i in range(Settings.ClientCount):
            self.easyRsaDo(["--batch", "gen-req", f"client_team{self._team_id}_{i}", "nopass"])
            self.easyRsaDo(["--batch", "sign-req", "client", f"client_team{self._team_id}_{i}"])

        self.easyRsaDo(["gen-dh"])
        p = subprocess.Popen(["openvpn", "--genkey", "--secret pki/ta.key"], self.epath)
        p.wait()

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
        }

        with open(os.path.join(self.exppath, "server.conf")) as f:
            f.write(Settings.server_config_base.format(**env))

        for i in range(Settings.ClientCount):
            client_cert = open(os.path.join(self.epath, "pki", "issued", f"client_team{self._team_id}_{i}.crt"), 'r').read()
            client_key = open(os.path.join(self.epath, "pki", "private", f"client_team{self._team_id}_{i}.crt"), 'r').read()
            env["cl_cert_data"] = client_cert
            env["cl_key_data"] = client_key
            with open(os.path.join(self.cliexppath, f"client_team{self._team_id}_{i}.conf")) as f:
                f.write(Settings.client_config_base.format(**env))

    def easyRsaDo(self, args):
        cmdline = ["./easyrsa"]
        cmdline.extend(args)
        p = subprocess.Popen(cmdline, cwd=self.epath)
        return p.wait()
