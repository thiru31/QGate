import os
import random
import shutil
import subprocess
import sys
import time
from . import utils

def _rand_port(exclude=None):
    exclude = exclude or set()
    while True:
        p = random.randint(1024, 65535)
        if p not in exclude:
            return p

def _format_target(input_target):
    # if user passes shortname like sa304610, convert it to Complete cluster id name
    if "." in input_target:
        return input_target
    return f"{input_target}.sa.svc.cluster.local"

def connect(target, key_path=None, rdp_port=7373, open_rdp=True):
    """
    Create two SSH forwards inside Windows Terminal:
      - one forwarding local PORT1 -> target:22 (for ssh jump)
      - second forwarding local rdp_port -> localhost:3389 via the ssh tunnel
    """
    if sys.platform != "win32":
        raise RuntimeError("connect() currently supports Windows only (wt.exe + mstsc).")

    wt = shutil.which("wt.exe")
    if not wt:
        raise FileNotFoundError("Windows Terminal (wt.exe) not found in PATH.")

    ssh = shutil.which("ssh")
    if not ssh:
        raise FileNotFoundError("ssh client not found in PATH.")

    key_path = key_path or utils.default_key_path()
    if not os.path.exists(key_path):
        print(f"Warning: key not found at {key_path}; ssh may prompt for passphrase or fail.", flush=True)

    formatted_target = _format_target(target)

    # pick a random port for the inner ssh forward (avoid rdp_port)
    port1 = _rand_port(exclude={rdp_port})

    # Tunnel1: ssh -i KEY -L PORT1:TARGET:22 -N sshtunnel@ssh.qdc.qualcomm.com
    tunnel1_cmd = f'{ssh} -i "{key_path}" -L {port1}:{formatted_target}:22 -N sshtunnel@ssh.qdc.qualcomm.com'

    # Tunnel2: ssh -i KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -L RDPPORT:localhost:3389 -p PORT1 hcktest@localhost
    tunnel2_cmd = (
        f'{ssh} -i "{key_path}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null '
        f'-L {rdp_port}:localhost:3389 -p {port1} hcktest@localhost'
    )

    # Build the Windows Terminal command to open a tab for each tunnel.
    # Use wt.exe new-tab and split-pane semantics with cmd /k to keep them open.
    wt_command = [
        wt,
        "--title", "Tunnel1", "cmd", "/k", tunnel1_cmd,
        ";", "new-tab", "--title", "Tunnel2", "cmd", "/k", f'echo RDP forwarded to localhost:{rdp_port} && {tunnel2_cmd}'
    ]

    print(f"Using SSH port forward: {port1}")
    print(f"Using RDP port forward: {rdp_port}")
    print("Launching Windows Terminal with tunnels...")

    # Launch wt -- this returns immediately
    subprocess.Popen(wt_command, shell=False)

    # give small delay so ssh tunnels can start
    time.sleep(4)

    if open_rdp:
        mstsc = shutil.which("mstsc")
        if not mstsc:
            print("mstsc not found in PATH — skipping auto-open of Remote Desktop.")
            return
        print(f"Opening Remote Desktop to localhost:{rdp_port} ...")
        subprocess.Popen([mstsc, f"/v:localhost:{rdp_port}"])

def generate_bat(target, out="tunnel_generated.bat"):
    """
    Write a .bat file similar to the original one, substituting the target.
    """
    template = utils.load_template("tunnel.bat")
    content = template.replace("%TARGET_PLACEHOLDER%", target)
    with open(out, "w", newline="\r\n") as f:
        f.write(content)

def disconnect(name_contains=None):
    if sys.platform != "win32":
        raise RuntimeError("disconnect() currently supports Windows only.")

    import psutil  # optional dependency — if not present we try using taskkill

    if name_contains:
        substr = name_contains.lower()
    else:
        substr = "ssh"

    killed = 0
    try:
        for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                name = (p.info["name"] or "").lower()
                cmdline = " ".join(p.info.get("cmdline") or [])
                if substr in name or substr in cmdline.lower():
                    pid = p.info["pid"]
                    print(f"Terminating pid {pid} ({name}) ...")
                    p.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        # fallback: use taskkill search
        print("psutil not available or failed; using taskkill fallback.")
        subprocess.run(["taskkill", "/f", "/im", "ssh.exe"], shell=False)

    print(f"Attempted to stop {killed} process(es).")
