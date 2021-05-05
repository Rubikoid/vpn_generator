import argparse
import sys

# from .settings import Settings
# from .createVPN import teamGenerator
import wg


def main():
    parser = argparse.ArgumentParser(description='VPN configs gen.')

    parser.add_argument("-n", "--name", action="store", type=str, help="Network name", required=True)
    parser.add_argument("-l", "--host", action="store", type=str, help="Server host", required=True)
    parser.add_argument("-p", "--port", action="store", type=int, help="Start port (or one port for server)", required=True)
    parser.add_argument("-c", "--clients", action="store", type=int, help="Clients count (default: 10)", default=16)
    parser.add_argument("-k", "--keepalive", action="store", type=int, help="Client keepalive (default: None)", default=None)
    parser.add_argument("-i", "--ip_pool_base", action="store", type=str,
                        help="Format string for ip generation (default: 10.20.{tid}.{cid})", default="10.20.{tid}.{cid}")

    # parser.add_argument("--server_config_base", action="store", type=str, help="Server base config")
    # parser.add_argument("--client_config_base", action="store", type=str, help="Client base config")
    # parser.add_argument("--client_config_part", action="store", type=str, help="Client base config part")

    # subp = parser.add_subparsers(title="iptables modules", required=False)
    parser.add_argument("-f", "--fw_rules", action='append', help=f"FW Rules, possible variants: {','.join(wg.settings.iptables_lib.keys())}")
    for name, data in wg.settings.iptables_lib.items():
        wg.settings.generate_subparser(parser, name, data["args"])

    args = parser.parse_args()

    settings = wg.settings.Settings()

    settings.ServerName = args.host or settings.ServerName
    settings.StartPort = args.port or settings.StartPort
    settings.ClientCount = args.clients or settings.ClientCount
    settings.ip_pool_base = args.ip_pool_base or settings.ip_pool_base
    settings.ClientKeepAlive = args.keepalive or settings.ClientKeepAlive

    if args.fw_rules is not None:
        for rule_name in args.fw_rules:
            rule = wg.settings.iptables_lib[rule_name]
            pUp = rule["up"].format(n=args)
            pDown = rule["down"].format(n=args)
            settings.PostUp.append(pUp)
            settings.PostDown.append(pDown)

    print(args)
    print(settings.PostUp, settings.PostDown)

    gen = wg.createVPN.teamGenerator(args.name, ".", settings)
    gen.generate()

    # settings.server_config_base = args["server_config_base"] or settings.server_config_base
    # settings.client_config_base = args["client_config_base"] or settings.client_config_base
    # settings.client_config_part = args["client_config_part"] or settings.client_config_part


if __name__ == "__main__":
    main()
