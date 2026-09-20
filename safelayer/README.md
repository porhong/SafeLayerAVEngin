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

Binaries are not code signed yet. Signing has to be added before the package is
offered to the public.
