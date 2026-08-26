"""DIRECT SSH toolkit + POPUP DIFF - bypasses broken wrapper entirely."""
import sys, io, os
# NOTE: library modules must NEVER touch sys.stdout (double-wrap GC closes buffers)
import paramiko

HOST, USER, PW = "192.168.1.241", "root", "subscribe"

def ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, 22, USER, PW, timeout=12, allow_agent=False, look_for_keys=False)
    return c

def sh(c, cmd, t=30):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    return out + (("\n[err] " + err[:200]) if err.strip() else "")

def pull(c, remote, local):
    sftp = c.open_sftp()
    sftp.get(remote, local)
    sftp.close()

if __name__ == "__main__":
    L = r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump"
    c = ssh()
    print("connected:", sh(c, "echo DIRECT_OK; ls /var/mobile/Containers/Data/Application/5CDF08B0-815B-4890-81F4-F099D14A54B9/Documents/SAVE_DATA")[:120])
    pull(c, "/var/mobile/Containers/Data/Application/5CDF08B0-815B-4890-81F4-F099D14A54B9/Documents/SAVE_DATA",
         os.path.join(L, "SAVE_DATA"))
    c.close()
    cur = open(os.path.join(L, "SAVE_DATA"), "rb").read()
    gold = open(os.path.join(L, "SAVE_DATA.popup_state1"), "rb").read()
    n = min(len(cur), len(gold))
    diffs = [i for i in range(n) if cur[i] != gold[i]]
    clusters = []
    for d in diffs:
        if clusters and d - clusters[-1][1] <= 16:
            clusters[-1][1] = d
        else:
            clusters.append([d, d])
    print(f"cur={len(cur)}B gold={len(gold)}B · diffbytes={len(diffs)} · clusters={len(clusters)}")
    for a, b in clusters[:40]:
        print(f"  @0x{a:06x}-0x{b:06x} ({b-a+1}B)")
    open(os.path.join(L, "SAVE_DATA.popup_state2"), "wb").write(bytes(cur))
    print("*** SNAPSHOT1 saved (DIRECT path) ***")
