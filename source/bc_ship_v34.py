"""V34: GOD / CATFOOD(+value) / XP(+value) / ENERGY PIN / CATS UNLOCK+MAX /
SKILLS MAX. No speed. ASCII-only UI. Bunny logo bundled in app + fallback."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\abrow\Desktop\IosGameOwn\tools")
from bc_direct import ssh, sh

REMOTE = "/var/tmp/bcv34"
SHIP4 = "/var/mobile/Media/Downloads/BattleCatsBuns-ship4.ipa"
VREL = "Frameworks/RecaptchaInterop.framework/RecaptchaInterop"
INAME = "@rpath/RecaptchaInterop.framework/RecaptchaInterop"
ENTS = "<?xml version=\"1.0\"?><plist version=\"1.0\"><dict><key>platform-application</key><true/><key>get-task-allow</key><true/></dict></plist>"
OUT = "/var/mobile/Downloads/INSTALL-ME-BC-v34-fullport.ipa"
SRC = r"C:\Users\abrow\Desktop\IosGameOwn\BunsTS\src\Tweak.m"
BUNNY = r"C:\Users\abrow\Desktop\IosGameOwn\BunsGod\assets\bunny.png"

STUB = """#import <Foundation/Foundation.h>
@interface PodsDummy_RecaptchaInterop : NSObject
@end
@implementation PodsDummy_RecaptchaInterop
@end
"""

data = open(SRC, encoding="utf-8", errors="replace").read().replace("\r\n", "\n")

start = data.index("    /* CATFOOD row */")
end = data.index("    UIPanGestureRecognizer *pan")
rows = """    /* GOD row */
    UILabel *gt = [[UILabel alloc] initWithFrame:CGRectMake(14, 38, 100, 20)];
    gt.text = @"GOD MODE"; gt.textColor = UIColor.whiteColor;
    gt.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:gt];
    ts_godBtn = [self rowBtn:w-116 y:34 w:76 title:ts_god ? @"ON" : @"OFF" color:ts_god ? tsG() : tsR()];
    [ts_godBtn addTarget:self action:@selector(doGod) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ts_godBtn];

    /* CATFOOD row with live value */
    UILabel *cfl = [[UILabel alloc] initWithFrame:CGRectMake(14, 74, 90, 20)];
    cfl.text = @"CATFOOD"; cfl.textColor = UIColor.whiteColor;
    cfl.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:cfl];
    ts_cfVal = [[UILabel alloc] initWithFrame:CGRectMake(104, 76, 76, 16)];
    ts_cfVal.textColor = tsG(); ts_cfVal.font = [UIFont systemFontOfSize:11];
    ts_cfVal.textAlignment = NSTextAlignmentRight;
    [panel addSubview:ts_cfVal];
    UIButton *cfb = [self rowBtn:w-116 y:70 w:76 title:@"MAX" color:UIColor.whiteColor];
    cfb.backgroundColor = tsP();
    [cfb addTarget:self action:@selector(doFood) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:cfb];

    /* XP row with live value */
    UILabel *xpl = [[UILabel alloc] initWithFrame:CGRectMake(14, 110, 90, 20)];
    xpl.text = @"XP"; xpl.textColor = UIColor.whiteColor;
    xpl.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:xpl];
    ts_xpVal = [[UILabel alloc] initWithFrame:CGRectMake(104, 112, 76, 16)];
    ts_xpVal.textColor = tsG(); ts_xpVal.font = [UIFont systemFontOfSize:11];
    ts_xpVal.textAlignment = NSTextAlignmentRight;
    [panel addSubview:ts_xpVal];
    UIButton *xpb = [self rowBtn:w-116 y:106 w:76 title:@"MAX" color:UIColor.whiteColor];
    xpb.backgroundColor = tsP();
    [xpb addTarget:self action:@selector(doXP) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:xpb];

    /* ENERGY PIN row */
    UILabel *et = [[UILabel alloc] initWithFrame:CGRectMake(14, 146, 140, 20)];
    et.text = @"ENERGY PIN"; et.textColor = UIColor.whiteColor;
    et.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:et];
    ts_enBtn = [self rowBtn:w-116 y:142 w:76 title:ts_energy_pin ? @"ON" : @"OFF" color:ts_energy_pin ? tsG() : tsR()];
    [ts_enBtn addTarget:self action:@selector(doEnergy) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ts_enBtn];

    /* CATS row */
    UILabel *ct = [[UILabel alloc] initWithFrame:CGRectMake(14, 182, 80, 20)];
    ct.text = @"CATS"; ct.textColor = UIColor.whiteColor;
    ct.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:ct];
    UIButton *ub = [self rowBtn:w-208 y:178 w:94 title:@"UNLOCK ALL" color:UIColor.whiteColor];
    ub.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    ub.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightBold];
    [ub addTarget:self action:@selector(doUnlock) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ub];
    UIButton *mb = [self rowBtn:w-106 y:178 w:92 title:@"MAX LEVELS" color:UIColor.whiteColor];
    mb.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    mb.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightBold];
    [mb addTarget:self action:@selector(doMaxLv) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:mb];

    /* SKILLS row */
    UILabel *skt = [[UILabel alloc] initWithFrame:CGRectMake(14, 218, 90, 20)];
    skt.text = @"SKILLS"; skt.textColor = UIColor.whiteColor;
    skt.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:skt];
    UIButton *skb = [self rowBtn:w-208 y:214 w:194 title:@"MAX SKILLS" color:UIColor.whiteColor];
    skb.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    skb.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightBold];
    [skb addTarget:self action:@selector(doSkills) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:skb];

"""
data = data[:start] + rows + data[end:]
data = data.replace("CGFloat w = 300, h = 300;", "CGFloat w = 300, h = 252;")
data = data.replace('title.text = @"Buns Menu";', 'title.text = @"BC UJ v34";')

# popups stay suppressed for now
old_pop = "static dispatch_once_t popOnce;\n        dispatch_once(&popOnce, ^{ [TSMenu showSubscribeOverlay]; });"
assert old_pop in data
data = data.replace(old_pop, "/* subscribe overlay suppressed */")
old_gate = "else if (cur && !ts_seen_gate && !celebrated) {"
assert old_gate in data
data = data.replace(old_gate, "else if (0 && cur && !ts_seen_gate && !celebrated) { /* popup suppressed */")

# FAB logo: Documents/bunny.png, then bundled copy, then ASCII caption
old_bun = ('UIImage *bun = [UIImage imageWithContentsOfFile:'
           '[docs stringByAppendingPathComponent:@"bunny.png"]];')
assert old_bun in data
data = data.replace(old_bun, old_bun +
        '\n            if (!bun) bun = [UIImage imageWithContentsOfFile:'
        '[[NSBundle mainBundle] pathForResource:@"bunny" ofType:@"png"]];')
data = data.replace('[ts_fab setTitle:@"" forState:UIControlStateNormal];',
                    '[ts_fab setTitle:@"BC" forState:UIControlStateNormal];', 1)

# pure ASCII enforcement
for k, v in {"♥": "", "✕": "X", "🐰": "", "🔋": "", "🐱": "", "✦": "*", "🎉": "*",
             "·": "-", "◀": "<", "▶": ">", "⏪": "<<", "⏩": ">>",
             "‘": "'", "’": "'", "“": '"', "”": '"'}.items():
    data = data.replace(k, v)
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
d["CFBundleDisplayName"] = "BC UJ v34"
d["CFBundleName"] = "BCUJ34"
plistlib.dump(d, open(p, "wb"))
print("branded BC-UJ-v34")
PY
clang -arch arm64 -dynamiclib -O2 -isysroot "$SDK" \\
  -framework Foundation -framework UIKit -fobjc-arc \\
  -install_name '{INAME}' \\
  -o impostor.dylib BunsTS34.m stub.m 2>&1 | grep -E ' error ' | head -10 || true
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
cd work
rm -f {OUT}
zip -qr {OUT} Payload
chown mobile:mobile {OUT}
cd "$R"
rm -rf verify && mkdir verify && cd verify
unzip -q -o {OUT} 'Payload/battlecatsen.app/Frameworks/RecaptchaInterop.framework/*' 'Payload/battlecatsen.app/bunny.png'
F=$(find . -name RecaptchaInterop | head -1)
strings "$F" | grep -aq 'MAX SKILLS' && echo IPA_VERIFIED_V34 || {{ echo IPA_VERIFY_FAIL; exit 1 }}
[ -f Payload/battlecatsen.app/bunny.png ] && echo BUNNY_IN_IPA || {{ echo NO_BUNNY; exit 1 }}
ls -lah {OUT}
echo V34_SHIP_DONE
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
with sftp.open(f"{REMOTE}/BunsTS34.m", "w") as fh:
    fh.write(data)
with sftp.open(f"{REMOTE}/stub.m", "w") as fh:
    fh.write(STUB)
sftp.put(BUNNY, f"{REMOTE}/bunny.png")
with open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship34.sh", "w", newline="\n") as f:
    f.write(SH.replace("\r\n", "\n"))
sh2 = open(r"C:\Users\abrow\Desktop\IosGameOwn\gd_dump\ship34.sh", encoding="utf-8").read().replace("\r\n", "\n")
with sftp.open(f"{REMOTE}/ship.sh", "w") as fh:
    fh.write(sh2 + CHOICY.replace("\r\n", "\n"))
sftp.close()

i, o, e = c.exec_command(f"zsh {REMOTE}/ship.sh 2>&1", timeout=600)
out = o.read().decode(errors="replace")
print(out[-1500:])
c.close()
print("V34 READY" if "V34_SHIP_DONE" in out else "FAILED")
