#!/usr/bin/env python3
import argparse
import sys
import textwrap
from . import core

def build_parser():
    p = argparse.ArgumentParser(prog="QGate", description="QGate - An easy gateway to QDC devices")
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("connect", help="Create SSH tunnels and open RDP to the provided session target")
    c.add_argument("target", help="Target host session id (e.g. sa304610)")
    c.add_argument("--key", "-k", help="Path to private key (default: ~/Downloads/qdc123.pem)")
    c.add_argument("--rdp-port", type=int, default=7373, help="Local RDP forwarded port (default: 7373)")
    c.add_argument("--no-open-rdp", action="store_true", help="Don't auto-open RDP session (just create tunnels)")

    d = sub.add_parser("generate-bat", help="Generate a .bat file template with the chosen target")
    d.add_argument("target", help="Target shortname to embed in the template")
    d.add_argument("--out", "-o", default="tunnel_generated.bat", help="Output filename")

    e = sub.add_parser("disconnect", help="Attempt to close tunnels launched by this tool")
    e.add_argument("--name-contains", help="Filter processes by name substring (e.g. ssh)")

    return p

def main(argv=None):
    description = textwrap.dedent("""
    ==========================================================
              QGate - An easy gateway to QDC devices
    ==========================================================
    Author: Thirumalai Nagalingam
    Version: 0.1.0  License: GPLv3
    ==========================================================
    """)
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "connect":
        core.connect(
            args.target,
            key_path=args.key,
            rdp_port=args.rdp_port,
            open_rdp=not args.no_open_rdp,
        )
    elif args.cmd == "generate-bat":
        core.generate_bat(args.target, args.out)
        print(f"Wrote {args.out}")
    elif args.cmd == "disconnect":
        core.disconnect(name_contains=args.name_contains)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
