# SafeLayer engine build

This fork produces the scan engine package that SafeLayer AV downloads at first
run. It is ClamAV with a small, mechanical patch set. The engine runs as a
separate process; SafeLayer AV talks to it over a local connection.

## Branches and tags

- `main` mirrors upstream's development branch. Nothing is built from it.
- `safelayer/<line>` (for example `safelayer/1.5.x`) is an upstream release tag
  plus the patch set. Packages are built only from these branches.
- `engine-<version>` tags (for example `engine-1.5.4`) are published packages.
  Every ZIP names its tag and commit in `SOURCE.txt`. Never delete or move one
  of these tags: it is the source record the GPL requires.

## The patch set

| Change | Files |
|---|---|
| Program file names `slengine`, `slscan`, `slscanc`, `slupdate` | `clamd/`, `clamscan/`, `clamdscan/`, `freshclam/CMakeLists.txt` |
| Windows tests find the programs by target, not by literal name | `unit_tests/CMakeLists.txt` |
| Version resources: company, product, descriptions, no ClamAV icon. Cisco's copyright line stays and the modification is stated | `win32/res/common.rc.in`, four `.rc` files |
| Own registry key, so another ClamAV installation's directories are never adopted | `common/optparser.c` |
| Notice of modification | `README.md` |

Not changed, on purpose: scanning code, signature (CVD) verification, the
updater's User-Agent and the version number. The official signature source
blocks clients it does not recognise and versions past end of life.

## Moving to a new upstream release

```
git fetch upstream --tags
git checkout -b safelayer/1.5.x-next clamav-1.5.5     # or rebase the branch
python safelayer/apply-patches.py .
```

`apply-patches.py` stops if any text it replaces is missing or ambiguous, so a
changed upstream file is noticed instead of half-patched. Review the diff, push
the branch, and wait for the workflow: upstream's full test suite has to pass.
Then tag `engine-<version>` and push the tag to publish.

An upstream security release should become a package within days.

## Publishing

The `SafeLayer engine` workflow builds on every push to `safelayer/**`. On an
`engine-*` tag it also creates a release here and uploads the ZIP to the app's
release channel (`porhong/safelayer-av-releases`, release `engine`). That last
step needs a repository secret, `RELEASE_CHANNEL_TOKEN`: a fine-grained token
with Contents read/write on the release channel repository only.

## Do not publish unsigned builds

Binaries are not code signed yet, and that blocks publishing. Tested on
2026-09-20 with the first green build (commit `3f64c44`), on Windows 11 with
Microsoft Defender real-time protection on:

- `slscan.exe` was given the EICAR test string. Defender flagged the scanner's
  temp file, which is expected, and three seconds later its machine-learning
  classifier convicted `slscan.exe` itself as `Trojan:Win32/Bearfoos.B!ml`,
  ended the process and deleted the file.
- The Cisco-signed upstream `clamscan.exe` 1.5.4 did the same thing on the same
  machine one minute later. Defender flagged only the temp file.
- After the conviction, a fresh copy of `slscan.exe` was refused at launch even
  for a harmless scan ("the file contains a virus or potentially unwanted
  software").

An unsigned, unknown program that writes malware to disk looks like a dropper.
A scan engine does that all day. So before any `engine-*` tag: sign every
program and DLL built here with a certificate that carries reputation, submit
each release to Microsoft as a false positive if it is still flagged, and repeat
this test. Until then SafeLayer AV keeps downloading the upstream package, which
the app still supports.
