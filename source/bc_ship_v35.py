"""V35 = v34 + ENERGY live value label + title 'Buns Menu'. No speed."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\abrow\Desktop\IosGameOwn\tools")
from bc_direct import ssh, sh

# ---- load v34 script source and exec its transform section verbatim ----
v34_src = open(r"C:\Users\abrow\Desktop\IosGameOwn\tools\bc_ship_v34.py", encoding="utf-8").read()
ns = {}
head = v34_src.split('SH = f"""')[0]
head = head.replace('bc_ship_v34', 'THIS')
exec(head, ns)
SHIP4 = "/var/mobile/Media/Downloads/BattleCatsBuns-ship4.ipa"
VREL = "Frameworks/RecaptchaInterop.framework/RecaptchaInterop"
INAME = "@rpath/RecaptchaInterop.framework/RecaptchaInterop"
ENTS = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict><key>platform-application</key><true/><key>get-task-allow</key><true/></dict></plist>"
OUT = "/var/mobile/Downloads/INSTALL-ME-BC-v35-buns-menu.ipa"
SRC = r"C:\Users\abrow\Desktop\IosGameOwn\BunsTS\src\Tweak.m"
BUNNY = r"C:\Users\abrow\Desktop\IosGameOwn\BunsGod\assets\bunny.png"

STUB = """#import <Foundation/Foundation.h>
@interface PodsDummy_RecaptchaInterop : NSObject
@end
@implementation PodsDummy_RecaptchaInterop
@end
"""

# ---- load v34 script source and exec its transform section verbatim ----
v34_src = open(r"C:\Users\abrow\Desktop\IosGameOwn\tools\bc_ship_v34.py", encoding="utf-8").read()
ns = {}
head = v34_src.split('SH = f"""')[0]
head = head.replace('bc_ship_v34', 'THIS')
head = "\n".join(l for l in head.splitlines() if "sys.stdout = io.TextIOWrapper" not in l)
exec(head, ns)
data = ns["data"]  # fully transformed v34 source (ascii, rows, popups off)

REMOTE = "/var/tmp/bcv35"

# ---- v35 deltas ----
assert "static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;" in data
data = data.replace("static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;",
                    "static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;\nstatic UILabel *ts_enVal;")
old_en_row = """    ts_enBtn = [self rowBtn:w-116 y:142 w:76 title:ts_energy_pin ? @"ON" : @"OFF" color:ts_energy_pin ? tsG() : tsR()];"""
new_en_row = """    ts_enVal = [[UILabel alloc] initWithFrame:CGRectMake(104, 148, 76, 16)];
    ts_enVal.textColor = tsG(); ts_enVal.font = [UIFont systemFontOfSize:11];
    ts_enVal.textAlignment = NSTextAlignmentRight;
    [panel addSubview:ts_enVal];
    ts_enBtn = [self rowBtn:w-116 y:142 w:76 title:ts_energy_pin ? @"ON" : @"OFF" color:ts_energy_pin ? tsG() : tsR()];"""
assert old_en_row in data
data = data.replace(old_en_row, new_en_row)
old_refresh = "    ts_xpVal.text = [NSString stringWithFormat:@\"%u\", ts_dec((const uint8_t *)ts_ud() + 0xbde0)];"
new_refresh = old_refresh + ("\n    ts_enVal.text = [NSString stringWithFormat:@\"%u\", "
                             "ts_dec((const uint8_t *)ts_ud() + 0xbd68)];")
assert old_refresh in data
data = data.replace(old_refresh, new_refresh)
data = data.replace('title.text = @"BC UJ v34";', 'title.text = @"Buns Menu";')
data = "".join(ch if ord(ch) < 128 else "" for ch in data)

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
d["CFBundleDisplayName"] = "BC UJ v35"
d["CFBundleName"] = "BCUJ35"
plistlib.dump(d, open(p, "wb"))
print("branded BC-UJ-v35")
PY
clang -arch arm64 -dynamiclib -O2 -isysroot "$SDK" \\
  -framework Foundation -framework UIKit -fobjc-arc \\
  -install_name '{INAME}' \\
  -o impostor.dylib BunsTS35.m stub.m 2>&1 | grep -E ' error ' | head -10 || true
[ -f impostor.dylib ] || {{ echo COMPILE_FAIL; exit 1; }}
echo "COMPILE_OK $(wc -c < impostor.dylib)"
printf '%s' '{ENTS}' > e.plist
ldid -Se.plist impostor.dylib && echo DYLIB_SIGNED
cp -f impostor.dylib "$APP/{VREL}"
cp -f bunny.png "$APP/bunny.png"
strings "$APP/{VREL}" | grep -aq 'GOD MODE' && echo HAS_GOD || exit 1
strings "$APP/{VREL}" | grep -aq 'UNLOCK ALL' && echo HAS_CATS || exit 1
strings "$APP/{VREL}" | grep -aq 'MAX SKILLS' && echo HAS_SKILLS || exit 1
strings "$APP/{VREL}" | grep -aq 'ENERGY PIN' && echo HAS_ENERGY || exit 1
strings "$APP/{VREL}" | grep -aq 'Buns Menu' && echo HAS_TITLE || exit 1
cd work
rm -f {OUT}
zip -qr {OUT} Payload
chown mobile:mobile {OUT}
cd "$R"
rm -rf verify && mkdir verify && cd verify
unzip -q -o {OUT} 'Payload/battlecatsen.app/Frameworks/RecaptchaInterop.framework/*' 'Payload/battlecatsen.app/bunny.png'
F=$(find . -name RecaptchaInterop | head -1)
strings "$F" | grep -aq 'Buns Menu' && echo IPA_VERIFIED_V35 || {{ echo IPA_VERIFY_FAIL; exit 1 }}
ls -lah {OUT}
echo V35_SHIP_DONE
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
with sftp.open(f"{REMOTE}/BunsTS35.m", "w") as fh:
    fh.write(data)
with sftp.open(f"{REMOTE}/stub.m", "w") as fh:
    fh.write(STUB)
sftp.put(BUNNY, f"{REMOTE}/bunny.png")
with open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship35.sh", "w", newline="\n") as f:
    f.write(SH.replace("\r\n", "\n"))
sh2 = open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship35.sh", encoding="utf-8").read().replace("\r\n", "\n")
with sftp.open(f"{REMOTE}/ship.sh", "w") as fh:
    fh.write(sh2 + CHOICY.replace("\r\n", "\n"))
sftp.close()

i, o, e = c.exec_command(f"zsh {REMOTE}/ship.sh 2>&1", timeout=600)
out = o.read().decode(errors="replace")
print(out[-1400:])
c.close()
print("V35 READY" if "V35_SHIP_DONE" in out else "FAILED")
