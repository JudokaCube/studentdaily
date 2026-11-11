#!/usr/bin/env python3
"""Configure aliases and Noctalia while preserving unrelated settings."""
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

USER_HOME=Path.home()
CONFIG=Path(os.environ.get('XDG_CONFIG_HOME',USER_HOME/'.config'))
STATE=Path(os.environ.get('XDG_STATE_HOME',USER_HOME/'.local/state'))
DATA=Path(os.environ.get('XDG_DATA_HOME',USER_HOME/'.local/share'))

def table_update(text,table,values):
    # Change only keys in the exact table, leaving all other settings untouched.
    match=re.search(r'(?m)^\['+re.escape(table)+r'\]\s*$',text)
    if not match:
        return text+'\n['+table+']\n'+''.join(f'{k} = {v}\n' for k,v in values.items())
    begin=match.end()
    end_match=re.search(r'(?m)^\[',text[begin:])
    end=begin+end_match.start() if end_match else len(text)
    body=text[begin:end]
    for key,value in values.items():
        pattern=r'(?m)^\s*'+re.escape(key)+r'\s*=\s*(?:\[[\s\S]*?\]|[^\n]*)\n?'
        body=re.sub(pattern,'',body)
        body+='\n'+key+' = '+value+'\n'
    return text[:match.start()]+'['+table+']\n'+body.lstrip('\n')+'\n'+text[end:]


def jsonc(text):
    # Remove comments and trailing commas only outside quoted strings.
    result=[];i=0;quoted=False
    while i<len(text):
        ch=text[i]
        if quoted:
            result.append(ch)
            if ord(ch)==92 and i+1<len(text):i+=1;result.append(text[i])
            elif ch=='"':quoted=False
        elif ch=='"':quoted=True;result.append(ch)
        elif text[i:i+2]=='//':
            end=text.find('\n',i);i=len(text) if end<0 else end;continue
        elif text[i:i+2]=='/*':
            end=text.find('*/',i+2)
            if end<0:raise ValueError('Unclosed JSONC comment')
            i=end+2;continue
        elif ch==',':
            j=i+1
            while j<len(text) and text[j].isspace():j+=1
            if j<len(text) and text[j] in '}]':i+=1;continue
            result.append(ch)
        else:result.append(ch)
        i+=1
    clean=''.join(result)
    pattern=r'("(?:\\.|[^"\\])*")|,\s*(?=[}\]])'
    return json.loads(re.sub(pattern,lambda match:match.group(1) or '',clean))


def configure_alternative(root,components,backend):
    if backend=='none':return
    if backend=='waybar':
        directory=CONFIG/'waybar';directory.mkdir(parents=True,exist_ok=True)
        requested=os.environ.get('SUITE_WAYBAR_CONFIG')
        path=Path(requested).expanduser() if requested else next((directory/n for n in ('config.jsonc','config') if (directory/n).exists()),directory/'config.jsonc')
        current=jsonc(path.read_text()) if path.exists() else {'layer':'top','modules-left':[],'modules-center':[],'modules-right':[]}
        bars=current if isinstance(current,list) else [current]
        definitions=json.loads((root/'integrations/waybar/config.json').read_text())
        for bar in bars:
            for component in components:
                key='custom/studentdaily' if component=='classes' else 'custom/keepitnew'
                for section in ('modules-left','modules-center','modules-right'):
                    if section in bar:bar[section]=[x for x in bar[section] if x!=key]
                section=os.environ.get('SUITE_POSITION','auto')
                section={'start':'modules-left','center':'modules-center','end':'modules-right'}.get(section,'modules-center' if component=='classes' else 'modules-left')
                entries=bar.setdefault(section,[]);index=entries.index('clock') if 'clock' in entries else 0
                entries.insert(index,key);bar[key]=definitions[key]
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(current,indent=2)+'\n')
        css=directory/'suite.css';css.write_text((root/'integrations/waybar/style.css').read_text())
        style=directory/'style.css';text=style.read_text() if style.exists() else ''
        if '@import "suite.css";' not in text:style.write_text('@import "suite.css";\n'+text)
        print('Waybar modules configured. Restart Waybar to load newly added modules.')
    elif backend=='caelestia':
        shell=Path(os.environ['SUITE_CAELESTIA_ROOT']).expanduser()
        bar=shell/'modules/bar/Bar.qml'
        text=bar.read_text()
        if 'ColumnLayout {' not in text or 'Repeater {' not in text:raise ValueError('Unsupported Caelestia Bar.qml layout')
        destination=bar.parent/'studentdaily-keepitnew';destination.mkdir(exist_ok=True)
        import shutil
        shutil.copy2(root/'integrations/caelestia/AppWidget.qml',destination/'AppWidget.qml')
        if 'import "studentdaily-keepitnew" as Suite' not in text:
            index=text.index('import QtQuick');text=text[:index]+'import "studentdaily-keepitnew" as Suite\n'+text[index:]
        for component in components:
            begin='    // BEGIN SUITE '+component;end='    // END SUITE '+component
            text=re.sub(re.escape(begin)+r'.*?'+re.escape(end)+r'\n?','',text,flags=re.S)
            fragment=begin+'\n    Suite.AppWidget { app: "'+component+'"; Layout.alignment: Qt.AlignHCenter }\n'+end+'\n\n'
            index=text.index('    Repeater {');text=text[:index]+fragment+text[index:]
        bar.write_text(text)
        print('Caelestia editable checkout configured. Restart that shell instance to load widgets.')


def configure_aliases(components):
    for component in components:
        pairs=[('classes','classes'),('class','classes'),('today','classes')] if component=='classes' else [('update','system-update')]
        tag='NORD '+component.upper()
        for shell,rc in [('zsh',USER_HOME/'.zshrc'),('bash',USER_HOME/'.bashrc')]:
            if shell=='bash' and not rc.exists():continue
            content=rc.read_text() if rc.exists() else ''
            content=re.sub(r'(?ms)^# BEGIN '+tag+r'\n.*?^# END '+tag+r'\n?','',content)
            content+='\n# BEGIN '+tag+'\nexport PATH="$HOME/.local/bin:$PATH"\n'
            for alias,target in pairs:
                content+=f'unalias {alias} 2>/dev/null || true\n'
                content+=('unfunction ' if shell=='zsh' else 'unset -f ')+alias+' 2>/dev/null || true\n'
                content+=f'alias {alias}=\'"$HOME/.local/bin/{target}"\'\n'
            content+='# END '+tag+'\n';rc.write_text(content)


def main():
    root=Path(__file__).resolve().parent
    components=[name for name in ('classes','updates') if (root/'plugins'/name).exists()]
    components=[c for c in components if c in os.environ.get('SUITE_COMPONENTS','classes,updates').split(',')]
    backend=os.environ.get('SUITE_BAR','noctalia')
    if backend!='noctalia':
        configure_alternative(root,components,backend)
        if os.environ.get('SUITE_ALIASES','1')!='0':configure_aliases(components)
        return
    definitions={'classes':('classes','center'),'updates':('system-updates','start')}
    config_dir=Path(os.environ.get('NOCTALIA_CONFIG_HOME',CONFIG))/'noctalia'
    state_dir=Path(os.environ.get('NOCTALIA_STATE_HOME',STATE))/'noctalia'
    config_dir.mkdir(parents=True,exist_ok=True);state_dir.mkdir(parents=True,exist_ok=True)
    current=tomllib.loads(subprocess.check_output(['noctalia','config','export','full'],text=True))
    bar=current.get('bar',{}).get('default',{})
    owned=[definitions[c][0] for c in components]
    arrays={key:[x for x in bar.get(key,default) if x not in owned] for key,default in [('start',['wallpaper','workspaces']),('center',['clock']),('end',[])]}
    for component in components:
        widget,location=definitions[component]
        position=os.environ.get('SUITE_POSITION','auto')
        if position in arrays:location=position
        values=arrays[location]
        if component=='classes':values.insert(values.index('clock') if 'clock' in values else 0,widget)
        else:values.insert(values.index('wallpaper')+1 if 'wallpaper' in values else 0,widget)
        plugin='nord-desktop/'+component
        (config_dir/('nord-'+component+'.toml')).write_text(f'[widget.{widget}]\ntype = "{plugin}:bar"\ncapsule = false\nshow_tooltip = true\n')
    enabled=list(current.get('plugins',{}).get('enabled',[]))
    for component in components:
        plugin='nord-desktop/'+component
        if plugin not in enabled:enabled.append(plugin)
    settings=state_dir/'settings.toml';text=settings.read_text() if settings.exists() else ''
    text=table_update(text,'bar.default',{key:json.dumps(value) for key,value in arrays.items()})
    text=table_update(text,'plugins',{'enabled':json.dumps(enabled)})
    sources=current.get('plugins',{}).get('source',[])
    sources=[x for x in sources if x.get('name')!='nord-desktop-local']
    sources.append({'name':'nord-desktop-local','kind':'path','location':str(DATA/'noctalia-plugins'),'enabled':True})
    text=re.sub(r'(?ms)^\s*\[\[plugins\.source\]\].*?(?=^\s*\[|\Z)','',text)
    for source in sources:
        text+='\n[[plugins.source]]\n'+''.join(f'{k} = {json.dumps(v)}\n' for k,v in source.items())
    tomllib.loads(text);settings.write_text(text)
    if os.environ.get('SUITE_ALIASES','1')!='0':configure_aliases(components)
    subprocess.run(['noctalia','config','validate'],check=True)

if __name__=='__main__':main()
