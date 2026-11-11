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
(release/'README.md').write_text('# StudentDaily\n\n## Install\n\nRun as your normal desktop user:\n\n```sh\nbash install.sh\n```\n\nRequires Linux, Python 3.11+, Kitty and systemd. Reminders use python-dbus and python-gobject. Choose Noctalia, Waybar, Caelestia or no bar. Caelestia needs an editable shell checkout. The installer reports missing dependencies. Existing app data is preserved; no keybindings are added. Open a new terminal afterward for updated aliases.\n\n## StudentDaily\n\nChoose empty, customize now, or import a preset during setup. Run `classes` afterward. Schedule opens an interactive event list and form. Choose class or personal; personal events follow the selected theme and have no teacher or meeting link. Ctrl+s saves, Esc cancels. Zones edits clocks; data imports/exports; theme changes appearance.\n\n- `--setup blank`: start empty.\n- `--setup customize`: open setup editors.\n- `--preset file.json`: import on a fresh install.\n\n## Options\n\nSetup selects theme, opacity, bar, position, aliases and reminders. `--help` lists all flags; `--yes` skips questions.\n\n- `--no-start`: enable startup services without starting them now.\n- Right-click a widget to reload it and open fresh app code.\n- Source and release-building instructions are in the separate source project.\n')
with tarfile.open(root/'release.tar.gz','w:gz') as out:
    for path in release.rglob('*'):
        if path.is_file():
            info=out.gettarinfo(str(path),str(Path('release')/path.relative_to(release)))
            info.uid=info.gid=0;info.uname=info.gname=''
            with path.open('rb') as f:out.addfile(info,f)
print('Created release/ and release.tar.gz')
