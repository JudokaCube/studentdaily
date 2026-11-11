"""Shared theme data and live-preview picker. No external dependencies."""
import json,os,tempfile
from pathlib import Path
THEMES={
 'Nord':('2e3440','eceff4','88c0d0','b48ead','a3b1c6','434c5e','a3be8c','bf616a'),
 'Catppuccin Mocha':('1e1e2e','cdd6f4','89b4fa','cba6f7','a6adc8','45475a','a6e3a1','f38ba8'),
 'Tokyo Night':('1a1b26','c0caf5','7aa2f7','bb9af7','9aa5ce','292e42','9ece6a','f7768e'),
 'Gruvbox Dark':('282828','ebdbb2','83a598','d3869b','a89984','504945','b8bb26','fb4934'),
 'Dracula':('282a36','f8f8f2','8be9fd','bd93f9','a4a5b8','44475a','50fa7b','ff5555'),
 'Rose Pine':('191724','e0def4','9ccfd8','c4a7e7','908caa','403d52','31748f','eb6f92'),
 'Solarized Dark':('002b36','93a1a1','2aa198','6c71c4','839496','073642','859900','dc322f'),
 'Solarized Light':('fdf6e3','586e75','268bd2','6c71c4','657b83','eee8d5','859900','dc322f'),
 'High Contrast':('000000','ffffff','00ffff','ff88ff','dddddd','333333','00ff00','ff7777'),
}
SETTINGS=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'nord-desktop/appearance.json'

_THEME_CACHE={}
def current():
 try:
  stamp=(str(SETTINGS),SETTINGS.stat().st_mtime_ns)
  if _THEME_CACHE.get('stamp')!=stamp:_THEME_CACHE.update(stamp=stamp,name=json.loads(SETTINGS.read_text()).get('theme','Nord'))
  name=_THEME_CACHE['name']
 except (OSError,ValueError,AttributeError):name='Nord'
 return name if isinstance(name,str) and name in THEMES else 'Nord'

def palette(name=None):return dict(zip(('background','text','accent','purple','dim','surface','green','red'),THEMES[name or current()]))

def save(name):
 if name not in THEMES:raise ValueError('Unknown theme')
 SETTINGS.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=SETTINGS.parent,delete=False) as f:
  json.dump({'theme':name},f);path=f.name
 os.replace(path,SETTINGS)

def curses_colors(curses,win,name=None):
 p=palette(name)
 try:
  # Define useful pairs even on terminals without mutable RGB colors.
  for pair,fg,bg in ((1,curses.COLOR_CYAN,-1),(2,curses.COLOR_WHITE,curses.COLOR_BLUE),
                     (3,curses.COLOR_WHITE,-1),(4,curses.COLOR_MAGENTA,-1)):
   curses.init_pair(pair,fg,bg)
  if curses.can_change_color() and curses.COLORS>21:
   for i,key in enumerate(('accent','text','surface','background','purple'),16):
    color=p[key];curses.init_color(i,*(round(int(color[n:n+2],16)*1000/255) for n in (0,2,4)))
   curses.init_pair(1,16,19);curses.init_pair(2,17,18);curses.init_pair(3,17,19);curses.init_pair(4,20,19)
  elif curses.COLORS>=256:
   def nearest(value):
    rgb=[int(value[i:i+2],16) for i in (0,2,4)]
    levels=(0,95,135,175,215,255)
    candidates=[(16+36*r+6*g+b,(levels[r],levels[g],levels[b])) for r in range(6) for g in range(6) for b in range(6)]
    candidates += [(232+i,(8+i*10,)*3) for i in range(24)]
    return min(candidates,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c[1])))[0]
   colors={key:nearest(value) for key,value in p.items()}
   for pair,fg,bg in ((1,'accent','background'),(2,'text','surface'),(3,'text','background'),(4,'purple','background')):
    curses.init_pair(pair,colors[fg],colors[bg])
  win.bkgd(' ',curses.color_pair(3))
 except curses.error:pass

def picker():
 import curses
 names=list(THEMES)
 def screen(win):
  selected=names.index(current());offset=0
  curses.curs_set(0);win.keypad(True);curses.start_color();curses.use_default_colors()
  curses.init_pair(1,curses.COLOR_CYAN,-1);curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_BLUE)
  curses.mousemask(curses.ALL_MOUSE_EVENTS);curses.mouseinterval(0)
  while True:
   curses_colors(curses,win,names[selected]);win.erase();h,w=win.getmaxyx()
   def put(y,text,style=0):
    if 0<=y<h-1:
     try:win.addnstr(y,2,text,max(0,w-4),style)
     except curses.error:pass
   put(1,'APPEARANCE / shared by both apps and widgets',curses.color_pair(1))
   visible=max(1,h-7);offset=max(0,min(offset,selected))
   if selected>=offset+visible:offset=selected-visible+1
   for i,name in enumerate(names[offset:offset+visible]):put(3+i,('› ' if i+offset==selected else '  ')+name,curses.color_pair(2) if i+offset==selected else 0)
   hint='Enter Apply · N Nord · Esc Back' if w<70 else '↑↓ Preview · Enter/click Apply · N Nord · Esc Back'
   put(h-3,' '*max(0,(w-4-len(hint))//2)+hint,curses.color_pair(1))
   win.refresh();key=win.getch()
   if key in (27,ord('q')):return
   if key in (10,13):save(names[selected]);return
   if key==ord('n'):save('Nord');return
   if key in (curses.KEY_DOWN,ord('j')):selected=min(len(names)-1,selected+1)
   elif key in (curses.KEY_UP,ord('k')):selected=max(0,selected-1)
   elif key==curses.KEY_MOUSE:
    try:_,x,y,_,state=curses.getmouse()
    except curses.error:continue
    if state & curses.BUTTON4_PRESSED:selected=max(0,selected-1)
    elif state & getattr(curses,'BUTTON5_PRESSED',0):selected=min(len(names)-1,selected+1)
    elif state & (curses.BUTTON1_CLICKED|curses.BUTTON1_PRESSED) and 3<=y<3+min(visible,len(names)-offset):
     save(names[offset+y-3]);return
 curses.wrapper(screen)

_PREF_CACHE={}
def preferences():
 path=SETTINGS.parent/'preferences.json'
 try:
  stamp=(str(path),path.stat().st_mtime_ns)
  if _PREF_CACHE.get('stamp')!=stamp:_PREF_CACHE.update(stamp=stamp,data=json.loads(path.read_text()))
  return _PREF_CACHE['data'] if isinstance(_PREF_CACHE['data'],dict) else {}
 except (OSError,ValueError):return {}

def opacity():
 try:return min(1,max(.75,float(preferences().get('opacity',.94))))
 except (TypeError,ValueError):return .94

def notification_icon(kind='calendar'):
 color=palette()['purple' if kind=='personal' else 'accent'];cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'studentdaily-icons'
 cache.mkdir(parents=True,exist_ok=True);path=cache/(kind+'-'+color+'.svg')
 if not path.exists():
  # A monochrome vector stays clean at notification icon sizes.
  drawing='<rect x="12" y="16" width="40" height="36" rx="3"/><path d="M12 28h40M23 10v12M41 10v12M23 37h6m6 0h6m-18 8h6"/>'
  path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><g fill="none" stroke="#'+color+'" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'+drawing+'</g></svg>')
 return str(path)

def reload_widgets():
 import shutil,subprocess
 backend=preferences().get('bar','noctalia')
 if backend=='noctalia' and shutil.which('noctalia'):subprocess.run(['noctalia','msg','config-reload'],stdout=subprocess.DEVNULL)
 elif backend=='waybar' and shutil.which('pkill'):subprocess.run(['pkill','-u',str(os.getuid()),'-RTMIN+8','-x','waybar'])
 # Caelestia QML polls fresh app data; changing shell QML itself requires a shell restart.

def waybar_status(data,kind):
 import html
 color=data.get('color',data.get('glyphColor','#'+palette()['accent']))
 icon='▦' if kind=='classes' else '▣'
 tips='\n'.join(' · '.join(str(v) for v in row if v) for row in data.get('tips',[]))
 text=f'<span foreground="{color}">{icon}</span>'
 if kind=='classes' and data.get('expandUntil',0):text+=' '+html.escape(data.get('text',''))
 return {'text':text,'tooltip':html.escape(data.get('text','')+'\n'+tips),
         'class':kind,'percentage':data.get('classProgress') or 0}
