"""V36 = v35 (energy value, Buns Menu title) + popups RESTORED pure-ASCII.
Self-contained: builds on v34 transforms only (no nested exec)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\abrow\Desktop\IosGameOwn\tools")
from bc_direct import ssh, sh

REMOTE = "/var/tmp/bcv36"
SHIP4 = "/var/mobile/Media/Downloads/BattleCatsBuns-ship4.ipa"
VREL = "Frameworks/RecaptchaInterop.framework/RecaptchaInterop"
INAME = "@rpath/RecaptchaInterop.framework/RecaptchaInterop"
ENTS = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict><key>platform-application</key><true/><key>get-task-allow</key><true/></dict></plist>"
OUT = "/var/mobile/Downloads/INSTALL-ME-BC-v36-popups.ipa"
SRC = r"C:\Users\abrow\Desktop\IosGameOwn\BunsTS\src\Tweak.m"
BUNNY = r"C:\Users\abrow\Desktop\IosGameOwn\BunsGod\assets\bunny.png"

STUB = """#import <Foundation/Foundation.h>
@interface PodsDummy_RecaptchaInterop : NSObject
@end
@implementation PodsDummy_RecaptchaInterop
@end
"""

# ---- v34 transform section, executed for its `data` ----
v34_src = open(r"C:\Users\abrow\Desktop\IosGameOwn\tools\bc_ship_v34.py", encoding="utf-8").read()
ns = {}
head = v34_src.split('SH = f"""')[0]
head = "\n".join(l for l in head.splitlines()
                 if "sys.stdout = io.TextIOWrapper" not in l)
head = head.split("# pure ASCII enforcement")[0]  # keep unicode intact; we strip at the end
exec(head, ns)
data = ns["data"]

# ---- v35 deltas: energy value label + refresh line ----
data = data.replace("static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;",
                    "static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;\nstatic UILabel *ts_enVal;")
old_en_row = "    ts_enBtn = [self rowBtn:w-116 y:142 w:76 title:ts_energy_pin ? @\"ON\" : @\"OFF\" color:ts_energy_pin ? tsG() : tsR()];"
new_en_row = ("    ts_enVal = [[UILabel alloc] initWithFrame:CGRectMake(104, 148, 76, 16)];\n"
              "    ts_enVal.textColor = tsG(); ts_enVal.font = [UIFont systemFontOfSize:11];\n"
              "    ts_enVal.textAlignment = NSTextAlignmentRight;\n"
              "    [panel addSubview:ts_enVal];\n" + old_en_row)
assert old_en_row in data
data = data.replace(old_en_row, new_en_row)
old_refresh = '    ts_xpVal.text = [NSString stringWithFormat:@"%u", ts_dec((const uint8_t *)ts_ud() + 0xbde0)];'
new_refresh = old_refresh + ('\n    ts_enVal.text = [NSString stringWithFormat:@"%u", '
                             'ts_dec((const uint8_t *)ts_ud() + 0xbd68)];')
assert old_refresh in data
data = data.replace(old_refresh, new_refresh)

# ---- v36 deltas: restore popups with ASCII text ----
old_pop = "/* subscribe overlay suppressed */"
assert old_pop in data
data = data.replace(old_pop,
    "static dispatch_once_t popOnce;\n        dispatch_once(&popOnce, ^{ [TSMenu showSubscribeOverlay]; });")

old_gate = "else if (0 && cur && !ts_seen_gate && !celebrated) { /* popup suppressed */"
assert old_gate in data
data = data.replace(old_gate, "else if (cur && !ts_seen_gate && !celebrated) {")

# subscribe overlay msg / buttons ASCII (regex — glyph-agnostic)
import re as _re
data = _re.sub(r'msg\.text = @"SUBSCRIBE for more hacked games!\\n[^"]*";',
               'msg.text = @"SUBSCRIBE for more hacked games!\\\\n'
               'youtube.com/@BunsDeveloper\\\\nGOD - SPEED - ENERGY - CATS";',
               data, count=1)
data = _re.sub(r'\[sub setTitle:@"[^"]*SUBSCRIBE"',
               '[sub setTitle:@">> SUBSCRIBE"', data, count=1)
data = _re.sub(r'bunny\.text = @"[^"]*";', 'bunny.text = @":B";', data, count=1)

# red warning ASCII
old_warn_title = 'ts_alert(@"\u26a0\ufe0f WARNING \u2014 READ FIRST!"'
assert old_warn_title in data
data = data.replace(old_warn_title, 'ts_alert(@"WARNING - READ FIRST!"')
i2 = data.find(', @"PLAY NORMALLY UNTIL YOU HAVE 5 CATS!')
assert i2 != -1
j2 = data.index('"', i2 + 5) + 1
data = data[:i2] + (', @"PLAY NORMALLY UNTIL YOU HAVE 5 CATS!\\n\\nThe EQUIP / Organizer button unlocks at 5 cats.\\n'
                    'UNLOCK ALL is BLOCKED until then - this prevents soft-locking your account.\\n\\n'
                    'After 5 cats: unlock everything & go crazy!"') + data[j2:]

# celebration alert ASCII (slice keeps surrounding @"/" quotes intact)
i3 = data.find('alertControllerWithTitle:@"')
assert i3 != -1
k3 = i3 + len('alertControllerWithTitle:@"')
e3 = data.index('"', k3)          # closing quote of title
m3 = data.find('message:@"', e3)
k4 = m3 + len('message:@"')
e4 = data.index('"', k4)          # closing quote of message
data = (data[:k3] + "*** 5 CATS UNLOCKED! ***" + data[e3:k4] +
        "The EQUIP button is now available!\\n\\nOpen the Buns Menu and hit UNLOCK ALL -\\n"
        "every cat in the game is yours, instantly.\\n\\nThen MAX LEVELS + MAX SKILLS!" + data[e4:])

# overlay bunny logo bundle fallback
old_logo = ('UIImage *logo = [UIImage imageWithContentsOfFile:'
            '[docs stringByAppendingPathComponent:@"bunny.png"]];')
assert old_logo in data
data = data.replace(old_logo, old_logo +
    '\n        if (!logo) logo = [UIImage imageWithContentsOfFile:'
    '[[NSBundle mainBundle] pathForResource:@"bunny" ofType:@"png"]];')

# title + final ASCII hard pass
data = data.replace('title.text = @"BC UJ v34";', 'title.text = @"Buns Menu";')
data = "".join(ch if ord(ch) < 128 else "" for ch in data)
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
d["CFBundleDisplayName"] = "BC UJ v36"
d["CFBundleName"] = "BCUJ36"
plistlib.dump(d, open(p, "wb"))
print("branded BC-UJ-v36")
PY
clang -arch arm64 -dynamiclib -O2 -isysroot "$SDK" \\
  -framework Foundation -framework UIKit -fobjc-arc \\
  -install_name '{INAME}' \\
  -o impostor.dylib BunsTS36.m stub.m 2>&1 | grep -E ' error ' | head -10 || true
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
cd work
rm -f {OUT}
zip -qr {OUT} Payload
chown mobile:mobile {OUT}
cd "$R"
rm -rf verify && mkdir verify && cd verify
unzip -q -o {OUT} 'Payload/battlecatsen.app/Frameworks/RecaptchaInterop.framework/*' 'Payload/battlecatsen.app/bunny.png'
F=$(find . -name RecaptchaInterop | head -1)
strings "$F" | grep -aq '5 CATS UNLOCKED' && echo IPA_VERIFIED_V36 || {{ echo IPA_VERIFY_FAIL; exit 1 }}
ls -lah {OUT}
echo V36_SHIP_DONE
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
with sftp.open(f"{REMOTE}/BunsTS36.m", "w") as fh:
    fh.write(data)
with sftp.open(f"{REMOTE}/stub.m", "w") as fh:
    fh.write(STUB)
sftp.put(BUNNY, f"{REMOTE}/bunny.png")
with open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship36.sh", "w", newline="\n") as f:
    f.write(SH.replace("\r\n", "\n"))
sh2 = open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship36.sh", encoding="utf-8").read().replace("\r\n", "\n")
with sftp.open(f"{REMOTE}/ship.sh", "w") as fh:
    fh.write(sh2 + CHOICY.replace("\r\n", "\n"))
sftp.close()

i, o, e = c.exec_command(f"zsh {REMOTE}/ship.sh 2>&1", timeout=600)
out = o.read().decode(errors="replace")
import os as _os
_os.write(1, (out[-1400:] + "\n").encode())
c.close()
_os.write(1, (b"V36 READY\n" if "V36_SHIP_DONE" in out else b"FAILED\n"))
