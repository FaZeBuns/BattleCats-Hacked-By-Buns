"""V38 = v37 (SPEED row restored) + UI polish:
1. Close X top-right: big red circle, white bold X (was a non-ASCII "✕"
   that the old-clang ASCII strip turned invisible -- empty button).
2. FAB logo button now TOGGLES the menu (tap = show if hidden, hide if
   shown) instead of always showing.
Additive UI only -- no hooking changes. Everything else identical to v37.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\abrow\Desktop\IosGameOwn\tools")
from bc_direct import ssh, sh

REMOTE = "/var/tmp/bcv38"
SHIP4 = "/var/mobile/Media/Downloads/BattleCatsBuns-ship4.ipa"
VREL = "Frameworks/RecaptchaInterop.framework/RecaptchaInterop"
INAME = "@rpath/RecaptchaInterop.framework/RecaptchaInterop"
ENTS = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict><key>platform-application</key><true/><key>get-task-allow</key><true/></dict></plist>"
OUT = "/var/mobile/Downloads/INSTALL-ME-BC-v38-menu.ipa"
SRC = r"C:\Users\abrow\Desktop\IosGameOwn\BunsTS\src\Tweak.m"
BUNNY = r"C:\Users\abrow\Desktop\IosGameOwn\BunsGod\assets\bunny.png"

STUB = """#import <Foundation/Foundation.h>
@interface PodsDummy_RecaptchaInterop : NSObject
@end
@implementation PodsDummy_RecaptchaInterop
@end
"""

# ---- reuse v37's transform chain (v34 -> v35 -> v36 -> v37), same as shipped v37 ----
v37_src = open(r"C:\Users\abrow\Desktop\IosGameOwn\tools\bc_ship_v37.py", encoding="utf-8").read()
ns = {}
head = v37_src.rsplit('SH = f"""', 1)[0]   # last occurrence = the real shell block
head = "\n".join(l for l in head.splitlines() if not l.startswith("sys.stdout ="))
exec(head, ns)
data = ns["data"]  # fully transformed v37 source

# ================= V38 DELTAS (additive UI only) =================
import re as _re

# 1) Close button -> big visible red circle with white bold X
close_pat = _re.compile(r'UIButton \*close = \[UIButton buttonWithType:UIButtonTypeSystem\];.*?\[panel addSubview:close\];', _re.S)
assert close_pat.search(data), "close block not found"
new_close = """UIButton *close = [UIButton buttonWithType:UIButtonTypeCustom];
    close.frame = CGRectMake(w - 34, 6, 28, 28);
    close.backgroundColor = [UIColor colorWithRed:0.85 green:0.18 blue:0.2 alpha:0.95];
    close.layer.cornerRadius = 14;
    close.layer.borderWidth = 1;
    close.layer.borderColor = [UIColor whiteColor].CGColor;
    [close setTitle:@"X" forState:UIControlStateNormal];
    [close setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    close.titleLabel.font = [UIFont systemFontOfSize:15 weight:UIFontWeightBold];
    [close addTarget:self action:@selector(hide) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:close];"""
data = close_pat.sub(new_close, data, count=1)

# 2) FAB tap = toggle panel show/hide
old_fab_target = "[ts_fab addTarget:[TSMenu class] action:@selector(showPanel) forControlEvents:UIControlEventTouchUpInside];"
assert old_fab_target in data
data = data.replace(old_fab_target,
                    "[ts_fab addTarget:[TSMenu class] action:@selector(togglePanel) forControlEvents:UIControlEventTouchUpInside];")

toggle_method = """+ (void)togglePanel {
    UIWindow *win = [UIApplication sharedApplication].keyWindow;
    if (!win) return;
    UIView *panel = [win viewWithTag:9100];
    if (panel) { [panel removeFromSuperview]; return; }
    [self showPanel];
}
"""
assert "+ (void)showPanel {" in data
data = data.replace("+ (void)showPanel {", toggle_method + "+ (void)showPanel {", 1)

# final ASCII hard pass (safety)
data = "".join(ch if ord(ch) < 128 else "" for ch in data)
assert "togglePanel" in data and 'setTitle:@"X"' in data
assert "SPEED set %d" in data and "5 CATS UNLOCKED" in data

SH = f"""#!/bin/zsh
export PATH=/var/jb/usr/bin:/var/jb/bin:/usr/bin:/bin:$PATH
R={REMOTE}
SDK=/var/jb/usr/share/SDKs/iPhoneOS.sdk
set -e
cd "$R"
rm -rf work
mkdir -p work
unzip -q -o "{SHIP4}" -d work
APP=work/Payload/battlecatsen.app
python3 - "$APP" <<'PY'
import plistlib, sys
p = sys.argv[1] + "/Info.plist"
d = plistlib.load(open(p, "rb"))
d["CFBundleIdentifier"] = "com.buns.bc.hacked"
d["CFBundleDisplayName"] = "BC UJ v38"
d["CFBundleName"] = "BCUJ38"
plistlib.dump(d, open(p, "wb"))
print("branded BC-UJ-v38")
PY
clang -arch arm64 -dynamiclib -O2 -isysroot "$SDK" \\
  -framework Foundation -framework UIKit -fobjc-arc \\
  -install_name '{INAME}' \\
  -o impostor.dylib BunsTS38.m stub.m 2>&1 | grep -E ' error ' | head -10 || true
[ -f impostor.dylib ] || {{ echo COMPILE_FAIL; exit 1; }}
echo "COMPILE_OK $(wc -c < impostor.dylib)"
printf '%s' '{ENTS}' > e.plist
ldid -Se.plist impostor.dylib && echo DYLIB_SIGNED
cp -f impostor.dylib "$APP/{VREL}"
cp -f bunny.png "$APP/bunny.png"
strings "$APP/{VREL}" | grep -aq 'HACKED BY BUNS' && echo HAS_OVERLAY || exit 1
strings "$APP/{VREL}" | grep -aq '5 CATS UNLOCKED' && echo HAS_CELEBRATE || exit 1
strings "$APP/{VREL}" | grep -aq 'WARNING - READ FIRST' && echo HAS_WARNING || exit 1
strings "$APP/{VREL}" | grep -aq 'Buns Menu' && echo HAS_TITLE || exit 1
strings "$APP/{VREL}" | grep -aq 'SPEED set %d' && echo HAS_SPEED || exit 1
strings "$APP/{VREL}" | grep -aq 'togglePanel' && echo HAS_TOGGLE || exit 1
cd work
rm -f {OUT}
zip -qr {OUT} Payload
chown mobile:mobile {OUT}
cd "$R"
rm -rf verify && mkdir verify && cd verify
unzip -q -o {OUT} 'Payload/battlecatsen.app/Frameworks/RecaptchaInterop.framework/*' 'Payload/battlecatsen.app/bunny.png'
F=$(find . -name RecaptchaInterop | head -1)
strings "$F" | grep -aq 'togglePanel' && echo IPA_VERIFIED_V38 || {{ echo IPA_VERIFY_FAIL; exit 1 }}
ls -lah {OUT}
echo V38_SHIP_DONE
"""

CHOICY = """
python3 - <<'PY'
import plistlib
p='/var/mobile/Library/Preferences/com.opa334.choicyprefs.plist'
try: d=plistlib.load(open(p,'rb'))
except Exception: d={}
s=d.setdefault('appSettings',{}).setdefault('com.buns.bc.hacked',{})
s['tweakInjectionDisabled']=True
s['overwriteGlobalTweakConfiguration']=True
plistlib.dump(d,open(p,'wb'))
print('choicy updated')
PY
killall -9 cfprefsd 2>/dev/null || true
"""

c = ssh()
sh(c, f"rm -rf {REMOTE} && mkdir -p {REMOTE} && echo DIR", t=15)
sftp = c.open_sftp()
with sftp.open(f"{REMOTE}/BunsTS38.m", "w") as fh:
    fh.write(data)
with sftp.open(f"{REMOTE}/stub.m", "w") as fh:
    fh.write(STUB)
sftp.put(BUNNY, f"{REMOTE}/bunny.png")
with open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship38.sh", "w", newline="\n") as f:
    f.write(SH.replace("\r\n", "\n"))
sh2 = open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship38.sh", encoding="utf-8").read().replace("\r\n", "\n")
with sftp.open(f"{REMOTE}/ship.sh", "w") as fh:
    fh.write(sh2 + CHOICY.replace("\r\n", "\n"))
sftp.close()

i, o, e = c.exec_command(f"zsh {REMOTE}/ship.sh 2>&1", timeout=600)
out = o.read().decode(errors="replace")
import os as _os
_os.write(1, (out[-1400:] + "\n").encode())
c.close()
_os.write(1, (b"V38 READY\n" if "V38_SHIP_DONE" in out else b"FAILED\n"))
