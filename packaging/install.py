#!/usr/bin/env python3
"""Install only the components shipped next to this file."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HOME=Path.home()
CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',HOME/'.config'))
DATA=Path(os.environ.get('XDG_DATA_HOME',HOME/'.local/share'))

def main():
    has_classes=(ROOT/'bin/classes').exists()
    has_packages=(ROOT/'bin/system-update').exists()
    app_name='StudentDaily + KeepItNew' if has_classes and has_packages else 'StudentDaily' if has_classes else 'KeepItNew'
    choices=['both','classes','packages'] if has_classes and has_packages else ['classes'] if has_classes else ['packages']
    parser=argparse.ArgumentParser(description=f'Install {app_name} and its widgets. Existing data is preserved.')
    parser.add_argument('--setup',choices=['blank','customize','import'])
    parser.add_argument('--preset',type=Path,help='Optional private JSON preset to import on a fresh install')
    parser.add_argument('--no-start',action='store_true')
    parser.add_argument('--bar',choices=['auto','noctalia','waybar','caelestia','none'],default='auto')
    parser.add_argument('--components',choices=choices,help='Choose apps included in this installer' if len(choices)>1 else argparse.SUPPRESS)
    parser.add_argument('--position',choices=['auto','start','center','end'],default='auto')
    parser.add_argument('--waybar-config',type=Path)
    parser.add_argument('--caelestia-root',type=Path)
    parser.add_argument('--theme')
    parser.add_argument('--opacity',type=float)
    parser.add_argument('--reminder-minutes',type=int,default=5)
    parser.add_argument('--check-minutes',type=int,default=30)
    parser.add_argument('--no-reminders',action='store_true')
    parser.add_argument('--no-checks',action='store_true')
    parser.add_argument('--no-aliases',action='store_true')
    parser.add_argument('--confirm-updates',action='store_true')
    parser.add_argument('--yes',action='store_true',help='Use chosen flags/defaults without the setup questionnaire')
    args=parser.parse_args()
    if os.geteuid()==0:parser.error('Run as your desktop user, not root.')
    has_classes=(ROOT/'bin/classes').exists()
    has_packages=(ROOT/'bin/system-update').exists()
    sys.path.insert(0,str(ROOT/'bin'))
    import importlib
    ui_modules={name:importlib.import_module(module) for name,module,present in [('classes','studentdaily_ui',has_classes),('updates','keepitnew_ui',has_packages)] if present}
    nord_theme=next(iter(ui_modules.values()))
    interactive=sys.stdin.isatty() and not args.yes
    if interactive:
        print(app_name+' · customize installation')
        if has_classes and has_packages and args.components is None:
            args.components={'2':'classes','3':'packages'}.get(input('Apps: 1 Both, 2 StudentDaily, 3 KeepItNew [1]: ').strip(),'both')
        if args.bar=='auto':args.bar={'1':'noctalia','2':'waybar','3':'caelestia','4':'none'}.get(input('Bar: 1 Noctalia, 2 Waybar, 3 Caelestia, 4 No bar [1]: ').strip(),'noctalia')
        args.position={'1':'auto','2':'start','3':'center','4':'end'}.get(input('Widget position: 1 Default, 2 Start, 3 Center, 4 End [1]: ').strip(),'auto')
        if args.theme is None:
            names=list(nord_theme.THEMES)
            print('Themes: '+', '.join(f'{i+1} {name}' for i,name in enumerate(names)))
            choice=input('Theme number [1]: ').strip() or '1'
            if not choice.isdigit() or not 1<=int(choice)<=len(names):parser.error('Invalid theme number')
            args.theme=names[int(choice)-1]
        if args.opacity is None:
            try:args.opacity=float(input('Window opacity, 0.75–1 [0.94]: ').strip() or '.94')
            except ValueError:parser.error('Opacity must be numeric')
        args.no_aliases=input('Add convenient shell aliases? [Y/n]: ').strip().lower()=='n'
    if args.components=='classes':has_packages=False
    if args.components=='packages':has_classes=False
    if not has_classes and not has_packages:parser.error('Requested app is not included in this installer')
    if args.bar=='auto':args.bar=next((name for name in ('noctalia','waybar') if shutil.which(name)),'none')
    if args.bar=='caelestia':
        if args.caelestia_root is None and interactive:args.caelestia_root=Path(input('Editable Caelestia shell checkout path: ').strip()).expanduser()
        if args.caelestia_root is None:parser.error('--caelestia-root must point to an editable shell checkout')
        target=args.caelestia_root.expanduser()/'modules/bar/Bar.qml'
        if not target.is_file() or not os.access(target,os.W_OK):parser.error('Caelestia Bar.qml must exist and be writable')
    if interactive:
        if has_classes:
            args.no_reminders=input('Enable class reminders? [Y/n]: ').strip().lower()=='n'
            try:args.reminder_minutes=int(input('Minutes before class [5]: ').strip() or '5')
            except ValueError:parser.error('Reminder minutes must be numeric')
        if has_packages:
            args.no_checks=input('Check updates automatically? [Y/n]: ').strip().lower()=='n'
            try:args.check_minutes=int(input('Check interval in minutes [30]: ').strip() or '30')
            except ValueError:parser.error('Check interval must be numeric')
            args.confirm_updates=input('Confirm each package-manager transaction? [y/N]: ').strip().lower()=='y'
        args.no_start=input('Start enabled services now? [Y/n]: ').strip().lower()=='n'
    if args.theme is not None and args.theme not in nord_theme.THEMES:parser.error('Unknown theme')
    if args.opacity is not None and not .75<=args.opacity<=1:parser.error('Opacity must be between .75 and 1')
    if not 1<=args.reminder_minutes<=60 or not 5<=args.check_minutes<=1440:parser.error('Reminder minutes: 1–60; check minutes: 5–1440')
    needed=['python3','kitty','systemctl']+(['noctalia'] if args.bar=='noctalia' else [])+(['xdg-open'] if has_classes else [])+(['pacman'] if has_packages else [])
    missing=[app for app in needed if not shutil.which(app)]
    if missing:parser.error('Install required tools first: '+', '.join(missing))
    if sys.version_info<(3,11):parser.error('Python 3.11+ required')
    if has_classes and not args.no_reminders:
        try:
            import dbus
            from gi.repository import GLib
        except ImportError:parser.error('Install python-dbus and python-gobject for reminders, or use --no-reminders.')
    if has_packages and not (shutil.which('checkupdates') or shutil.which('fakeroot')):parser.error('Install pacman-contrib or fakeroot for update checks.')
    setup=args.setup or ('import' if args.preset else None)
    if has_classes and setup is None and interactive:
        print('StudentDaily setup: 1 Empty (edit later) · 2 Customize now · 3 Import a private preset')
        setup={'2':'customize','3':'import'}.get(input('Choose [1]: ').strip(),'blank')
    setup=setup or 'blank'
    preset=None
    if has_classes and setup=='import':
        path=args.preset or Path(input('Preset JSON path: ').strip()).expanduser()
        preset=json.loads(path.read_text())
        # Validate before modifying the installation.
        import runpy
        app=runpy.run_path(str(ROOT/'bin/classes'),run_name='installer_validation')
        app['validate_bundle'](preset)
        from zoneinfo import ZoneInfo
        for zone in preset.get('timezones',[]):ZoneInfo(zone['zone'])
    def copy(source,target):
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_symlink():target.unlink()
        shutil.copy2(source,target)
    included=(['classes','studentdaily_ui.py'] if has_classes else [])+(['system-update','keepitnew_ui.py'] if has_packages else [])
    for file in (ROOT/'bin').iterdir():
        if file.is_file() and file.name in included:
            copy(file,HOME/'.local/bin'/file.name);(HOME/'.local/bin'/file.name).chmod(0o755)
    for name,target,enabled in [('studentdaily','classes',has_classes),('keepitnew','system-update',has_packages)]:
        if enabled:
            link=HOME/'.local/bin'/name
            if link.is_symlink() or link.exists():link.unlink()
            link.symlink_to(target)
    for folder,target in [('plugins',DATA/'noctalia-plugins'),('services',CONFIG/'systemd/user')]:
        for file in (ROOT/folder).rglob('*'):
            if not file.is_file():continue
            if folder=='plugins' and (args.bar!='noctalia' or file.relative_to(ROOT/folder).parts[0] not in (['classes'] if has_classes else [])+(['updates'] if has_packages else [])):continue
            if folder=='services' and ((file.name.startswith('classes') and not has_classes) or (file.name.startswith('system-update') and not has_packages)):continue
            copy(file,target/file.relative_to(ROOT/folder))
    if has_classes:
        for alias in (() if args.no_aliases else ('class','today')):
            link=HOME/'.local/bin'/alias
            if link.exists() or link.is_symlink():link.unlink()
            link.symlink_to('classes')
        directory=CONFIG/'classes';directory.mkdir(parents=True,exist_ok=True)
        for name,value in [('schedule',preset['schedule'] if preset else {'version':2,'series':[],'exceptions':{}}),('timezones',preset.get('timezones',[]) if preset else [])]:
            path=directory/(name+'.json')
            if not path.exists():path.write_text(json.dumps(value,indent=2)+'\n');path.chmod(0o600)
        if preset and preset.get('tasks'):
            path=DATA/'classes/tasks.json';path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():path.write_text(json.dumps(preset['tasks'],indent=2)+'\n');path.chmod(0o600)
    if has_classes and preset and preset.get('completed'):
        path=DATA/'classes/completed.json';path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_text(json.dumps(preset['completed'])+'\n');path.chmod(0o600)
    if has_classes and preset and 'theme' in preset:
        module=ui_modules['classes']
        if not module.SETTINGS.exists():module.save(preset['theme'])
    selected_components=(['classes'] if has_classes else [])+(['updates'] if has_packages else [])
    for component in selected_components:
        module=ui_modules[component]
        preferences=dict(module.preferences());preferences.update(bar=args.bar)
        if component=='classes':preferences.update(reminders=not args.no_reminders,reminder_minutes=args.reminder_minutes)
        else:preferences.update(check_minutes=args.check_minutes,checks_enabled=not args.no_checks,auto_confirm=not args.confirm_updates)
        if args.opacity is not None:preferences['opacity']=args.opacity
        module._write_json(module.SETTINGS.parent/'preferences.json',preferences)
        if args.theme:module.save(args.theme)
    if has_packages:
        timer=CONFIG/'systemd/user/system-update-check.timer'
        import re
        timer.write_text(re.sub(r'OnUnitActiveSec=.*',f'OnUnitActiveSec={args.check_minutes}min',timer.read_text()))
        dropin=timer.parent/'system-update-check.timer.d/keepitnew.conf'
        if dropin.exists():dropin.write_text('[Timer]\nOnUnitActiveSec=\nOnUnitActiveSec='+str(args.check_minutes)+'min\n')
    environment=dict(os.environ,SUITE_BAR=args.bar,SUITE_POSITION=args.position,SUITE_ALIASES='0' if args.no_aliases else '1',SUITE_COMPONENTS=','.join((['classes'] if has_classes else [])+(['updates'] if has_packages else [])))
    if args.caelestia_root:environment['SUITE_CAELESTIA_ROOT']=str(args.caelestia_root.expanduser())
    if args.waybar_config:environment['SUITE_WAYBAR_CONFIG']=str(args.waybar_config.expanduser())
    subprocess.run([sys.executable,str(ROOT/'configure.py')],check=True,env=environment)
    subprocess.run(['systemctl','--user','daemon-reload'],check=True)
    units=(['classes-reminders.service'] if has_classes and not args.no_reminders else [])+(['system-update-check.timer'] if has_packages and not args.no_checks else [])
    disabled=(['classes-reminders.service'] if has_classes and args.no_reminders else [])+(['system-update-check.timer'] if has_packages and args.no_checks else [])
    for unit in disabled:subprocess.run(['systemctl','--user','disable','--now',unit],check=True)
    for unit in units:subprocess.run(['systemctl','--user','enable',unit],check=True)
    if not args.no_start:
        for key in ('WAYLAND_DISPLAY','DISPLAY','XDG_CURRENT_DESKTOP'):
            if os.environ.get(key):subprocess.run(['systemctl','--user','import-environment',key],check=True)
        for unit in units:subprocess.run(['systemctl','--user','restart',unit],check=True)
        if has_packages and not args.no_checks:subprocess.run(['systemctl','--user','start','--no-block','system-update-check.service'])
        for component in selected_components:ui_modules[component].reload_widgets()
    print('Installed. Open a new terminal for aliases. No keybindings were changed.')
    if has_classes and setup=='customize':
        subprocess.run([str(HOME/'.local/bin/classes'),'timezones'])
        subprocess.run([str(HOME/'.local/bin/classes'),'edit'])
    if has_classes:print('StudentDaily: Schedule edits classes and personal events; Zones edits clocks.')
    if has_packages:print('KeepItNew: run update; arrows/click select, Space toggles cleanup items.')

if __name__=='__main__':main()
