"""V37 = v36 (popups, Buns Menu, all rows) + SPEED row RESTORED in the menu.

The vtable speed engine (ts_speed_arm / ts_mu_thunk / BunsTS_SpeedSet) is
ALREADY compiled into every v34+ build and ALREADY ARMS at boot (v36 log:
"SPEED ARMED"). The v34 menu rewrite simply removed the row that lets the
user change N. V37 only adds that row back (label + </> stepper) wired to
the existing methods -- zero hooking changes, N stays 1 until tapped.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\abrow\Desktop\IosGameOwn\tools")
from bc_direct import ssh, sh

REMOTE = "/var/tmp/bcv37"
SHIP4 = "/var/mobile/Media/Downloads/BattleCatsBuns-ship4.ipa"
VREL = "Frameworks/RecaptchaInterop.framework/RecaptchaInterop"
INAME = "@rpath/RecaptchaInterop.framework/RecaptchaInterop"
ENTS = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict><key>platform-application</key><true/><key>get-task-allow</key><true/></dict></plist>"
OUT = "/var/mobile/Downloads/INSTALL-ME-BC-v37-speed.ipa"
SRC = r"C:\Users\abrow\Desktop\IosGameOwn\BunsTS\src\Tweak.m"
BUNNY = r"C:\Users\abrow\Desktop\IosGameOwn\BunsGod\assets\bunny.png"

STUB = """#import <Foundation/Foundation.h>
@interface PodsDummy_RecaptchaInterop : NSObject
@end
@implementation PodsDummy_RecaptchaInterop
@end
"""

# ---- reuse v36's transform chain (v34 -> v35 -> v36), same as shipped v36 ----
v36_src = open(r"C:\Users\abrow\Desktop\IosGameOwn\tools\bc_ship_v36.py", encoding="utf-8").read()
ns = {}
head = v36_src.rsplit('SH = f"""', 1)[0]  # last occurrence = the real shell block
# remove ONLY the sys.stdout assignment line; must NOT match v36's own
# filter line (which contains the substring in a string literal)
head = "\n".join(l for l in head.splitlines() if not l.startswith("sys.stdout ="))
exec(head, ns)  # v36 head includes v34+v35+v36 transforms; defines ns["data"]
data = ns["data"]  # fully transformed v36 source (popups ASCII, Buns Menu title)

# ================= V37 DELTAS (additive UI only) =================
# 1) panel taller to fit the SPEED row
assert "CGFloat w = 300, h = 252;" in data
data = data.replace("CGFloat w = 300, h = 252;", "CGFloat w = 300, h = 288;")

# 2) shift CATS + SKILLS rows down 36px to make room
assert "CGRectMake(14, 182, 80, 20)" in data
data = data.replace("CGRectMake(14, 182, 80, 20)", "CGRectMake(14, 220, 80, 20)")       # CATS label
assert "[self rowBtn:w-208 y:178 w:94 title:@\"UNLOCK ALL\"" in data
data = data.replace("[self rowBtn:w-208 y:178 w:94 title:@\"UNLOCK ALL\"",
                    "[self rowBtn:w-208 y:216 w:94 title:@\"UNLOCK ALL\"")               # CATS unlock btn
assert "[self rowBtn:w-106 y:178 w:92 title:@\"MAX LEVELS\"" in data
data = data.replace("[self rowBtn:w-106 y:178 w:92 title:@\"MAX LEVELS\"",
                    "[self rowBtn:w-106 y:216 w:92 title:@\"MAX LEVELS\"")               # CATS max btn
assert "CGRectMake(14, 218, 90, 20)" in data
data = data.replace("CGRectMake(14, 218, 90, 20)", "CGRectMake(14, 256, 90, 20)")       # SKILLS label
assert "[self rowBtn:w-208 y:214 w:194 title:@\"MAX SKILLS\"" in data
data = data.replace("[self rowBtn:w-208 y:214 w:194 title:@\"MAX SKILLS\"",
                    "[self rowBtn:w-208 y:252 w:194 title:@\"MAX SKILLS\"")              # SKILLS btn

# 3) SPEED row inserted between ENERGY and CATS (same geometry as base
#    Tweak.m speed row, shifted +36; ASCII "<"/">" for old-clang safety)
speed_row = """    /* SPEED row */
    UILabel *st = [[UILabel alloc] initWithFrame:CGRectMake(14, 184, 52, 20)];
    st.text = @"SPEED"; st.textColor = UIColor.whiteColor;
    st.font = [UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
    [panel addSubview:st];
    ts_spdVal = [[UILabel alloc] initWithFrame:CGRectMake(w-152, 182, 58, 30)];
    ts_spdVal.text = [NSString stringWithFormat:@"%dx", ts_spd_n];
    ts_spdVal.textAlignment = NSTextAlignmentCenter;
    ts_spdVal.textColor = ts_spd_n > 1 ? tsG() : tsR();
    ts_spdVal.font = [UIFont systemFontOfSize:18 weight:UIFontWeightBold];
    [panel addSubview:ts_spdVal];
    UIButton *dn = [self rowBtn:w-194 y:186 w:38 title:@"<" color:UIColor.whiteColor];
    dn.backgroundColor = [UIColor colorWithWhite:0.28 alpha:1];
    dn.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightBold];
    dn.layer.cornerRadius = 7;
    [dn addTarget:self action:@selector(spdDown) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:dn];
    UIButton *up = [self rowBtn:w-90 y:186 w:38 title:@">" color:UIColor.whiteColor];
    up.backgroundColor = tsP();
    up.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightBold];
    up.layer.cornerRadius = 7;
    [up addTarget:self action:@selector(spdUp) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:up];

"""
anchor = "    /* CATS row */"
assert anchor in data
data = data.replace(anchor, speed_row + anchor, 1)

# 4) log speed changes so we can verify remotely (bunsts.log)
old_ss = '    ts_spd_n = n;\n    [NSUserDefaults.standardUserDefaults setInteger:n forKey:@"bg_speed_n"];'
assert old_ss in data
data = data.replace(old_ss,
                    '    ts_spd_n = n;\n    tlog("SPEED set %d", n);\n'
                    '    [NSUserDefaults.standardUserDefaults setInteger:n forKey:@"bg_speed_n"];')

# final ASCII hard pass (old on-device clang mangles non-ASCII)
data = "".join(ch if ord(ch) < 128 else "" for ch in data)
assert "SPEED set %d" in data and "    /* SPEED row */" in data
assert "5 CATS UNLOCKED" in data and "WARNING - READ FIRST" in data

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
d["CFBundleDisplayName"] = "BC UJ v37"
d["CFBundleName"] = "BCUJ37"
plistlib.dump(d, open(p, "wb"))
print("branded BC-UJ-v37")
PY
clang -arch arm64 -dynamiclib -O2 -isysroot "$SDK" \\
  -framework Foundation -framework UIKit -fobjc-arc \\
  -install_name '{INAME}' \\
  -o impostor.dylib BunsTS37.m stub.m 2>&1 | grep -E ' error ' | head -10 || true
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
cd work
rm -f {OUT}
zip -qr {OUT} Payload
chown mobile:mobile {OUT}
cd "$R"
rm -rf verify && mkdir verify && cd verify
unzip -q -o {OUT} 'Payload/battlecatsen.app/Frameworks/RecaptchaInterop.framework/*' 'Payload/battlecatsen.app/bunny.png'
F=$(find . -name RecaptchaInterop | head -1)
strings "$F" | grep -aq 'SPEED set %d' && echo IPA_VERIFIED_V37 || {{ echo IPA_VERIFY_FAIL; exit 1 }}
ls -lah {OUT}
echo V37_SHIP_DONE
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
with sftp.open(f"{REMOTE}/BunsTS37.m", "w") as fh:
    fh.write(data)
with sftp.open(f"{REMOTE}/stub.m", "w") as fh:
    fh.write(STUB)
sftp.put(BUNNY, f"{REMOTE}/bunny.png")
with open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship37.sh", "w", newline="\n") as f:
    f.write(SH.replace("\r\n", "\n"))
sh2 = open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship37.sh", encoding="utf-8").read().replace("\r\n", "\n")
with sftp.open(f"{REMOTE}/ship.sh", "w") as fh:
    fh.write(sh2 + CHOICY.replace("\r\n", "\n"))
sftp.close()

i, o, e = c.exec_command(f"zsh {REMOTE}/ship.sh 2>&1", timeout=600)
out = o.read().decode(errors="replace")
import os as _os
_os.write(1, (out[-1400:] + "\n").encode())
c.close()
_os.write(1, (b"V37 READY\n" if "V37_SHIP_DONE" in out else b"FAILED\n"))
