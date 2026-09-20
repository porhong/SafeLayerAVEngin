"""Applies the SafeLayer build patch set to a ClamAV release checkout.

Every edit asserts that the text it replaces is present exactly once, so a
rebase onto a new upstream tag fails loudly instead of half-applying.
"""
import sys

ROOT = sys.argv[1]
NL = chr(10)


def edit(rel, pairs):
    path = ROOT + "/" + rel
    raw = open(path, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", NL)
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit("%s: expected exactly one %r, found %d" % (rel, old, text.count(old)))
        text = text.replace(old, new)
    if crlf:
        text = text.replace(NL, "\r\n")
    open(path, "wb").write(text.encode("utf-8"))
    print("patched", rel)


# 1. Executable file names.
for target, folder, name in [
    ("clamd", "clamd", "slengine"),
    ("clamscan", "clamscan", "slscan"),
    ("clamdscan", "clamdscan", "slscanc"),
]:
    old = 'set_target_properties( %s PROPERTIES COMPILE_FLAGS "${WARNCFLAGS}" )' % target
    new = old + NL + "# SafeLayer build: the program ships under SafeLayer's file name." + NL + \
        "set_target_properties( %s PROPERTIES OUTPUT_NAME %s )" % (target, name)
    edit(folder + "/CMakeLists.txt", [(old, new)])

edit("freshclam/CMakeLists.txt", [
    ("# Now we rename freshclam-bin executable to freshclam using target properties",
     "# SafeLayer build: the freshclam-bin executable ships as slupdate."),
    ("PROPERTIES OUTPUT_NAME freshclam )", "PROPERTIES OUTPUT_NAME slupdate )"),
])

# 2. The Windows test environment names the programs literally.
edit("unit_tests/CMakeLists.txt", [
    ("$<TARGET_FILE_DIR:check_clamav>/clamd.exe  ", "$<TARGET_FILE_DIR:check_clamav>/$<TARGET_FILE_NAME:clamd>"),
    ("$<TARGET_FILE_DIR:check_clamav>/clamdscan.exe  ", "$<TARGET_FILE_DIR:check_clamav>/$<TARGET_FILE_NAME:clamdscan>"),
    ("$<TARGET_FILE_DIR:check_clamav>/clamscan.exe  ", "$<TARGET_FILE_DIR:check_clamav>/$<TARGET_FILE_NAME:clamscan>"),
    ("$<TARGET_FILE_DIR:check_clamav>/freshclam.exe  ", "$<TARGET_FILE_DIR:check_clamav>/$<TARGET_FILE_NAME:freshclam-bin>"),
])

# 3. Version resources. Cisco's copyright line stays; the modification is stated.
edit("win32/res/common.rc.in", [
    ('#define RES_VER_S "ClamAV @PROJECT_VERSION_MAJOR@.@PROJECT_VERSION_MINOR@.@PROJECT_VERSION_PATCH@-devel"',
     '#define RES_VER_S "@PROJECT_VERSION_MAJOR@.@PROJECT_VERSION_MINOR@.@PROJECT_VERSION_PATCH@"'),
    ('VALUE "CompanyName", "Cisco Systems, Inc."', 'VALUE "CompanyName", "Anantbot"'),
    ('VALUE "ProductName", "ClamAV"', 'VALUE "ProductName", "SafeLayer AV Engine"'),
    ('VALUE "LegalCopyright", "(C) 2025 Cisco Systems, Inc."',
     'VALUE "LegalCopyright", "(C) 2025 Cisco Systems, Inc. Modified build (C) 2026 Anantbot."'),
    ('VALUE "Comments", REPO_VERSION',
     'VALUE "Comments", "Based on ClamAV " REPO_VERSION ", modified by Anantbot. Source: https://github.com/porhong/SafeLayerAVEngin"'),
])

for rc, fname, name, desc in [
    ("clamd", "slengine.exe", "slengine", "SafeLayer AV Engine - service"),
    ("clamscan", "slscan.exe", "slscan", "SafeLayer AV Engine - scanner"),
    ("clamdscan", "slscanc.exe", "slscanc", "SafeLayer AV Engine - service client"),
    ("freshclam", "slupdate.exe", "slupdate", "SafeLayer AV Engine - signature updater"),
]:
    edit("win32/res/%s.rc" % rc, [
        ('#define RES_FNAME "%s.exe"' % rc, '#define RES_FNAME "%s"' % fname),
        ('#define RES_NAME "%s"' % rc, '#define RES_NAME "%s"' % name),
        ('#define RES_FDESC "ClamAV - %s"' % rc, '#define RES_FDESC "%s"' % desc),
        # The upstream icon is ClamAV artwork; ship without one.
        (NL + '1337 ICON "clam.ico"', ""),
    ])

# 4. Do not adopt another ClamAV installation's directories from its registry key.
edit("common/optparser.c", [
    ('#define CLAMKEY "Software' + chr(92)*2 + 'ClamAV"',
     '/* SafeLayer build: own key, so a separate ClamAV installation is never adopted. */' + NL +
     '#define CLAMKEY "Software' + chr(92)*2 + 'SafeLayerAV' + chr(92)*2 + 'Engine"'),
])

# 5. Notice of modification at the top of the README (GPLv2 section 2a).
notice = open(ROOT + "/safelayer/readme-notice.md", encoding="utf-8").read()
readme_path = ROOT + "/README.md"
readme = open(readme_path, "rb").read().decode("utf-8")
if "This is a modified build of ClamAV" not in readme:
    notice = notice.replace("\r\n", NL)
    if "\r\n" in readme:
        notice = notice.replace(NL, "\r\n")
    open(readme_path, "wb").write((notice + readme).encode("utf-8"))
    print("patched README.md")
