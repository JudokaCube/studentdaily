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
(release/'README.md').write_text('# StudentDaily\n\nOrganize classes, personal events and daily tasks, with reminders and a desktop widget.\n\n## Features\n\n- Classes and personal events, with interactive forms and edits for one occurrence, future occurrences or the whole series.\n- Daily School/Life tasks, teachers, meeting links, extra timezone clocks and search.\n- Event reminders, progress indicators, early finish/undo, and JSON import/export.\n- Nine themes, optional transparency, square border styles and configurable widgets.\n\n## Installation\n\nRequires Linux, Python 3.11+, Kitty and systemd. Reminders use python-dbus and python-gobject.\n\nFrom the installer folder, run as your normal desktop user:\n\n```sh\nbash install.sh\n```\n\nThis installer includes only StudentDaily and its widgets. Choose a bar, theme and background-service options during setup. Existing app data is preserved. Open a new terminal to use newly enabled aliases.\n\n## Usage\n\nRun `studentdaily`. Local installs also provide `classes`, with optional `class` and `today` aliases. Use **Schedule** to add or edit events, **Zones** for clocks, and **Data** for import/export. Click controls or use the keyboard; **H** opens help.\n\nIn event forms, type directly into fields, use arrows or Tab to move, and toggle repeat days with Space. **Apply to** opens the one-date, future-date and entire-series choices; a summary shows the affected dates. Weekly presets select weekdays or daily personal events. **Ctrl+S** saves; **Esc** cancels. When saving a changed meeting link, choose all classes with that title or the selected event scope. Personal events have no teacher or meeting-link fields.\n\n## Settings\n\nOpen **Settings** or press **Y**. Use arrows for quick adjustments; Enter or a click opens choices. **Save / Ctrl+S** applies changes; **Esc** discards unsaved changes.\n\n- StudentDaily: 12/24-hour clocks, clock seconds, week numbers, teacher details, default event length, reminders, progress, weekends and task summary.\n- Appearance: theme, opacity, borders, widget visibility and text. Noctalia also supports animation controls.\n\nReopen the app after changing opacity. Widget changes appear after a short delay.\n\n## Desktop bars\n\n- **Noctalia 5.3+**: native widgets with hover details.\n- **Waybar**: custom modules and tooltips. Restart Waybar after installation.\n- **Caelestia**: requires a writable shell checkout using `--caelestia-root`. Restart the shell after installation.\n- **No bar**: use the apps and optional background services on their own.\n\nRight-click a widget to reload and open its app.\n\n## License\n\nMIT · jdkcube\n')
with tarfile.open(root/'release.tar.gz','w:gz') as out:
    for path in release.rglob('*'):
        if path.is_file():
            info=out.gettarinfo(str(path),str(Path('release')/path.relative_to(release)))
            info.uid=info.gid=0;info.uname=info.gname=''
            with path.open('rb') as f:out.addfile(info,f)
print('Created release/ and release.tar.gz')
