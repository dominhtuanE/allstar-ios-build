"""Va engine + du an iOS cho Allstar Warrior (python3 patch.py <engine> <proj>).
1. FileUtils::getPathForFilename: khong thay file -> thu lai ten bo duoi (tai nguyen goc cua game bi bo duoi
   file, ban Android dung engine da sua de tra bang ten).
2. AppController: moi phuong thuc lop la dang "xxx:" (game goi jsb.reflection.callStaticMethod("AppController", ...)
   cho SDK goc) -> tu them, tra ve @"{}".
3. Man hinh doc: Info.plist + RootViewController. Ten hien thi "Allstar Warrior", bo yeu cau opengles-1."""
import os
import plistlib
import re
import sys

engine, proj = sys.argv[1], sys.argv[2]
ios = os.path.join(proj, 'frameworks', 'runtime-src', 'proj.ios_mac', 'ios')


def edit(path, old, new, count=1):
    s = open(path, encoding='utf8').read()
    if old not in s:
        raise SystemExit('khong thay mau trong %s: %r' % (path, old[:80]))
    s = s.replace(old, new, count)
    open(path, 'w', encoding='utf8').write(s)
    print('va', path)


# 1. FileUtils
edit(os.path.join(engine, 'cocos', 'platform', 'CCFileUtils.cpp'),
     '''    path = getFullPathForDirectoryAndFilename(path, file);

    return path;
}''',
     '''    std::string dir = path;
    path = getFullPathForDirectoryAndFilename(dir, file);
    if (path.empty()) {  // [private] tai nguyen goc bi bo duoi file -> thu ten khong duoi
        size_t dot = file.find_last_of('.');
        // khong ap dung cho .jsc (engine thu main.jsc truoc main.js -> se doc nham file JS thuong)
        if (dot != std::string::npos && dot > 0 && file.compare(dot, std::string::npos, ".jsc") != 0)
            path = getFullPathForDirectoryAndFilename(dir, file.substr(0, dot));
    }

    return path;
}''')

# 1a. V8 luon chay --jitless tren iOS: app cai qua Sideloadly khong duoc cap trang nho thuc thi (JIT);
#     jitSupported() bao sai tren iOS moi -> regexp bien dich ra ma may -> KERN_PROTECTION_FAILURE (SIGKILL)
edit(os.path.join(engine, 'cocos', 'scripting', 'js-bindings', 'jswrapper', 'v8', 'ScriptEngine.cpp'),
     '''        if(!jitSupported()) {
            flags.append(" --jitless");
        }''',
     '''        flags.append(" --jitless");  // [private] luon tat JIT tren iOS''')

# 1b. COCOS_X_ROOT (Creator dat san) -> duong dan tuyet doi toi engine trong moi xcconfig/pbxproj cua du an
COCOS_ROOT = '/Applications/CocosCreator.app/Contents/Resources/cocos2d-x'
for base in (os.path.join(proj, 'frameworks'),):
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(('.xcconfig', '.pbxproj')):
                p = os.path.join(root, f)
                s = open(p, encoding='utf8', errors='surrogateescape').read()
                n = s.replace('${COCOS_X_ROOT}', COCOS_ROOT).replace('$(COCOS_X_ROOT)', COCOS_ROOT)
                if n != s:
                    open(p, 'w', encoding='utf8', errors='surrogateescape').write(n)
                    print('COCOS_X_ROOT ->', p)

# 2. AppController: phuong thuc lop dong
ac = os.path.join(ios, 'AppController.mm')
s = open(ac, encoding='utf8').read()
if '#import <objc/runtime.h>' not in s:
    s = '#import <objc/runtime.h>\n' + s
if '#include <execinfo.h>' not in s:
    s = '#include <execinfo.h>\n#include <string.h>\n#include <signal.h>\n#include <unistd.h>\n#include <fcntl.h>\n#include <stdio.h>\n' + s
s = s.replace('@implementation AppController\n', '''static id pv_native_stub(id self, SEL _cmd, id arg) { return @"{}"; }
static id pv_native_stub0(id self, SEL _cmd) { return @"{}"; }

// [private] log chan doan -> Documents (lay ra bang iTunes > Chia se tep)
static int pv_crash_fd = -1;
static void pv_signal(int sig) {
    if (pv_crash_fd >= 0) {
        char m[64]; int n = snprintf(m, sizeof m, "\\n== SIGNAL %d ==\\n", sig); write(pv_crash_fd, m, n);
        void *bt[64]; int c = backtrace(bt, 64); backtrace_symbols_fd(bt, c, pv_crash_fd); fsync(pv_crash_fd);
    }
    signal(sig, SIG_DFL); raise(sig);
}
static void pv_exception(NSException *e) {
    NSString *t = [NSString stringWithFormat:@"\\n== NSException %@: %@ ==\\n%@\\n", e.name, e.reason, e.callStackSymbols];
    if (pv_crash_fd >= 0) { const char *u = t.UTF8String; write(pv_crash_fd, u, strlen(u)); fsync(pv_crash_fd); }
}
void pv_mark(const char *m) { fprintf(stderr, "[pv] %s\\n", m); fflush(stderr); }
static void pv_diag_init() {
    NSString *doc = NSSearchPathForDirectoriesInDomains(NSDocumentDirectory, NSUserDomainMask, YES).firstObject;
    freopen([[doc stringByAppendingPathComponent:@"pv_log.txt"] fileSystemRepresentation], "w", stderr);
    freopen([[doc stringByAppendingPathComponent:@"pv_stdout.txt"] fileSystemRepresentation], "w", stdout);
    setvbuf(stdout, NULL, _IOLBF, 0); setvbuf(stderr, NULL, _IONBF, 0);
    pv_crash_fd = open([[doc stringByAppendingPathComponent:@"pv_crash.txt"] fileSystemRepresentation], O_WRONLY | O_CREAT | O_APPEND, 0644);
    int sigs[] = {SIGSEGV, SIGABRT, SIGBUS, SIGILL, SIGFPE, SIGTRAP};
    for (int i = 0; i < 6; i++) signal(sigs[i], pv_signal);
    NSSetUncaughtExceptionHandler(&pv_exception);
    pv_mark([[NSString stringWithFormat:@"boot %@ iOS %@", [NSDate date], [UIDevice currentDevice].systemVersion] UTF8String]);
}

@implementation AppController

// [private] SDK goc khong co tren ban nay: lenh "ten:" / "ten" cua game (goi qua jsb.reflection) tra ve "{}".
// Bo qua selector he thong (KVO, NSObject, '_' ...) de khong lam hong UIKit.
// Danh sach bo qua la mang chuoi C: du an bien dich KHONG ARC -> @[...] luu trong bien static bi giai phong -> crash.
+ (BOOL)resolveClassMethod:(SEL)sel {
    static const char *skip[] = {"_", "automatically", "keyPaths", "instances", "conformsTo", "isSubclass", "resolve",
        "accessInstance", "load", "initialize", "new", "alloc", "copy", "mutableCopy", "description", "debugDescription",
        "respondsTo", "methodFor", "instanceMethod", "class", "superclass", "supports", "layer", "hash", "self",
        "requires", "is", "should", "can", "set", "get", "init", "dealloc", "retain", "release", "autorelease", NULL};
    const char *n = sel_getName(sel);
    for (int i = 0; skip[i]; i++) if (strncmp(n, skip[i], strlen(skip[i])) == 0) return [super resolveClassMethod:sel];
    const char *c = strchr(n, ':');
    int colons = 0;
    for (const char *q = n; *q; q++) if (*q == ':') colons++;
    if (colons == 1 && c[1] == 0) {  // "ten:" -> 1 tham so
        pv_mark("native stub (1 arg)"); pv_mark(n);
        class_addMethod(object_getClass(self), sel, (IMP)pv_native_stub, "@@:@");
        return YES;
    }
    if (colons == 0 && n[0] >= 'a' && n[0] <= 'z') {  // "ten" -> khong tham so (vd pingsdtw8)
        pv_mark("native stub (0 arg)"); pv_mark(n);
        class_addMethod(object_getClass(self), sel, (IMP)pv_native_stub0, "@@:");
        return YES;
    }
    return [super resolveClassMethod:sel];
}
''', 1)
s = s.replace('''- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
''', '''- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    pv_diag_init();
''', 1)
s = s.replace('    app->start();\n', '    pv_mark("app->start begin");\n    app->start();\n    pv_mark("app->start end");\n', 1)
if 'pv_diag_init();' not in s or 'app->start begin' not in s:
    raise SystemExit('khong chen duoc log chan doan vao AppController.mm')
open(ac, 'w', encoding='utf8').write(s)
print('va', ac)

# 2b. moc log trong AppDelegate.cpp (khoi dong JS)
ad = os.path.join(proj, 'frameworks', 'runtime-src', 'Classes', 'AppDelegate.cpp')
s = open(ad, encoding='utf8').read()
s = s.replace('USING_NS_CC;', 'USING_NS_CC;\nvoid pv_mark(const char *m);', 1)
s = s.replace('        cocos2d::log("\\nUncaught Exception:', '        pv_mark(message); pv_mark(stack);\n        cocos2d::log("\\nUncaught Exception:', 1)
s = s.replace('    jsb_run_script("jsb-adapter/jsb-builtin.js");\n    jsb_run_script("main.js");',
              '    pv_mark("run jsb-builtin");\n    jsb_run_script("jsb-adapter/jsb-builtin.js");\n'
              '    pv_mark("run main.js");\n    jsb_run_script("main.js");\n    pv_mark("main.js returned");', 1)
if 'run main.js' not in s or 'pv_mark(message)' not in s:
    raise SystemExit('khong chen duoc moc log vao AppDelegate.cpp')
open(ad, 'w', encoding='utf8').write(s)
print('va', ad)

# 3. man hinh doc
rv = os.path.join(ios, 'RootViewController.mm')
s = open(rv, encoding='utf8').read()
s = re.sub(r'return UIInterfaceOrientationMask\w+;', 'return UIInterfaceOrientationMaskPortrait;', s)
open(rv, 'w', encoding='utf8').write(s)
print('va', rv)

ip = os.path.join(ios, 'Info.plist')
pl = plistlib.load(open(ip, 'rb'))
pl['CFBundleDisplayName'] = 'Allstar Warrior'
pl['UISupportedInterfaceOrientations'] = ['UIInterfaceOrientationPortrait']
pl['UIRequiredDeviceCapabilities'] = ['arm64']
pl['NSAppTransportSecurity'] = {'NSAllowsArbitraryLoads': True, 'NSAllowsArbitraryLoadsForMedia': True,
                                'NSAllowsLocalNetworking': True}
pl['NSLocalNetworkUsageDescription'] = 'Ket noi toi may chu rieng trong mang noi bo.'
pl['UIFileSharingEnabled'] = True
plistlib.dump(pl, open(ip, 'wb'))
print('va', ip)
