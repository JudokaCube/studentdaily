#!/usr/bin/env python3
"""Prepare an individual Arch/AUR package without installing or publishing it."""
import argparse,gzip,hashlib,io,re,shutil,subprocess,tarfile,tempfile,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PROJECTS={
 'studentdaily':dict(component='classes',executable='classes',module='studentdaily_ui',unit='classes-reminders.service',description='Class and personal-event organizer with reminders and desktop widgets',depends=['python>=3.11','kitty','systemd','xdg-utils','tzdata','python-dbus','python-gobject','libnotify'],optional=['waybar: optional desktop bar','quickshell: optional Caelestia widget','qt6-declarative: optional Caelestia QML integration'],launch='pin',icon='x-office-calendar'),
 'keepitnew':dict(component='updates',executable='system-update',module='keepitnew_ui',unit='system-update-check.timer',description='Arch, AUR and Flatpak update dashboard and disk cleanup',depends=['python>=3.11','kitty','systemd','pacman','fakeroot','sudo'],optional=['flatpak: optional Flatpak updates and cleanup','pacman-contrib: update checks and package-cache cleanup','yay: AUR updates','paru: alternative AUR helper','waybar: optional desktop bar','quickshell: optional Caelestia widget','qt6-declarative: optional Caelestia QML integration'],launch='--open',icon='system-software-update')
}

def main():
    available=[name for name,info in PROJECTS.items() if (ROOT/'bin'/info['executable']).exists()]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',choices=available,default=available[0] if len(available)==1 else None)
    parser.add_argument('--version',required=True)
    parser.add_argument('--pkgrel',type=int,default=1)
    parser.add_argument('--verify-source',action='store_true',help='Download the public source URL and verify it matches the generated archive')
    parser.add_argument('--project-url',default='')
    parser.add_argument('--source-url',default='')
    parser.add_argument('--output',type=Path,default=ROOT/'arch-build')
    args=parser.parse_args()
    if args.pkgrel<1:parser.error('--pkgrel must be positive')
    if args.verify_source and not args.source_url:parser.error('--verify-source requires --source-url')
    if args.app is None:parser.error('Choose one app with --app; no combined Arch package is produced')
    if not re.fullmatch(r'[0-9][A-Za-z0-9._+]*',args.version):parser.error('Use a numeric-starting version without spaces or shell characters')
    for url in (args.project_url,args.source_url):
        if url and (not url.startswith('https://') or any(c.isspace() or c in "'\"`$\\" for c in url)):parser.error('Use a plain HTTPS URL')
    if args.source_url and not args.project_url:parser.error('--project-url is required with --source-url')
    app=args.app;info=PROJECTS[app];out=args.output.expanduser()/app;out.mkdir(parents=True,exist_ok=True)
    versioned=app+'-'+args.version;filename=versioned+'.tar.gz'
    with tempfile.TemporaryDirectory() as temp:
        tree=Path(temp)/versioned;(tree/'bin').mkdir(parents=True)
        for name in (info['executable'],info['module']+'.py'):shutil.copy2(ROOT/'bin'/name,tree/'bin'/name)
        module=tree/'bin'/(info['module']+'.py')
        module.write_text(re.sub(r'^VERSION\s*=.*$','VERSION = '+repr(args.version),module.read_text(),flags=re.M))
        shutil.copytree(ROOT/'plugins'/info['component'],tree/'plugins'/info['component'])
        (tree/'integrations/waybar').mkdir(parents=True);(tree/'integrations/caelestia').mkdir()
        import json
        defs=json.loads((ROOT/'integrations/waybar/config.json').read_text())
        key='custom/'+app
        (tree/'integrations/waybar/config.json').write_text(json.dumps({key:defs[key]},indent=2)+'\n')
        css=(ROOT/'integrations/waybar/style.css').read_text()
        (tree/'integrations/waybar/style.css').write_text('\n'.join(line for line in css.splitlines() if '#'+key.replace('/','-') in line)+'\n')
        qml=('StudentDaily' if app=='studentdaily' else 'KeepItNew')+'Widget.qml'
        shutil.copy2(ROOT/'integrations/caelestia'/qml,tree/'integrations/caelestia'/qml)
        (tree/'services').mkdir()
        for unit in (ROOT/'services').iterdir():
            if unit.name.startswith('classes' if app=='studentdaily' else 'system-update'):shutil.copy2(unit,tree/'services'/unit.name)
        shutil.copy2(ROOT/'LICENSE',tree/'LICENSE')
        (tree/'README.md').write_text('# '+app+'\n\n'+info['description']+'.\n\nRun `'+app+'` to open the app. Run `'+app+'-setup --help` for optional desktop integration. Settings are available inside the app.\n\nMIT · jdkcube\n')
        shutil.copy2(ROOT/'packaging/configure.py',tree/'configure.py')
        replacements={'APP':app,'VERSION':args.version,'DESCRIPTION':info['description'],'MODULE':info['module'],'COMPONENT':info['component'],'EXECUTABLE':info['executable'],'UNIT':info['unit'],'PKGREL':str(args.pkgrel),'PROJECT_URL':args.project_url or 'https://github.com/JudokaCube/'+app}
        setup=(ROOT/'packaging/aur/setup.py.in').read_text()
        for key,value in replacements.items():setup=setup.replace('@'+key+'@',value)
        (tree/'setup.py').write_text(setup)
        (tree/(app+'.desktop')).write_text('[Desktop Entry]\nType=Application\nName='+('StudentDaily' if app=='studentdaily' else 'KeepItNew')+'\nExec='+app+' '+info['launch']+'\nIcon='+info['icon']+'\nComment='+info['description']+'\nTerminal=false\nCategories='+('Education;' if app=='studentdaily' else 'System;')+'\n')
        with (out/filename).open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w') as archive:
            for path in sorted(tree.rglob('*')):
                if path.is_file():
                    content=path.read_bytes();entry=tarfile.TarInfo(str(Path(versioned)/path.relative_to(tree)));entry.size=len(content);entry.mode=0o755 if path.name==info['executable'] else 0o644
                    archive.addfile(entry,io.BytesIO(content))
    replacements.update(SOURCE=(filename+'::'+args.source_url) if args.source_url else filename,SHA256=hashlib.sha256((out/filename).read_bytes()).hexdigest(),DEPENDS=' '.join(repr(v) for v in info['depends']),OPTDEPENDS=' '.join(repr(v) for v in info['optional']))
    verified=False
    if args.verify_source:
        digest=hashlib.sha256()
        with urllib.request.urlopen(args.source_url,timeout=30) as response:
            while chunk:=response.read(1024*1024):digest.update(chunk)
        if digest.hexdigest()!=replacements['SHA256']:parser.error('Published archive differs from this source tree; do not submit these checksums')
        verified=True
    (out/'SHA256SUMS').write_text(replacements['SHA256']+'  '+filename+'\n')
    (out/'release.json').write_text(json.dumps({'app':app,'version':args.version,'pkgrel':args.pkgrel,'license':'MIT','project_url':replacements['PROJECT_URL'],'source_url':args.source_url or None,'source_verified':verified,'sha256':replacements['SHA256']},indent=2)+'\n')
    recipe=(ROOT/'packaging/aur/PKGBUILD.in').read_text()
    for key,value in replacements.items():recipe=recipe.replace('@'+key+'@',value)
    (out/'PKGBUILD').write_text(recipe)
    result=subprocess.run(['makepkg','--printsrcinfo'],cwd=out,capture_output=True,text=True,check=True)
    (out/'.SRCINFO').write_text(result.stdout)
    print('Prepared',app,'in',out)
    if not verified:print('Local candidate only. Publish the source archive and pass --verify-source before AUR submission.')
if __name__=='__main__':main()
