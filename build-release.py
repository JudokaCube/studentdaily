#!/usr/bin/env python3
from pathlib import Path
import shutil,tarfile
root=Path(__file__).resolve().parent
release=root/'release'
if release.exists():shutil.rmtree(release)
release.mkdir()
for name in ('bin','plugins','services','integrations'):shutil.copytree(root/name,release/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for path in (root/'packaging').iterdir():
    if path.is_file():shutil.copy2(path,release/path.name)
shutil.copy2(root/'LICENSE',release/'LICENSE')
(release/'README.md').write_text('# studentdaily\n\n## install\n\nrun as your normal desktop user:\n\n```sh\nbash install.sh\n```\n\nrequires linux, python 3.11+, kitty and systemd. reminders use python-dbus and python-gobject. choose noctalia, waybar, caelestia or no bar. caelestia needs an editable shell checkout. the installer reports missing dependencies. existing app data is preserved; no keybindings are added. open a new terminal afterward for updated aliases.\n\n## studentdaily\n\nchoose empty, customize now, or import a preset during setup. run `classes` afterward. schedule edits subjects and teachers; zones edits clocks; data imports/exports; theme changes appearance.\n\n- `--setup blank`: start empty\n- `--setup customize`: open setup editors\n- `--preset file.json`: import on a fresh install\n\n## options\n\nsetup selects theme, opacity, bar, position, aliases and reminders. `--help` lists all flags; `--yes` skips questions.\n\n- `--no-start`: enable startup services without starting them now\n- right-click a widget to reload it and open fresh app code\n- source and release-building instructions are in the separate source project\n')
with tarfile.open(root/'release.tar.gz','w:gz') as out:
    for path in release.rglob('*'):
        if path.is_file():
            info=out.gettarinfo(str(path),str(Path('release')/path.relative_to(release)))
            info.uid=info.gid=0;info.uname=info.gname=''
            with path.open('rb') as f:out.addfile(info,f)
print('Created release/ and release.tar.gz')
