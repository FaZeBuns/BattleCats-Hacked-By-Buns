/*
 * BunsTS v2 - TrollStore app (com.buns.bc.hacked) FULL hack menu.
 * CATFOOD / XP / GOD MODE / SPEED x1-25 (vtable engine) / ENERGY PIN.
 * No cats/upgrades (organizer research). Hard bundle-id guard.
 */
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#import <mach/mach.h>
#import <mach-o/dyld.h>
#import <dlfcn.h>
#import <pthread.h>
#import <stdarg.h>
#import <objc/runtime.h>
#import <objc/message.h>
#import <stdio.h>
#import <string.h>
#import <time.h>

static uintptr_t g_base = 0;
static FILE *g_log = NULL;

static void tlog(const char *fmt, ...) {
    if (!g_log) {
        NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
        if (!docs) return;
        g_log = fopen([docs stringByAppendingPathComponent:@"bunsts.log"].fileSystemRepresentation, "a");
        if (!g_log) return;
    }
    va_list ap; va_start(ap, fmt);
    vfprintf(g_log, fmt, ap); fprintf(g_log, "\n"); fflush(g_log);
    va_end(ap);
}

/* ---- currency codec (BunsGod rules) ---- */
static void ts_write_max(uint8_t *p, uint32_t V) {
    uint8_t key[4];
    for (int i = 0; i < 4; i++) key[i] = p[7 - i];
    for (int i = 0; i < 4; i++) p[i] = ((V >> (8 * i)) & 0xFF) ^ key[i];
}
static uint32_t ts_dec(const uint8_t *p) {
    uint32_t v = 0;
    for (int i = 0; i < 4; i++) v |= ((uint32_t)(p[i] ^ p[7 - i])) << (8 * i);
    return v;
}
extern kern_return_t mach_vm_remap(vm_map_t target_task, mach_vm_address_t *address,
    mach_vm_size_t size, mach_vm_offset_t mask, int flags, vm_map_t src_task,
    mach_vm_address_t memory_address, boolean_t copy, vm_prot_t *cur_protection,
    vm_prot_t *max_protection, vm_inherit_t inheritance);

static inline volatile uint8_t *ts_ud(void) {
    return (g_base ? (volatile uint8_t *)(g_base + 0x19d7878) : NULL);
}
static BOOL ts_ud_ok(void) {
    volatile uint8_t *o = ts_ud();
    if (!o) return NO;
    uint8_t b[8]; vm_size_t got = 0;
    if (vm_read_overwrite(mach_task_self(), (vm_address_t)(o + 0xbc58), 8, (vm_address_t)b, &got) != KERN_SUCCESS || got < 8) return NO;
    return ts_dec(b) <= 999999999u;
}

static const uint32_t TS_CF_MAX = 99999999u;
static const uint32_t TS_XP_MAX = 99999999u;

static int ts_apply(int which) {   /* 0=food 1=xp */
    if (!ts_ud_ok()) return -1;
    volatile uint8_t *o = ts_ud();
    if (which == 0) ts_write_max((uint8_t *)o + 0xbc58, TS_CF_MAX);
    else { ts_write_max((uint8_t *)o + 0xbde0, TS_XP_MAX); ts_write_max((uint8_t *)o + 0xbde8, TS_XP_MAX); }
    tlog("apply %d ok", which);
    return 0;
}

/* ================= ENERGY ================= */
static volatile int ts_energy_pin = 0;
static void ts_energy_once(void) {
    volatile uint8_t *o = ts_ud();
    if (!o) return;
    ts_write_max((uint8_t *)o + 0xbd68, 999u);
    ts_write_max((uint8_t *)o + 0xbda0, 0u);
    ts_write_max((uint8_t *)o + 0xbdb0, (uint32_t)time(NULL));
}
/* rank -> 10000 lifts max-energy so the 999 pin is a legal value
   (fresh accounts have max ~30; without this the game clamps us back) */
static void ts_rank(void) {
    if (!g_base) return;
    typedef void *(*getter_t)(void);
    getter_t getter = (getter_t)(g_base + 0x3e258);
    void *sing = getter();
    if (!sing) return;
    uint8_t chk[4]; vm_size_t osz = 0;
    if (vm_read_overwrite(mach_task_self(), (vm_address_t)sing + 0x2bb0, 4, (vm_address_t)chk, &osz) != KERN_SUCCESS) return;
    *(volatile uint32_t *)((uint8_t *)sing + 0x2bb0) = 10000u;
}
static void ts_rank_records(void) {
    volatile uint8_t *o = ts_ud();
    if (!o) return;
    for (uintptr_t p = 0; p + 8 <= 0x500000; p += 4)
        if (ts_dec((const uint8_t *)o + p) == 200000u) ts_write_max((uint8_t *)o + p, 10000u);
}

/* ================= SPEED (v15 vtable engine) ================= */
static volatile int ts_spd_n = 1;
static void (*ts_orig_mu)(void *) = NULL;
static void ts_mu_thunk(void *self) {
    int n = ts_spd_n;
    for (int i = 1; i < n; i++) ts_orig_mu(self);
    ts_orig_mu(self);
}
static void ts_speed_arm(void) {
    if (!g_base || ts_orig_mu) return;
    uintptr_t *vtbl = (uintptr_t *)(g_base + 0x16952e8);
    uintptr_t want = g_base + 0x1cbe24;
    if (vtbl[6] != want) return;
    ts_orig_mu = (void (*)(void *))want;
    uintptr_t page = (uintptr_t)vtbl & ~0xFFFULL;
    if (vm_protect(mach_task_self(), page, 0x1000, 0, VM_PROT_READ | VM_PROT_WRITE) == KERN_SUCCESS) {
        vtbl[6] = (uintptr_t)ts_mu_thunk;
        vm_protect(mach_task_self(), page, 0x1000, 0, VM_PROT_READ | VM_PROT_EXECUTE);
        tlog("SPEED ARMED");
    } else {
        mach_vm_address_t cp = 0; vm_prot_t cur = 0, mx = 0;
        if (mach_vm_remap(mach_task_self(), &cp, 0x1000, 0, VM_FLAGS_ANYWHERE,
                          mach_task_self(), page, TRUE, &cur, &mx, VM_INHERIT_COPY) == KERN_SUCCESS) {
            vm_protect(mach_task_self(), cp, 0x1000, 0, VM_PROT_READ | VM_PROT_WRITE);
            ((uintptr_t *)cp)[6] = (uintptr_t)ts_mu_thunk;
            mach_vm_address_t dst = page;
            mach_vm_remap(mach_task_self(), &dst, 0x1000, 0,
                          VM_FLAGS_FIXED | VM_FLAGS_OVERWRITE,
                          mach_task_self(), cp, FALSE, &cur, &mx, VM_INHERIT_COPY);
            tlog("SPEED ARMED remap");
        }
    }
}

/* background: arms speed + runs energy keeper */
static CFAbsoluteTime ts_suppress_until = 0;
static BOOL ts_seen_gate = NO;
static void *ts_bg_thr(void *arg) {
    (void)arg;
    int n = 0, logged = 0;
    int prev_gate = -1;
    for (;;) {
        usleep(250000);
        n++;
        /* lift rank from boot so max-energy is huge BEFORE any UI renders */
        if (ts_ud_ok() && (n % 20) == 1) ts_rank();
        if (ts_energy_pin && ts_ud_ok()) {
            ts_energy_once();
            if (!logged) { tlog("keeper pinning energy"); logged = 1; }
        }
        ts_speed_arm();
        /* 5-cat gate rising-edge -> celebration popup (ONCE EVER per install) */
        if (ts_ud_ok() && (n % 4) == 0) {
            int cur = (ts_dec((const uint8_t *)ts_ud() + 0xbe18) == 0x01000000u) ? 1 : 0;
            BOOL celebrated = [NSUserDefaults.standardUserDefaults boolForKey:@"buns_celebrated"];
            if (prev_gate == -1) { prev_gate = cur; ts_seen_gate = cur; }
            else if (cur && !ts_seen_gate && !celebrated) {
                ts_seen_gate = 1;
                [NSUserDefaults.standardUserDefaults setBool:YES forKey:@"buns_celebrated"];
                dispatch_async(dispatch_get_main_queue(), ^{
                    UIViewController *vc = [UIApplication sharedApplication].keyWindow.rootViewController;
                    if (!vc) return;
                    UIAlertController *ac = [UIAlertController alertControllerWithTitle:@"🎉 5 CATS UNLOCKED!"
                        message:@"The EQUIP button is now available!\n\nOpen the 🐾 menu and hit UNLOCK ALL —\nevery cat in the game is yours, instantly.\n\nThen MAX LEVELS + MAX SKILLS 😈"
                        preferredStyle:UIAlertControllerStyleAlert];
                    [ac addAction:[UIAlertAction actionWithTitle:@"LET'S GOOO" style:UIAlertActionStyleDefault handler:nil]];
                    [vc presentViewController:ac animated:YES completion:nil];
                });
                tlog("gate celebration fired");
            }
        }
    }
    return NULL;
}

/* ================= GOD (ported from NekoGod proven scanner) ================= */
static volatile BOOL ts_god = NO;
static volatile int32_t ts_exact = 0;
static uintptr_t ts_fx[64]; static int32_t ts_fv[64]; static volatile int ts_fn = 0;
static pthread_mutex_t ts_mtx = PTHREAD_MUTEX_INITIALIZER;

static void ts_scan_once(void) {
    static uint8_t *buf = NULL;
    if (!buf) buf = (uint8_t *)malloc(4 * 1024 * 1024);
    if (!buf) return;
    int n = 0;
    uintptr_t addrs[64];
    int32_t target = ts_exact;
    if (!target) target = 2988000;
    if (target) {
        for (uintptr_t base = 0x100000000ULL; base < 0x180000000ULL && n < 64; base += (4*1024*1024)) {
            vm_size_t out = 0;
            if (vm_read_overwrite(mach_task_self(), (vm_address_t)base, 4*1024*1024,
                                  (vm_address_t)(uintptr_t)buf, &out) != KERN_SUCCESS || out < 8)
                continue;
            int32_t *p = (int32_t *)buf;
            size_t cnt = out / 4;
            for (size_t i = 0; i + 1 < cnt && n < 64; i++)
                if (p[i] == target && p[i+1] > 0 && p[i+1] <= target)
                    addrs[n++] = base + (vm_address_t)((i+1)*4);
            if (n) break;
        }
        pthread_mutex_lock(&ts_mtx);
        ts_fn = 0;
        for (int j = 0; j < n && j < 64; j++) { ts_fx[j] = addrs[j]; ts_fv[j] = target; ts_fn++; }
        pthread_mutex_unlock(&ts_mtx);
        if (n) { tlog("god exact lock max=%d copies=%d", target, n); return; }
    }
    /* AUTO: full-HP snapshot -> damage diff -> mirror vote */
    #define AMAX 131072
    static uintptr_t *a1 = NULL; static int32_t *m1 = NULL, *c1 = NULL;
    if (!a1) { a1 = malloc(AMAX*sizeof(*a1)); m1 = malloc(AMAX*sizeof(*m1)); c1 = malloc(AMAX*sizeof(*c1)); }
    if (!a1) return;
    int n1 = 0;
    for (uintptr_t base = 0x100000000ULL; base < 0x180000000ULL && n1 < AMAX; base += (4*1024*1024)) {
        vm_size_t out = 0;
        if (vm_read_overwrite(mach_task_self(), (vm_address_t)base, 4*1024*1024,
                              (vm_address_t)(uintptr_t)buf, &out) != KERN_SUCCESS || out < 8)
            continue;
        uint8_t *q = (uint8_t *)buf;
        size_t cnt = (out / 8) * 8;
        for (size_t i = 0; i + 16 <= cnt && n1 < AMAX; i += 8) {
            int32_t mv = 0, cv = 0;
            for (int b = 0; b < 4; b++) {
                mv |= ((q[i+b] ^ q[i+7-b]) & 255) << (8*b);
                cv |= ((q[i+8+b] ^ q[i+15-b]) & 255) << (8*b);
            }
            if (mv >= 300 && mv <= 200000000 && mv == cv) { a1[n1] = base + (vm_address_t)i; m1[n1] = mv; c1[n1] = cv; n1++; }
        }
    }
    usleep(400000);
    int n2 = 0;
    static uintptr_t *a2 = NULL; static int32_t *m2 = NULL;
    if (!a2) { a2 = malloc(AMAX*sizeof(*a2)); m2 = malloc(AMAX*sizeof(*m2)); }
    if (!a2) return;
    for (int i = 0; i < n1; i++) {
        int32_t mv = 0, cv = 0; vm_size_t g1 = 0;
        uint8_t rb[16];
        if (vm_read_overwrite(mach_task_self(), (vm_address_t)a1[i], 16, (vm_address_t)rb, &g1) != KERN_SUCCESS || g1 < 16) continue;
        for (int b = 0; b < 4; b++) {
            mv |= ((rb[b] ^ rb[7-b]) & 255) << (8*b);
            cv |= ((rb[8+b] ^ rb[15-b]) & 255) << (8*b);
        }
        if (mv == m1[i] && c1[i] > 0 && cv <= mv && cv < c1[i]) { a2[n2] = a1[i]; m2[n2] = mv; n2++; if (n2 >= AMAX) break; }
    }
    int bestCnt = 0; int32_t bestMv = 0;
    for (int i = 0; i < n2; i++) {
        if (!m2[i]) continue;
        int c = 1;
        for (int j = i+1; j < n2; j++) if (m2[j] == m2[i]) { c++; m2[j] = 0; }
        if (c > bestCnt || (c == bestCnt && m2[i] > bestMv)) { bestCnt = c; bestMv = m2[i]; }
    }
    pthread_mutex_lock(&ts_mtx);
    ts_fn = 0;
    if (bestCnt >= 1) {
        for (int i = 0; i < n2 && ts_fn < 64; i++)
            if (m2[i] == bestMv) { ts_fx[ts_fn] = a2[i]; ts_fv[ts_fn] = bestMv; ts_fn++; }
        for (int i = 0; i < ts_fn; i++)
            *(volatile uint32_t *)(ts_fx[i] + 4) = 0;
        tlog("god auto lock max=%d copies=%d", bestMv, ts_fn);
    }
    pthread_mutex_unlock(&ts_mtx);
}
static void *ts_god_thr(void *arg) {
    (void)arg;
    usleep(400000);
    ts_scan_once();
    int ticks = 0;
    while (ts_god) {
        pthread_mutex_lock(&ts_mtx);
        for (int i = 0; i < ts_fn; i++) {
            int32_t chk = 0; vm_size_t got = 0;
            if (vm_read_overwrite(mach_task_self(), (vm_address_t)ts_fx[i], 4, (vm_address_t)(uintptr_t)&chk, &got) == KERN_SUCCESS)
                *(volatile int32_t *)ts_fx[i] = ts_fv[i];
            else { ts_fn = 0; break; }
        }
        pthread_mutex_unlock(&ts_mtx);
        ticks++;
        if (ts_fn == 0 && (ticks % 12 == 0)) ts_scan_once();
        usleep(250000);
    }
    return NULL;
}
static void TSGodSet(BOOL on) {
    if (on == ts_god) return;
    ts_god = on;
    if (on) { pthread_t th; pthread_create(&th, NULL, ts_god_thr, NULL); pthread_detach(th); }
    tlog("god %d", on ? 1 : 0);
}

/* ================= exports ================= */
__attribute__((visibility("default"))) void BunsTS_Food(void) { ts_apply(0); }
__attribute__((visibility("default"))) void BunsTS_XP(void)   { ts_apply(1); }
__attribute__((visibility("default"))) void BunsTS_SpeedSet(int n) {
    if (n < 1) n = 1;
    if (n > 50) n = 50;
    ts_spd_n = n;
    [NSUserDefaults.standardUserDefaults setInteger:n forKey:@"bg_speed_n"];
}
__attribute__((visibility("default"))) void BunsTS_Energy(int on) {
    tlog("energy toggle -> %d", on);
    ts_energy_pin = on ? 1 : 0;
    if (on) {
        ts_rank();
        uint8_t chk[4]; vm_size_t osz = 0;
        volatile uint8_t *o = ts_ud();
        if (o && vm_read_overwrite(mach_task_self(), (vm_address_t)(o + 0xbd68), 4, (vm_address_t)chk, &osz) == KERN_SUCCESS)
            tlog("pre-pin energy dec=%u", ts_dec(chk));
        ts_rank_records();
        ts_energy_once();
        if (o && vm_read_overwrite(mach_task_self(), (vm_address_t)(o + 0xbd68), 4, (vm_address_t)chk, &osz) == KERN_SUCCESS)
            tlog("post-pin energy dec=%u", ts_dec(chk));
    }
}
__attribute__((visibility("default"))) int BunsTS_EnergyState(void) { return ts_energy_pin; }

/* ================= CATS / SKILLS (ported from BunsGod proven code) ================= */
static void ts_unlock_cats(void) {
    volatile uint8_t *o = (volatile uint8_t *)ts_ud();
    if (!ts_ud_ok()) { tlog("UNLOCK: ud missing"); return; }
    volatile uint32_t *arr = (volatile uint32_t *)(o + 0x46800);
    uint32_t vals[873]; uint32_t uniq[64]; int ucnt[64]; int un = 0;
    for (int i = 0; i < 873; i++) {
        uint32_t v = arr[i]; vals[i] = v;
        int f = -1;
        for (int u = 0; u < un; u++) if (uniq[u] == v) { f = u; break; }
        if (f < 0 && un < 64) { uniq[un] = v; ucnt[un] = 1; un++; }
        else if (f >= 0) ucnt[f]++;
    }
    uint32_t saved = 0; int have_saved = 0;
    NSString *kf = [NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject ?: NSTemporaryDirectory() stringByAppendingPathComponent:@"buns_key.txt"];
    FILE *rf = fopen(kf.UTF8String, "r");
    if (rf) { if (fscanf(rf, "%x", &saved) == 1) have_saved = 1; fclose(rf); }

    /* v5 RULE: remembered key is LAW. Derive only once, ever. */
    if (!have_saved) {
        if (un == 1) {
            /* virgin array: flip LSB of the stored value */
            uint32_t keyU = vals[0];
            uint32_t ownedValU = keyU ^ 1;
            FILE *wf = fopen(kf.UTF8String, "w");
            if (wf) { fprintf(wf, "%08x", keyU); fclose(wf); }
            for (int i = 0; i < 873; i++) arr[i] = ownedValU;
            tlog("UNLOCK virgin done key=%08x wrote=873", keyU);
            return;
        }
        uint32_t modalv2 = 0; int best2 = 0;
        for (int u = 0; u < un; u++) if (ucnt[u] > best2) { best2 = ucnt[u]; modalv2 = uniq[u]; }
        if (best2 < 400 || un > 40) { tlog("UNLOCK: pattern abort modal=%u uniq=%d", best2, un); return; }
        saved = modalv2;
        FILE *wf = fopen(kf.UTF8String, "w");
        if (wf) { fprintf(wf, "%08x", saved); fclose(wf); }
        tlog("UNLOCK key derived %08x", saved);
    }

    uint32_t ownedVal = saved ^ 1;
    int owned = 0;
    for (int i = 0; i < 873; i++) if (vals[i] == ownedVal) owned++;
    if (owned >= 800) { tlog("UNLOCK: already all owned (%d)", owned); return; }
    for (int i = 0; i < 873; i++) arr[i] = ownedVal;

    /* ORGANIZER GATE replay: fields captured flat-all-account then jumping
       exactly at the natural 5th-cat transition (UD time-series 08-24).
       Written via the XOR codec so the stored key halves are preserved. */
    {
        ts_write_max((uint8_t *)o + 0xbe18, 0x01000000u);
        ts_write_max((uint8_t *)o + 0x322160, 0x01000000u);
        ts_write_max((uint8_t *)o + 0x322168, 0x00000000u);
        ts_write_max((uint8_t *)o + 0x3227a0, 1979777735u);
        ts_write_max((uint8_t *)o + 0x3227a8, 1476395176u);
        ts_write_max((uint8_t *)o + 0x324938, 0x01000000u);
        tlog("organizer gate fields stamped");
    }
    tlog("UNLOCK done key=%08x owned_was=%d wrote=873", saved, owned);
}
static void ts_upgrade_cats(void) {
    volatile uint8_t *o = (volatile uint8_t *)ts_ud();
    if (!ts_ud_ok()) { tlog("UPGRADE: ud missing"); return; }
    volatile uint8_t *base = o + 0x475a8;
    const uint32_t T = (80u << 16) | 49u;
    const uint8_t tb[4] = { (uint8_t)T, (uint8_t)(T >> 8), (uint8_t)(T >> 16), (uint8_t)(T >> 24) };
    int n = 0;
    for (int i = 0; i < 873; i++) {
        volatile uint8_t *r = base + (uintptr_t)i * 8;
        uint32_t x = 0;
        for (int b = 0; b < 4; b++) x |= (uint32_t)(r[b] ^ r[7 - b]) << (8 * b);
        if (x == T) continue;
        uint8_t nb[8] = { 0, 0, 0, 0, tb[3], tb[2], tb[1], tb[0] };
        for (int k = 0; k < 8; k++) r[k] = nb[k];
        n++;
    }
    tlog("UPGRADE done records=%d", n);
}
static void ts_golden_skills(void) {
    volatile uint8_t *o = (volatile uint8_t *)ts_ud();
    if (!ts_ud_ok()) { tlog("SKILLS: ud missing"); return; }
    volatile uint8_t *sb = o + 0x49e94;
    int changed = 0;
    for (int r2 = 0; r2 < 11; r2++) {
        volatile uint8_t *rr = sb + (uintptr_t)r2 * 8;
        const uint32_t SV = (uint32_t)(r2 == 10 ? 49 : 999) << 16;
        const uint8_t P[4] = { (uint8_t)SV, (uint8_t)(SV >> 8), (uint8_t)(SV >> 16), (uint8_t)(SV >> 24) };
        uint8_t p0[4];
        for (int k = 0; k < 4; k++) p0[k] = rr[k] ^ rr[7 - k];
        uint32_t cur = (uint32_t)p0[0] | ((uint32_t)p0[1] << 8) | ((uint32_t)p0[2] << 16) | ((uint32_t)p0[3] << 24);
        if (cur == SV) continue;
        for (int j = 0; j < 4; j++) rr[j] = (uint8_t)(P[j] ^ rr[7 - j]);
        changed++;
    }
    tlog("SKILLS golden set, %d changed", changed);
}

/* ================= STARTER SEED (manual button) =================
   Overwrites current save with the known-good 5-cat save (working
   organizer). Manual-only: never fires automatically. */
static void ts_seed_now(void) {
    @autoreleasepool {
        NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
        if (!docs) return;
        NSString *save = [docs stringByAppendingPathComponent:@"SAVE_DATA"];
        NSString *starter = @"/var/jb/usr/lib/TweakInject/BunsTS_starter.bin";
        NSData *d = [NSData dataWithContentsOfFile:starter];
        if (!d || d.length < 100000) { tlog("seed: starter missing"); return; }
        BOOL ok = [d writeToFile:save atomically:YES];
        NSString *kf = [docs stringByAppendingPathComponent:@"buns_key.txt"];
        [[NSFileManager defaultManager] removeItemAtPath:kf error:nil];
        [@"2" writeToFile:[docs stringByAppendingPathComponent:@".buns_seed"] atomically:YES];
        tlog("MANUAL SEED ok=%d (%lu bytes)", ok, (unsigned long)d.length);
    }
}

/* ================= UI ================= */
static UIColor *tsG(void) { return [UIColor colorWithRed:0.3 green:0.85 blue:0.4 alpha:1]; }
static UIColor *tsR(void) { return [UIColor colorWithRed:1 green:0.25 blue:0.25 alpha:1]; }
static UIColor *tsP(void) { return [UIColor colorWithRed:1 green:0.28 blue:0.55 alpha:1]; }

static UILabel *ts_cfVal, *ts_xpVal, *ts_spdVal;
static UIButton *ts_godBtn, *ts_enBtn;

@interface TSMenu : NSObject
+ (void)showPanel;
+ (void)launchPopups;
@end

static UIViewController *ts_rootvc(void) {
    UIWindow *win = [UIApplication sharedApplication].keyWindow;
    UIViewController *vc = win.rootViewController;
    while (vc.presentedViewController) vc = vc.presentedViewController;
    return vc;
}
static void ts_alert(NSString *title, NSString *msg, BOOL red, NSArray *titles, NSArray *handlers) {
    if (![NSThread isMainThread]) { dispatch_async(dispatch_get_main_queue(), ^{ ts_alert(title, msg, red, titles, handlers); }); return; }
    UIViewController *vc = ts_rootvc();
    if (!vc) return;
    UIAlertController *ac = [UIAlertController alertControllerWithTitle:title message:msg preferredStyle:UIAlertControllerStyleAlert];
    if (red) {
        ac.view.backgroundColor = [UIColor colorWithRed:0.16 green:0.01 blue:0.01 alpha:1];
        ac.view.layer.cornerRadius = 14;
        ac.view.tintColor = [UIColor colorWithRed:1 green:0.3 blue:0.3 alpha:1];
    }
    for (NSUInteger i = 0; i < titles.count; i++) {
        void (^h)(void) = handlers[i];
        [ac addAction:[UIAlertAction actionWithTitle:titles[i] style:UIAlertActionStyleDefault
            handler:^(UIAlertAction *act){ if (h) h(); }]];
    }
    [vc presentViewController:ac animated:YES completion:nil];
}
@implementation TSMenu

+ (UIButton *)rowBtn:(CGFloat)x y:(CGFloat)y w:(CGFloat)w title:(NSString *)t color:(UIColor *)c {
    UIButton *b = [UIButton buttonWithType:UIButtonTypeSystem];
    b.frame = CGRectMake(x, y, w, 30);
    [b setTitle:t forState:UIControlStateNormal];
    b.titleLabel.font = [UIFont systemFontOfSize:14 weight:UIFontWeightBold];
    b.tintColor = c;
    b.backgroundColor = [UIColor colorWithWhite:0.22 alpha:1];
    b.layer.cornerRadius = 8;
    return b;
}

+ (void)refresh {
    if (!ts_ud_ok()) return;
    ts_cfVal.text = [NSString stringWithFormat:@"%u", ts_dec((const uint8_t *)ts_ud() + 0xbc58)];
    ts_xpVal.text = [NSString stringWithFormat:@"%u", ts_dec((const uint8_t *)ts_ud() + 0xbde0)];
}
+ (void)doFood { ts_apply(0); [self refresh]; }
+ (void)doXP   { ts_apply(1); [self refresh]; }
+ (void)doGod {
    NSInteger v = [NSUserDefaults.standardUserDefaults integerForKey:@"ng_exact"];
    ts_exact = (v >= 1000) ? (int32_t)v : 0;
    TSGodSet(!ts_god);
    [ts_godBtn setTitle:ts_god ? @"ON" : @"OFF" forState:UIControlStateNormal];
    ts_godBtn.tintColor = ts_god ? tsG() : tsR();
}
+ (void)setSpeed:(int)n {
    BunsTS_SpeedSet(n);
    ts_spdVal.text = [NSString stringWithFormat:@"%dx", n];
    ts_spdVal.textColor = n > 1 ? tsG() : tsR();
}
+ (void)spdStep:(int)d {
    static const int vals[8] = {1,2,3,5,10,15,20,25};
    static NSInteger idx = 0;
    idx += d;
    if (idx < 0) idx = 0;
    if (idx > 7) idx = 7;
    [self setSpeed:(int)vals[idx]];
}
+ (void)spdUp   { [self spdStep: 1]; }
+ (void)spdDown { [self spdStep:-1]; }
+ (void)doEnergy {
    int on = !BunsTS_EnergyState();
    BunsTS_Energy(on);
    [ts_enBtn setTitle:on ? @"ON" : @"OFF" forState:UIControlStateNormal];
    ts_enBtn.tintColor = on ? tsG() : tsR();
}
+ (void)doUnlock {
    /* GATE: organizer flag must already be set by natural 5-cat progress
       (codec read — the field is an XOR record, raw u32 compare is wrong) */
    volatile uint8_t *o8 = (volatile uint8_t *)ts_ud();
    if (!o8 || ts_dec((const uint8_t *)o8 + 0xbe18) != 0x01000000u) {
        ts_alert(@"🔒 5 CATS REQUIRED"
            , @"Play NORMALLY and unlock 5 CATS first.\n\nThe EQUIP button appears at 5 cats — then UNLOCK ALL will give you every cat instantly!\n\n(Blocking early unlock so you can't get soft-locked 🐰)"
            , YES, @[@"GOT IT — BACK TO HUNTING"], @[[^{} copy]]);
        return;
    }
    ts_unlock_cats();
    ts_suppress_until = CFAbsoluteTimeGetCurrent() + 25;
}
+ (void)doMaxLv  { ts_upgrade_cats();  ts_suppress_until = CFAbsoluteTimeGetCurrent() + 25; }
+ (void)doSkills { ts_golden_skills(); ts_suppress_until = CFAbsoluteTimeGetCurrent() + 25; }
+ (void)doSeed {
    ts_seed_now();
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        exit(0);   /* clean exit so the game reloads the seeded save */
    });
}
+ (void)doDump {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        volatile uint8_t *o = ts_ud();
        if (!o || !ts_ud_ok()) { tlog("DUMP: ud missing"); return; }
        NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
        NSString *p = [docs stringByAppendingPathComponent:@"ud_dump.bin"];
        FILE *f = fopen(p.UTF8String, "wb");
        if (!f) { tlog("DUMP: fopen fail"); return; }
        uint8_t *buf = (uint8_t *)malloc(1024 * 1024);
        size_t total = 0;
        for (vm_address_t addr = 0; addr < 0x500000; addr += 1024 * 1024) {
            vm_size_t got = 0;
            kern_return_t kr = vm_read_overwrite(mach_task_self(),
                (vm_address_t)((uintptr_t)o + addr), 1024 * 1024,
                (vm_address_t)(uintptr_t)buf, &got);
            if (kr != KERN_SUCCESS) { memset(buf, 0xCC, 1024 * 1024); got = 1024 * 1024; }
            fwrite(buf, 1, got, f);
            total += got;
        }
        free(buf);
        fclose(f);
        tlog("DUMP wrote %zu bytes -> ud_dump.bin", total);
    });
}
+ (void)hide { [[[[UIApplication sharedApplication] keyWindow] viewWithTag:9100] removeFromSuperview]; }
+ (void)pan:(UIPanGestureRecognizer *)g {
    static CGPoint s0, p0;
    UIView *v = g.view;
    if (g.state == UIGestureRecognizerStateBegan) { s0 = [g translationInView:v.superview]; p0 = v.center; }
    else if (g.state == UIGestureRecognizerStateChanged) {
        CGPoint t = [g translationInView:v.superview];
        v.center = CGPointMake(p0.x + t.x - s0.x, p0.y + t.y - s0.y);
    }
}
+ (void)showRedWarning {
    ts_alert(@"⚠️ WARNING — READ FIRST!"
        , @"PLAY NORMALLY UNTIL YOU HAVE 5 CATS!\n\nThe EQUIP / Organizer button unlocks at 5 cats.\nUNLOCK ALL is BLOCKED until then — this prevents soft-locking your account.\n\nAfter 5 cats: unlock everything & go crazy 🐰"
        , YES
        , @[@"I UNDERSTAND"]
        , @[[^{} copy]]);
}
+ (BOOL)gatePassed {
    volatile uint8_t *o = ts_ud();
    return (o && ts_ud_ok() && ts_dec((const uint8_t *)o + 0xbe18) == 0x01000000u);
}
+ (void)showSubscribeOverlay {
    UIWindow *win = [UIApplication sharedApplication].keyWindow;
    if (!win) return;
    [[win viewWithTag:9300] removeFromSuperview];
    UIView *dim = [[UIView alloc] initWithFrame:win.bounds];
    dim.tag = 9300;
    dim.backgroundColor = [UIColor colorWithWhite:0 alpha:0.55];
    CGFloat cw = 280, ch = 240;
    UIView *card = [[UIView alloc] initWithFrame:CGRectMake((win.bounds.size.width-cw)/2, (win.bounds.size.height-ch)/2 - 40, cw, ch)];
    card.backgroundColor = [UIColor colorWithWhite:0.07 alpha:0.98];
    card.layer.cornerRadius = 16;
    card.layer.borderWidth = 1.5;
    card.layer.borderColor = tsP().CGColor;
    [dim addSubview:card];

    UILabel *bunny = [[UILabel alloc] initWithFrame:CGRectMake(0, 10, cw, 44)];
    NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
    UIImage *logo = [UIImage imageWithContentsOfFile:[docs stringByAppendingPathComponent:@"bunny.png"]];
    if (logo) {
        UIImageView *iv = [[UIImageView alloc] initWithFrame:CGRectMake((cw-56)/2, 8, 56, 56)];
        iv.image = logo; iv.contentMode = UIViewContentModeScaleAspectFill;
        iv.clipsToBounds = YES; iv.layer.cornerRadius = 28;
        [card addSubview:iv];
        bunny.hidden = YES;
    } else {
        bunny.text = @"🐰"; bunny.textAlignment = NSTextAlignmentCenter; bunny.font = [UIFont systemFontOfSize:38];
    }
    [card addSubview:bunny];
    UILabel *title = [[UILabel alloc] initWithFrame:CGRectMake(8, 60, cw-16, 24)];
    title.text = @"HACKED BY BUNS"; title.textAlignment = NSTextAlignmentCenter;
    title.textColor = tsP(); title.font = [UIFont systemFontOfSize:19 weight:UIFontWeightBlack];
    [card addSubview:title];
    UILabel *msg = [[UILabel alloc] initWithFrame:CGRectMake(12, 88, cw-24, 58)];
    msg.text = @"SUBSCRIBE for more hacked games!\nyoutube.com/@BunsDeveloper\nGOD • SPEED • ENERGY • CATS 😈";
    msg.numberOfLines = 0; msg.textAlignment = NSTextAlignmentCenter;
    msg.textColor = [UIColor colorWithWhite:0.85 alpha:1]; msg.font = [UIFont systemFontOfSize:12];
    [card addSubview:msg];
    UIButton *sub = [UIButton buttonWithType:UIButtonTypeSystem];
    sub.frame = CGRectMake(20, 150, cw-40, 34);
    [sub setTitle:@"▶ SUBSCRIBE" forState:UIControlStateNormal];
    sub.titleLabel.font = [UIFont systemFontOfSize:14 weight:UIFontWeightBlack];
    sub.tintColor = UIColor.whiteColor; sub.backgroundColor = [UIColor colorWithRed:0.9 green:0.15 blue:0.2 alpha:1];
    sub.layer.cornerRadius = 9;
    [sub addTarget:self action:@selector(openChannel) forControlEvents:UIControlEventTouchUpInside];
    [card addSubview:sub];
    UIButton *play = [UIButton buttonWithType:UIButtonTypeSystem];
    play.frame = CGRectMake(20, 192, cw-40, 34);
    [play setTitle:@"PLAY" forState:UIControlStateNormal];
    play.titleLabel.font = [UIFont systemFontOfSize:14 weight:UIFontWeightBold];
    play.tintColor = UIColor.whiteColor; play.backgroundColor = [UIColor colorWithWhite:0.25 alpha:1];
    play.layer.cornerRadius = 9;
    [play addTarget:self action:@selector(closeOverlayAndWarn) forControlEvents:UIControlEventTouchUpInside];
    [card addSubview:play];

    [win addSubview:dim];
    [win bringSubviewToFront:dim];
    tlog("subscribe overlay shown");
}
+ (void)openChannel {
    [[UIApplication sharedApplication] openURL:[NSURL URLWithString:@"https://www.youtube.com/@BunsDeveloper"] options:@{} completionHandler:nil];
    /* overlay intentionally stays open */
}
+ (void)closeOverlayAndWarn {
    UIWindow *win = [UIApplication sharedApplication].keyWindow;
    [[win viewWithTag:9300] removeFromSuperview];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        if (![TSMenu gatePassed]) [TSMenu showRedWarning];   /* repeats until 5 cats */
    });
}
+ (void)showPanel {
    UIWindow *win = [UIApplication sharedApplication].keyWindow;
    if (!win) return;
    [[win viewWithTag:9100] removeFromSuperview];
    CGFloat w = 300, h = 300;
    UIView *panel = [[UIView alloc] initWithFrame:CGRectMake(20, 90, w, h)];
    panel.tag = 9100;
    panel.backgroundColor = [UIColor colorWithWhite:0.08 alpha:0.96];
    panel.layer.cornerRadius = 14; panel.clipsToBounds = YES;
    panel.layer.borderWidth = 1.5;
    panel.layer.borderColor = tsP().CGColor;

    UILabel *title = [[UILabel alloc] initWithFrame:CGRectMake(0, 8, w, 22)];
    title.text = @"Buns Menu"; title.textAlignment = NSTextAlignmentCenter;
    title.textColor = UIColor.whiteColor; title.font = [UIFont systemFontOfSize:18 weight:UIFontWeightBold];
    [panel addSubview:title];
    UIButton *close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(w - 34, 6, 26, 24);
    [close setTitle:@"✕" forState:UIControlStateNormal];
    close.tintColor = [UIColor colorWithWhite:0.75 alpha:1];
    [close addTarget:self action:@selector(hide) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:close];

    /* CATFOOD row */
    UILabel *cf = [[UILabel alloc] initWithFrame:CGRectMake(14, 40, 82, 18)];
    cf.text = @"CATFOOD"; cf.textColor = UIColor.whiteColor;
    cf.font = [UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
    [panel addSubview:cf];
    ts_cfVal = [[UILabel alloc] initWithFrame:CGRectMake(96, 41, 104, 16)];
    ts_cfVal.textColor = tsG(); ts_cfVal.font = [UIFont systemFontOfSize:12];
    [panel addSubview:ts_cfVal];
    UIButton *cfb = [self rowBtn:w-74 y:36 w:60 title:@"MAX" color:UIColor.whiteColor];
    cfb.backgroundColor = tsP();
    [cfb addTarget:self action:@selector(doFood) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:cfb];

    /* XP row */
    UILabel *xp = [[UILabel alloc] initWithFrame:CGRectMake(14, 76, 82, 18)];
    xp.text = @"XP"; xp.textColor = UIColor.whiteColor;
    xp.font = [UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
    [panel addSubview:xp];
    ts_xpVal = [[UILabel alloc] initWithFrame:CGRectMake(96, 77, 104, 16)];
    ts_xpVal.textColor = tsG(); ts_xpVal.font = [UIFont systemFontOfSize:12];
    [panel addSubview:ts_xpVal];
    UIButton *xpb = [self rowBtn:w-74 y:72 w:60 title:@"MAX" color:UIColor.whiteColor];
    xpb.backgroundColor = tsP();
    [xpb addTarget:self action:@selector(doXP) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:xpb];

    /* GOD row */
    UILabel *gt = [[UILabel alloc] initWithFrame:CGRectMake(14, 112, 150, 20)];
    gt.text = @"♥ GOD MODE"; gt.textColor = UIColor.whiteColor;
    gt.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:gt];
    ts_godBtn = [self rowBtn:w-116 y:108 w:76 title:ts_god ? @"ON" : @"OFF" color:ts_god ? tsG() : tsR()];
    [ts_godBtn addTarget:self action:@selector(doGod) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ts_godBtn];

    /* SPEED row */
    UILabel *st = [[UILabel alloc] initWithFrame:CGRectMake(14, 148, 52, 20)];
    st.text = @"SPEED"; st.textColor = UIColor.whiteColor;
    st.font = [UIFont systemFontOfSize:13 weight:UIFontWeightSemibold];
    [panel addSubview:st];
    ts_spdVal = [[UILabel alloc] initWithFrame:CGRectMake(w-152, 146, 58, 30)];
    ts_spdVal.text = [NSString stringWithFormat:@"%dx", ts_spd_n];
    ts_spdVal.textAlignment = NSTextAlignmentCenter;
    ts_spdVal.textColor = ts_spd_n > 1 ? tsG() : tsR();
    ts_spdVal.font = [UIFont systemFontOfSize:18 weight:UIFontWeightBold];
    [panel addSubview:ts_spdVal];
    UIButton *dn = [self rowBtn:w-194 y:150 w:38 title:@"◀" color:UIColor.whiteColor];
    dn.backgroundColor = [UIColor colorWithWhite:0.28 alpha:1];
    dn.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightBold];
    dn.layer.cornerRadius = 7;
    [dn addTarget:self action:@selector(spdDown) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:dn];
    UIButton *up = [self rowBtn:w-90 y:150 w:38 title:@"▶" color:UIColor.whiteColor];
    up.backgroundColor = tsP();
    up.titleLabel.font = [UIFont systemFontOfSize:13 weight:UIFontWeightBold];
    up.layer.cornerRadius = 7;
    [up addTarget:self action:@selector(spdUp) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:up];

    /* ENERGY row */
    UILabel *et = [[UILabel alloc] initWithFrame:CGRectMake(14, 184, 160, 20)];
    et.text = @"🔋 ENERGY PIN"; et.textColor = UIColor.whiteColor;
    et.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:et];
    ts_enBtn = [self rowBtn:w-116 y:180 w:76 title:ts_energy_pin ? @"ON" : @"OFF" color:ts_energy_pin ? tsG() : tsR()];
    [ts_enBtn addTarget:self action:@selector(doEnergy) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ts_enBtn];

    /* CATS row */
    UILabel *ct = [[UILabel alloc] initWithFrame:CGRectMake(14, 220, 90, 20)];
    ct.text = @"🐱 CATS"; ct.textColor = UIColor.whiteColor;
    ct.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:ct];
    UIButton *ub = [self rowBtn:w-208 y:216 w:94 title:@"UNLOCK ALL" color:UIColor.whiteColor];
    ub.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    ub.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightBold];
    [ub addTarget:self action:@selector(doUnlock) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:ub];
    UIButton *mb = [self rowBtn:w-106 y:216 w:92 title:@"MAX LEVELS" color:UIColor.whiteColor];
    mb.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    mb.titleLabel.font = [UIFont systemFontOfSize:12 weight:UIFontWeightBold];
    [mb addTarget:self action:@selector(doMaxLv) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:mb];

    /* SKILLS row */
    UILabel *skt = [[UILabel alloc] initWithFrame:CGRectMake(14, 256, 100, 20)];
    skt.text = @"✦ SKILLS"; skt.textColor = UIColor.whiteColor;
    skt.font = [UIFont systemFontOfSize:14 weight:UIFontWeightSemibold];
    [panel addSubview:skt];
    UIButton *skb = [self rowBtn:w-208 y:252 w:194 title:@"MAX SKILLS" color:UIColor.whiteColor];
    skb.backgroundColor = [UIColor colorWithRed:0.55 green:0.2 blue:0.9 alpha:0.9];
    skb.titleLabel.font = [UIFont systemFontOfSize:11 weight:UIFontWeightBold];
    [skb addTarget:self action:@selector(doSkills) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:skb];

    UIPanGestureRecognizer *pan = [[UIPanGestureRecognizer alloc] initWithTarget:self action:@selector(pan:)];
    [panel addGestureRecognizer:pan];
    [win addSubview:panel];
    dispatch_async(dispatch_get_main_queue(), ^{ [win bringSubviewToFront:panel]; });
    [self refresh];
    tlog("panel shown");
}
/* IAP FLOOD SHIELD: catfood/xp/cateye purchase alerts are swallowed
   forever (they regenerate every launch); other alerts suppressed for
   25s after cheat taps. */
static void (*ts_orig_pvc)(id, SEL, UIViewController*, BOOL, void(^)(void));
static BOOL ts_is_junk_alert(UIViewController *v) {
    if (![v isKindOfClass:[UIAlertController class]]) return NO;
    UIAlertController *ac = (UIAlertController *)v;
    NSString *t = [[NSString stringWithFormat:@"%@ %@", ac.title ?: @"", ac.message ?: @""] lowercaseString];
    NSArray *kw = @[@"cat food", @"catfood", @"cat eye", @"cateye", @"xp",
                    @"bundle", @"purchase", @"buy", @"restore", @"insufficient", @"not enough"];
    for (NSString *k in kw) if ([t containsString:k]) return YES;
    return NO;
}
static void ts_pvc_imp(id self, SEL _cmd, UIViewController *v, BOOL anim, void (^comp)(void)) {
    CFAbsoluteTime now = CFAbsoluteTimeGetCurrent();
    if ([v isKindOfClass:[UIAlertController class]]) {
        UIAlertController *ac = (UIAlertController *)v;
        tlog("UIAlertVC seen: title='%@' msg='%.60@'", ac.title ?: @"-", ac.message ?: @"-");
        if (ts_is_junk_alert(v)) { if (comp) comp(); return; }
        if (now < ts_suppress_until) { if (comp) comp(); return; }
    } else {
        tlog("PRES non-alert: %@ title='%@'", NSStringFromClass([v class]), [(id)v respondsToSelector:@selector(title)] ? [(id)v title] : @"-");
    }
    ts_orig_pvc(self, _cmd, v, anim, comp);
}
/* legacy path: UIAlertView.show (2014-era engine dialogs) */
static void (*ts_orig_avshow)(id, SEL);
static void ts_avshow_imp(id self, SEL _cmd) {
    CFAbsoluteTime now = CFAbsoluteTimeGetCurrent();
    if ([self isKindOfClass:[UIAlertView class]]) {
        NSString *t = [[NSString stringWithFormat:@"%@ %@", [(id)self title] ?: @"", [(id)self message] ?: @""] lowercaseString];
        tlog("AVAlert seen: '%.80@'", t);
        NSArray *kw = @[@"cat food", @"catfood", @"cat eye", @"cateye", @"xp",
                        @"bundle", @"purchase", @"buy", @"restore", @"insufficient", @"not enough"];
        for (NSString *k in kw) if ([t containsString:k]) { tlog("AVAlert swallowed"); return; }
        if (now < ts_suppress_until) return;
    }
    ts_orig_avshow(self, _cmd);
}
+ (void)load {
    NSBundle *b = [NSBundle mainBundle];
    if (![[b bundleIdentifier] isEqualToString:@"com.buns.bc.hacked"]) return;
    Method m = class_getInstanceMethod([UIViewController class], @selector(presentViewController:animated:completion:));
    if (m) {
        ts_orig_pvc = (void (*)(id, SEL, UIViewController*, BOOL, void(^)(void)))method_getImplementation(m);
        method_setImplementation(m, (IMP)ts_pvc_imp);
    }
    Method m2 = class_getInstanceMethod([UIAlertView class], @selector(show));
    if (m2) {
        ts_orig_avshow = (void (*)(id, SEL))method_getImplementation(m2);
        method_setImplementation(m2, (IMP)ts_avshow_imp);
    }
}
@end

/* FAB with the real logo */
static UIButton *ts_fab = nil;
static void ts_toggle_fab(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        UIWindow *win = [UIApplication sharedApplication].keyWindow;
        if (!win) return;
        if (ts_fab && ts_fab.superview) { [TSMenu showPanel]; return; }
        if (!ts_fab) {
            ts_fab = [UIButton buttonWithType:UIButtonTypeCustom];
            ts_fab.frame = CGRectMake(14, 140, 52, 52);
            ts_fab.layer.cornerRadius = 26; ts_fab.clipsToBounds = YES;
            ts_fab.backgroundColor = [UIColor colorWithWhite:0.05 alpha:0.95];
            ts_fab.layer.borderWidth = 1.5;
            ts_fab.layer.borderColor = tsP().CGColor;
            NSString *docs = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
            UIImage *bun = [UIImage imageWithContentsOfFile:[docs stringByAppendingPathComponent:@"bunny.png"]];
            if (bun) {
                [ts_fab setImage:bun forState:UIControlStateNormal];
                ts_fab.imageView.contentMode = UIViewContentModeScaleAspectFill;
            } else {
                [ts_fab setTitle:@"🐰" forState:UIControlStateNormal];
                ts_fab.titleLabel.font = [UIFont systemFontOfSize:26];
            }
            [ts_fab addTarget:[TSMenu class] action:@selector(showPanel) forControlEvents:UIControlEventTouchUpInside];
            UIPanGestureRecognizer *pan = [[UIPanGestureRecognizer alloc] initWithTarget:[TSMenu class] action:@selector(pan:)];
            [ts_fab addGestureRecognizer:pan];
            tlog("fab ready png=%d", bun ? 1 : 0);
        }
        [win addSubview:ts_fab];
        [win bringSubviewToFront:ts_fab];
        static dispatch_once_t popOnce;
        dispatch_once(&popOnce, ^{ [TSMenu showSubscribeOverlay]; });
    });
}

/* ================= STARTER SEED ================= */
__attribute__((constructor))
static void bunts_init(void) {
    @autoreleasepool {
        NSString *bid = [[NSBundle mainBundle] bundleIdentifier];
        if (![bid isEqualToString:@"com.buns.bc.hacked"]) return;
        for (uint32_t i = 0; i < _dyld_image_count(); i++) {
            const char *n = _dyld_get_image_name(i);
            if (n && strstr(n, "battlecatsen.app/battlecatsen")) {
                g_base = 0x100000000 + _dyld_get_image_vmaddr_slide(i);
                break;
            }
        }
        NSInteger sp = [NSUserDefaults.standardUserDefaults integerForKey:@"bg_speed_n"];
        if (sp >= 1 && sp <= 50) ts_spd_n = (int)sp;
        tlog("BunsTS v2 init base=%p spd=%d", (void *)g_base, ts_spd_n);
        pthread_t th; pthread_create(&th, NULL, ts_bg_thr, NULL); pthread_detach(th);
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(3 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
            if (ts_ud_ok()) { ts_rank(); tlog("boot rank lift done"); }
        });
        dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(4 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
            ts_toggle_fab();
        });
    }
}
