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

# 2. AppController: phuong thuc lop dong
ac = os.path.join(ios, 'AppController.mm')
s = open(ac, encoding='utf8').read()
if '#import <objc/runtime.h>' not in s:
    s = '#import <objc/runtime.h>\n' + s
s = s.replace('@implementation AppController\n', '''static id pv_native_stub(id self, SEL _cmd, id arg) { return @"{}"; }

@implementation AppController

// [private] SDK goc khong co tren ban nay: moi lenh "ten:" cua game tra ve "{}"
+ (BOOL)resolveClassMethod:(SEL)sel {
    NSString *n = NSStringFromSelector(sel);
    if ([n hasSuffix:@":"] && [[n componentsSeparatedByString:@":"] count] == 2) {
        class_addMethod(object_getClass(self), sel, (IMP)pv_native_stub, "@@:@");
        return YES;
    }
    return [super resolveClassMethod:sel];
}
''', 1)
open(ac, 'w', encoding='utf8').write(s)
print('va', ac)

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
