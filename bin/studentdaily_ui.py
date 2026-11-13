"""StudentDaily appearance, settings and widget helpers. No external dependencies."""
import json,os,tempfile
from pathlib import Path
from functools import lru_cache
APP='classes'
VERSION = '0.1.8'
APP_NAME='StudentDaily'
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
SETTINGS=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'classes/appearance.json'

# The default profile retains legacy paths; additional calendars are isolated.
PROFILE_ROOT=SETTINGS.parent
_PROFILE_CACHE={}

def profile_registry():
 path=PROFILE_ROOT/'profiles.json'
 import copy
 try:
  stat=path.stat();stamp=(str(path),stat.st_mtime_ns,stat.st_size,stat.st_ino)
  if _PROFILE_CACHE.get('stamp')==stamp:return copy.deepcopy(_PROFILE_CACHE['data'])
  data=json.loads(path.read_text())
 except FileNotFoundError:return {'active':'default','profiles':{'default':'My calendar'}}
 if not isinstance(data,dict) or not isinstance(data.get('profiles'),dict):raise ValueError('Invalid calendar registry')
 import re
 for identity,name in data['profiles'].items():
  if identity!='default' and not re.fullmatch(r'[a-f0-9]{32}',identity):raise ValueError('Invalid calendar ID')
  validate_profile_name(name)
 if 'default' not in data['profiles'] or not isinstance(data.get('active'),str) or data['active'] not in data['profiles']:raise ValueError('Missing active calendar')
 _PROFILE_CACHE.update(stamp=stamp,data=copy.deepcopy(data))
 return data

def validate_profile_name(name):
 if not isinstance(name,str) or not name.strip() or len(name)>60 or any(not c.isprintable() for c in name):raise ValueError('Use a calendar name of 1–60 printable characters')
 return name.strip()

def profile_directory(identity):
 if identity!='default':
  import re
  if not re.fullmatch(r'[a-f0-9]{32}',identity):raise ValueError('Invalid calendar ID')
 return PROFILE_ROOT if identity=='default' else PROFILE_ROOT/'profiles'/identity

PROFILE_ID=profile_registry()['active']
SETTINGS=profile_directory(PROFILE_ID)/'appearance.json'

def activate_profile(identity):
 global PROFILE_ID,SETTINGS
 if identity not in profile_registry()['profiles']:raise ValueError('Calendar no longer exists')
 PROFILE_ID=identity;SETTINGS=profile_directory(identity)/'appearance.json'
 _OPTIONS_CACHE.clear();_THEME_CACHE.clear()

def edit_profile_registry(change):
 import fcntl
 PROFILE_ROOT.mkdir(parents=True,exist_ok=True)
 with (PROFILE_ROOT/'profiles.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  data=profile_registry();change(data);_write_json(PROFILE_ROOT/'profiles.json',data)


CORE_ROLES=('background','text','accent','purple','dim','surface','green','red')
ROLE_LABELS={
 'background':'Window background','text':'Main text','accent':'Links and controls',
 'purple':'Secondary accent','dim':'Muted text','surface':'Surfaces',
 'green':'Success and timer','red':'Errors',
 'border':'Borders','heading':'Menu headings','selection_text':'Selected text',
 'selection_background':'Selected background','classes':'Class events',
 'personal':'Personal events','active':'Active class','progress':'Class progress',
 'task':'Pending tasks','task_done':'Completed tasks','notification':'Notification icon',
 'widget_idle':'Idle widget','widget_upcoming':'Upcoming widget','widget_active':'Active widget',
}
ROLE_DEFAULTS={'border':'accent','heading':'accent','selection_text':'text',
 'selection_background':'surface','classes':'text','personal':'purple','active':'green',
 'progress':'green','task':'text','task_done':'dim','notification':'accent',
 'widget_idle':'dim','widget_upcoming':'accent','widget_active':'green'}
_THEME_CACHE={}

def theme_names():return list(THEMES)+['Custom']

def appearance():
 try:
  stamp=(str(SETTINGS),SETTINGS.stat().st_mtime_ns)
  if _THEME_CACHE.get('stamp')!=stamp:
   data=json.loads(SETTINGS.read_text())
   _THEME_CACHE.update(stamp=stamp,data=data if isinstance(data,dict) else {})
  return dict(_THEME_CACHE.get('data',{}))
 except (OSError,ValueError):return {}

def current():
 name=appearance().get('theme','Nord')
 return name if isinstance(name,str) and name in theme_names() else 'Nord'

def validate_custom(data):
 import re
 if not isinstance(data,dict) or data.get('format')!='studentdaily-theme' or type(data.get('version')) is not int or data.get('version')!=1:
  raise ValueError('Choose a StudentDaily theme JSON file (version 1)')
 name=data.get('name','My theme')
 if not isinstance(name,str) or not name.strip() or len(name)>60 or any(ord(c)<32 or ord(c)==127 for c in name):
  raise ValueError('Use a theme name of 1–60 printable characters')
 colors=data.get('colors')
 if not isinstance(colors,dict) or not set(CORE_ROLES)<=set(colors) or set(colors)-set(ROLE_LABELS):
  raise ValueError('Theme has missing or unknown color roles')
 clean={}
 for role,color in colors.items():
  if not isinstance(color,str) or not re.fullmatch(r'#?[0-9a-fA-F]{6}',color):
   raise ValueError(ROLE_LABELS[role]+': use six hex digits, such as #88c0d0')
  clean[role]=color.lstrip('#').lower()
 for role,base in ROLE_DEFAULTS.items():clean.setdefault(role,clean[base])
 return {'format':'studentdaily-theme','version':1,'name':name.strip(),'colors':clean}

def make_custom(name=None):
 base=current() if name is None else name
 colors=palette(base)
 return validate_custom({'format':'studentdaily-theme','version':1,'name':'My theme','colors':colors})

def custom_theme():
 try:return validate_custom(appearance().get('custom'))
 except ValueError:return make_custom('Nord')

def palette(name=None):
 if isinstance(name,dict):return validate_custom(name)['colors']
 name=name or current()
 if name=='Custom':return custom_theme()['colors']
 return dict(zip(CORE_ROLES,THEMES[name]))

def role_color(role,fallback):
 colors=palette();return colors.get(role,colors[fallback])

def save(name):
 if name not in theme_names():raise ValueError('Unknown theme')
 data=appearance();data['theme']=name
 _write_json(SETTINGS,data)

def save_custom(data):
 custom=validate_custom(data);state=appearance();state.update(theme='Custom',custom=custom)
 _write_json(SETTINGS,state)

def read_theme(path):
 path=Path(path).expanduser()
 if path.stat().st_size>65536:raise ValueError('Theme file is too large (maximum 64 KB)')
 return validate_custom(json.loads(path.read_text()))

def export_theme(path,data=None,replace=False):
 path=Path(path).expanduser()
 if path.exists() and not replace:raise ValueError('File exists; choose another filename')
 _write_json(path,validate_custom(data if data is not None else custom_theme() if current()=='Custom' else make_custom()))

def contrast_ratio(a,b):
 def light(color):
  rgb=[int(color[i:i+2],16)/255 for i in (0,2,4)]
  rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
  return sum(v*w for v,w in zip(rgb,(.2126,.7152,.0722)))
 values=sorted((light(a),light(b)))
 return (values[1]+.05)/(values[0]+.05)


_COLOR_SESSION=0
_TERMINAL_PALETTE=None

from contextlib import contextmanager

@contextmanager
def terminal_session():
 """Keep app colors local to this terminal session and restore them on exit."""
 import sys
 global _COLOR_SESSION,_TERMINAL_PALETTE
 supported=sys.stdout.isatty() and bool(os.environ.get('KITTY_WINDOW_ID')) and not os.environ.get('TMUX')
 if supported:
  sys.stdout.write('\033]30001\033\\');sys.stdout.flush();_COLOR_SESSION+=1
 try:yield
 finally:
  if supported:
   sys.stdout.write('\033]30101\033\\');sys.stdout.flush();_COLOR_SESSION-=1;_TERMINAL_PALETTE=None

def run_screen(screen):
 import curses
 with terminal_session():return curses.wrapper(screen)

def kitty_launch_options():
 """Use an isolated app window; no global Kitty configuration is changed."""
 import uuid
 name=APP_NAME.lower()
 return ['-o','dynamic_background_opacity=yes','-o','allow_remote_control=socket-only',
         '--listen-on','unix:@'+name+'-'+uuid.uuid4().hex,
         '-o','env='+name.upper()+'_WINDOW=1']

def apply_opacity(value):
 import subprocess
 name=APP_NAME.lower();socket=os.environ.get('KITTY_LISTEN_ON','');window=os.environ.get('KITTY_WINDOW_ID','')
 if (os.environ.get(name.upper()+'_WINDOW')!='1' or not socket.startswith('unix:@'+name+'-') or not window.isdigit()):
  return 'Reopen from the widget or app launcher to apply opacity.'
 try:
  result=subprocess.run(['kitty','@','--to',socket,'set-background-opacity','--match','id:'+window,str(value)],
                        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=3)
  if result.returncode==0:return 'Opacity applied to this window.'
 except (OSError,subprocess.TimeoutExpired):pass
 return 'Opacity saved; reopen the app window to apply it.'

def terminal_palette(p):
 import sys
 global _TERMINAL_PALETTE
 stamp=(p['text'],p['background'])
 if _COLOR_SESSION and stamp!=_TERMINAL_PALETTE:
  sys.stdout.write('\033]21;foreground=#'+p['text']+';background=#'+p['background']+'\033\\');sys.stdout.flush()
  _TERMINAL_PALETTE=stamp

def curses_colors(curses,win,name=None,personal_role=None):
 p=palette(name);terminal_palette(p)
 custom='heading' in p
 if custom:p.update(accent=p['heading'],purple=p['personal'],surface=p['selection_background'])
 if personal_role in p:p['purple']=p[personal_role]
 try:
  # Define useful pairs even on terminals without mutable RGB colors.
  for pair,fg,bg in ((1,curses.COLOR_CYAN,-1),(2,curses.COLOR_WHITE,curses.COLOR_BLUE),
                     (3,curses.COLOR_WHITE,-1),(4,curses.COLOR_MAGENTA,-1),(5,curses.COLOR_WHITE,-1),(6,curses.COLOR_CYAN,-1),(7,curses.COLOR_RED,-1)):
   curses.init_pair(pair,fg,bg)
  if curses.can_change_color() and curses.COLORS>25:
   for i,key in enumerate(('accent','text','surface','background','purple','dim'),16):
    color=p[key];curses.init_color(i,*(round(int(color[n:n+2],16)*1000/255) for n in (0,2,4)))
   curses.init_pair(1,16,-1);curses.init_pair(2,17,18);curses.init_pair(3,17,-1);curses.init_pair(4,20,-1);curses.init_pair(5,21,-1)
   color=p['red'];curses.init_color(24,*(round(int(color[n:n+2],16)*1000/255) for n in (0,2,4)));curses.init_pair(7,24,-1)
   if custom:
    for i,role in ((22,'border'),(23,'selection_text')):
     color=p[role];curses.init_color(i,*(round(int(color[n:n+2],16)*1000/255) for n in (0,2,4)))
    curses.init_pair(6,22,-1);curses.init_pair(2,23,18)
  elif curses.COLORS>=256:
   def nearest(value):
    rgb=[int(value[i:i+2],16) for i in (0,2,4)]
    levels=(0,95,135,175,215,255)
    candidates=[(16+36*r+6*g+b,(levels[r],levels[g],levels[b])) for r in range(6) for g in range(6) for b in range(6)]
    candidates += [(232+i,(8+i*10,)*3) for i in range(24)]
    return min(candidates,key=lambda c:sum((a-b)**2 for a,b in zip(rgb,c[1])))[0]
   colors={key:nearest(value) for key,value in p.items()}
   for pair,fg,bg in ((1,'accent','background'),(2,'text','surface'),(3,'text','background'),(4,'purple','background'),(5,'dim','background')):
    curses.init_pair(pair,colors[fg],colors[bg] if pair==2 else -1)
   curses.init_pair(7,colors['red'],-1)
   if custom:
    curses.init_pair(6,colors['border'],-1);curses.init_pair(2,colors['selection_text'],colors['selection_background'])
  win.bkgd(' ',curses.color_pair(3))
 except curses.error:pass


def menu_frame(curses,win,app=None,values=None):
 """Square, theme-aware frame using the terminal's transparent background."""
 app=app or APP;values=values or options(app)
 h,w=win.getmaxyx()
 if h<5 or w<12:return
 style=values.get(app+'_border','single')
 edges={'single':('┌','┐','└','┘','─','│'),'double':('╔','╗','╚','╝','═','║'),'heavy':('┏','┓','┗','┛','━','┃'),'none':(' ',' ',' ',' ',' ',' ')}
 tl,tr,bl,br,line,side=frame(app,values)
 color=curses.color_pair(6 if values.get('_custom_colors') or current()=='Custom' else {'accent':1,'purple':4,'dim':5}.get(values.get(app+'_border_color'),1))
 def write(y,x,text):
  try:win.addnstr(y,x,text,max(0,w-x),color)
  except curses.error:pass
 write(0,0,tl+line*(w-2)+tr);write(h-1,0,bl+line*(w-2)+br)
 for y in range(1,h-1):
  write(y,0,side)
  try:win.addch(y,w-1,side,color)
  except curses.error:pass

def select_option(curses,win,title,choices,current):
 selected=next((i for i,(value,_) in enumerate(choices) if value==current),0);offset=0
 while True:
  curses_colors(curses,win,choices[selected][0] if title.lower()=='theme' else None);win.erase();h,w=win.getmaxyx();menu_frame(curses,win)
  def put(y,text,style=0):
   if 0<y<h-1:
    try:win.addnstr(y,2,text,max(0,w-4),style)
    except curses.error:pass
  put(1,title.upper(),curses.color_pair(1)|curses.A_BOLD)
  count=max(1,h-7);offset=min(offset,selected)
  if selected>=offset+count:offset=selected-count+1
  for i,(value,label) in enumerate(choices[offset:offset+count],offset):
   text=('› ' if i==selected else '  ')+label+('  ✓' if value==current else '')
   put(3+i-offset,text.ljust(max(0,w-4)),curses.color_pair(2) if i==selected else 0)
  put(h-3,'↑↓ Choose · Enter Apply to draft · Esc Cancel',curses.color_pair(1))
  win.refresh();key=win.getch()
  if key in (27,3):return current
  if key==curses.KEY_MOUSE:
   try:_,x,y,_,state=curses.getmouse()
   except curses.error:continue
   if state & curses.BUTTON4_PRESSED:key=curses.KEY_UP
   elif state & getattr(curses,'BUTTON5_PRESSED',0):key=curses.KEY_DOWN
   elif state & (curses.BUTTON1_CLICKED|curses.BUTTON1_PRESSED) and 3<=y<3+min(count,len(choices)-offset):return choices[offset+y-3][0]
   else:continue
  if key in (10,13,32):return choices[selected][0]
  if key in (curses.KEY_DOWN,9):selected=(selected+1)%len(choices)
  elif key in (curses.KEY_UP,curses.KEY_BTAB):selected=(selected-1)%len(choices)
  elif key in (curses.KEY_NPAGE,curses.KEY_PPAGE):selected=max(0,min(len(choices)-1,selected+(count if key==curses.KEY_NPAGE else -count)))

def picker():
 import curses
 names=theme_names()
 def screen(win):
  selected=names.index(current());offset=0
  curses.curs_set(0);win.keypad(True);curses.start_color();curses.use_default_colors()
  curses.init_pair(1,curses.COLOR_CYAN,-1);curses.init_pair(2,curses.COLOR_WHITE,curses.COLOR_BLUE)
  curses.mousemask(curses.ALL_MOUSE_EVENTS);curses.mouseinterval(0)
  while True:
   curses_colors(curses,win,names[selected]);win.erase();h,w=win.getmaxyx();menu_frame(curses,win)
   def put(y,text,style=0):
    if 0<=y<h-1:
     try:win.addnstr(y,2,text,max(0,w-4),style)
     except curses.error:pass
   put(1,'STUDENTDAILY / APPEARANCE',curses.color_pair(1))
   visible=max(1,h-7);offset=max(0,min(offset,selected))
   if selected>=offset+visible:offset=selected-visible+1
   for i,name in enumerate(names[offset:offset+visible]):put(3+i,('› ' if i+offset==selected else '  ')+name,curses.color_pair(2) if i+offset==selected else 0)
   hint='Enter Apply · C Custom · Esc Back' if w<70 else '↑↓ Preview · Enter Apply · C Custom colors · Esc Back'
   put(h-3,' '*max(0,(w-4-len(hint))//2)+hint,curses.color_pair(1))
   win.refresh();key=win.getch()
   if key in (27,ord('q')):return
   if key==ord('c'):
    if custom_editor(win,names[selected]):return
    continue
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
 run_screen(screen)

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
 color=personal_color() if kind=='personal' else role_color('notification','accent');cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'studentdaily-icons'
 cache.mkdir(parents=True,exist_ok=True);path=cache/(kind+'-'+color+'.svg')
 if not path.exists():
  # A monochrome vector stays clean at notification icon sizes.
  drawing='<rect x="12" y="16" width="40" height="36" rx="3"/><path d="M12 28h40M23 10v12M41 10v12M23 37h6m6 0h6m-18 8h6"/>'
  path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><g fill="none" stroke="#'+color+'" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'+drawing+'</g></svg>')
 return str(path)

def reload_widgets():
 import shutil,subprocess,tomllib
 backend=preferences().get('bar','noctalia')
 if backend=='noctalia' and shutil.which('noctalia'):
  data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
  manifest=data/'noctalia-plugins/classes/plugin.toml'
  try:
   plugin=tomllib.loads(manifest.read_text())['id']
   result=subprocess.run(['noctalia','config','export','full'],capture_output=True,text=True,timeout=10)
   enabled=tomllib.loads(result.stdout).get('plugins',{}).get('enabled',[]) if result.returncode==0 else []
   if plugin in enabled:
    stopped=subprocess.run(['noctalia','msg','plugins','disable',plugin],capture_output=True,timeout=10)
    if stopped.returncode==0:subprocess.run(['noctalia','msg','plugins','enable',plugin],capture_output=True,timeout=10)
  except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):pass
 elif backend=='waybar' and shutil.which('pkill'):
  subprocess.run(['pkill','-u',str(os.getuid()),'-RTMIN+8','-x','waybar'])
 # Caelestia polls fresh data; restart that shell after editing its QML component.


def waybar_status(data,kind):
 import html
 if data.get('visible') is False:return {'text':'','tooltip':'','class':'hidden'}
 color=data.get('color',data.get('glyphColor','#'+palette()['accent']))
 icon='▦'
 tips='\n'.join(' · '.join(str(v) for v in row if v) for row in data.get('tips',[]))
 text=f'<span foreground="{color}">{icon}</span>'
 if data.get('displayMode')=='always' or (kind=='classes' and data.get('expandUntil',0) and data.get('displayMode')!='icon'):text+=' '+html.escape(data.get('text',''))
 return {'text':text,'tooltip':html.escape(data.get('text','')+'\n'+tips),
         'class':kind,'percentage':data.get('classProgress') or 0}

# StudentDaily settings. Names are stable across installers.
@lru_cache(maxsize=2)
def settings_fields(app):
 if app!=APP:raise ValueError('Unknown app')
 def field(key,label,choices,default,help):return (key,label,choices,default,help)
 yes=[(True,'On'),(False,'Off')]
 fields=[
  field('theme','Theme',[(name,name) for name in theme_names()],'Nord','Applies to this app and its widget after Save.'),
  field('opacity','Window opacity',[(n/100,f'{n}%') for n in range(75,101)],.94,'Save updates opacity in app-launched Kitty windows. Older windows and other terminals need reopening from the widget or launcher.'),
  field(app+'_border','App borders',[(x,x.capitalize()) for x in ('single','double','ascii','none')],'single','Square terminal borders only; does not change desktop window decorations.'),
  field(app+'_border_color','Border color',[(x,label) for x,label in [('accent','Theme accent'),('purple','Secondary accent'),('dim','Muted')]],'accent','Built-in themes use this role. For Custom, edit Borders in Colors.'),
  field(app+'_widget','Bar widget',yes,True,'Hide or show this app’s installed widgets. Hidden widgets still poll so they can reappear.'),
  field(app+'_widget_mode','Widget text',[(x,label) for x,label in [('hover','On hover'),('always','Always'),('icon','Icon only')]],'hover','Noctalia and Waybar text. Caelestia keeps details in its tooltip.'),
  field(app+'_animation','Widget animation',[(x,x.capitalize()) for x in ('gentle','fast','off')],'gentle','Noctalia hover animation. Off reveals text immediately.'),
 ]
 fields += [
  field('classes_time_format','Clock format',[('24','24-hour · 15:30'),('12','12-hour · 3:30 PM')],'24','Display format for clocks, schedules, reminders and widget details. Event editing and stored times stay in 24-hour HH:MM.'),
  field('classes_clock_seconds','Clock seconds',yes,False,'Show seconds in the local and extra timezone clocks.'),
  field('classes_week_numbers','ISO week numbers',yes,False,'Show the ISO week number alongside the dashboard date.'),
  field('classes_teacher_details','Teacher details',yes,True,'Show teachers in schedule rows, widget tooltips and reminders. The Teachers page and event editor remain available.'),
  field('classes_default_duration','New event length',[(i,f'{i} min') for i in (15,20,30,45,60,90)],30,'Starting duration for new events. Existing events are unchanged.'),
  field('reminders','Event reminders',yes,True,'Applies to class and personal reminders; requires the installed reminder service.'),
  field('reminder_minutes','Reminder lead time',[(i,f'{i} min') for i in range(1,61)],5,'Remind before an event starts. Existing delivered reminders are not repeated.'),
  field('classes_auto_expand','Expand before event',yes,True,'Temporarily reveal the next event before it starts, except in Icon only mode.'),
  field('classes_progress','Progress indicator',yes,True,'Show active-event progress in the app and widgets.'),
  field('classes_personal_color','Personal-event color',[(x,label) for x,label in [('purple','Secondary accent'),('accent','Primary accent'),('green','Success accent')]],'purple','Built-in themes use this role, including notifications. For Custom, edit Personal events in Colors.'),
  field('classes_weekends','Weekend columns',[(x,label) for x,label in [('auto','When scheduled'),('hide','Hide'),('show','Always show')]],'auto','Controls the week view. Hidden weekend events still appear in Today and date navigation.'),
  field('classes_start_view','Opening view',[(x,label) for x,label in [('day','Today'),('week','Week'),('tasks','To-do')]],'day','Used the next time StudentDaily opens.'),
  field('classes_compact','Compact event rows',yes,False,'Hide secondary teacher/duration lines; keep titles, times and progress.'),
  field('classes_task_summary','Today’s task summary',yes,True,'Show your School and Life task summary below today’s events.'),
 ]
 return fields


_OPTIONS_CACHE={}
def options(app):
 saved=preferences();theme=current();cached=_OPTIONS_CACHE.get(app)
 if cached and cached[0] is saved and cached[1]==theme:return dict(cached[2])
 result={}
 for key,_,choices,default,_ in settings_fields(app):
  value=theme if key=='theme' else saved.get(key,default)
  if key=='opacity' and type(value) is int:value=float(value)
  result[key]=value if any(type(value)==type(candidate) and value==candidate for candidate,_ in choices) else default
 _OPTIONS_CACHE[app]=(saved,theme,result)
 return dict(result)


def frame(app,values=None):
 values=options(app) if values is None else values
 return {'single':('┌','┐','└','┘','─','│'),'double':('╔','╗','╚','╝','═','║'),
         'ascii':('+','+','+','+','-','|'),'none':(' ',' ',' ',' ',' ',' ')}[values.get(app+'_border','single')]


def border_color(app):return palette().get('border',palette()[options(app)[app+'_border_color']])
def personal_color():return palette().get('personal',palette()[options('classes')['classes_personal_color']])


def widget_options(app):
 prefs=options(app)
 return {'visible':prefs[app+'_widget'],'displayMode':prefs[app+'_widget_mode'],
         'animation':{'off':1,'fast':.45,'gentle':.22}[prefs[app+'_animation']]}


def _write_bytes(path,content):
 path.parent.mkdir(parents=True,exist_ok=True);temporary=None
 try:
  with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as file:
   temporary=Path(file.name);file.write(content)
  os.replace(temporary,path)
 finally:
  if temporary is not None:temporary.unlink(missing_ok=True)


def _write_json(path,data):
 _write_bytes(path,(json.dumps(data,indent=2)+'\n').encode())


def save_options(app,values):
 import fcntl,subprocess
 fields=settings_fields(app);valid={key:choices for key,_,choices,_,_ in fields}
 if set(values)!=set(valid):raise ValueError('Invalid settings fields')
 for key,value in values.items():
  if not any(type(value)==type(candidate) and value==candidate for candidate,_ in valid[key]):raise ValueError('Invalid '+key)
 path=SETTINGS.parent/'preferences.json';path.parent.mkdir(parents=True,exist_ok=True)
 with (path.parent/'settings.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  old=preferences().copy();merged=dict(old);merged.update({k:v for k,v in values.items() if k!='theme'})
  service_change=old.get('service_pending',False) or any(old.get(k,default)!=values[k] for k,default in [('reminders',True)])
  if service_change:merged['service_pending']=True
  theme_changed=values['theme']!=current();previous_theme=SETTINGS.read_bytes() if SETTINGS.exists() else None
  try:
   if theme_changed:save(values['theme'])
   _write_json(path,merged)
  except OSError:
   if theme_changed:
    if previous_theme is None:SETTINGS.unlink(missing_ok=True)
    else:_write_bytes(SETTINGS,previous_theme)
   raise
 opacity_note=apply_opacity(values['opacity']) if old.get('opacity',.94)!=values['opacity'] else ''
 if service_change:
  config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
  unit=config/'systemd/user/classes-reminders.service'
  if not unit.exists() and not (Path('/usr/lib/systemd/user')/unit.name).exists():return 'Settings saved. Install StudentDaily’s background service to apply scheduling.'
  try:
   commands=[['systemctl','--user','daemon-reload'],['systemctl','--user','enable' if values['reminders'] or len(profile_registry()['profiles'])>1 else 'disable','--now',unit.name]]
   for command in commands:
    result=subprocess.run(command,capture_output=True,text=True,timeout=15)
    if result.returncode:return 'Settings saved; service change failed: '+(result.stderr.strip() or 'systemctl error')[:120]
  except (OSError,subprocess.TimeoutExpired) as exc:return 'Settings saved; service change failed: '+str(exc)[:120]
  with (path.parent/'settings.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);merged=preferences().copy();merged['service_pending']=False;_write_json(path,merged)
 return 'Saved. '+opacity_note


def settings(app):
 """Interactive settings with explicit save and discard."""
 import curses,sys
 if not sys.stdin.isatty() or not sys.stdout.isatty():
  print('Open Settings in an interactive terminal.');return
 fields=settings_fields(app);name=APP_NAME
 def screen(win):
  draft=options(app);original=dict(draft);cursor=0;offset=0;notice=''
  curses.raw();curses.curs_set(0);win.keypad(True);curses.start_color();curses.use_default_colors()
  curses.mousemask(curses.ALL_MOUSE_EVENTS);curses.mouseinterval(0)
  def put(y,text,style=0):
   h,w=win.getmaxyx()
   if 0<=y<h-1:
    try:win.addnstr(y,2,text,max(0,w-4),style)
    except curses.error:pass
  def apply():
   nonlocal original,notice
   try:notice=save_options(app,draft);original=dict(draft)
   except (ValueError,OSError) as exc:notice='Not saved: '+str(exc)
  while True:
   curses_colors(curses,win,draft['theme']);win.erase();h,w=win.getmaxyx();menu_frame(curses,win,app,draft)
   if h<16 or w<48:
    put(1,'Resize to 48 columns × 16 rows. Esc returns.');win.refresh()
    if win.getch() in (27,3):return
    continue
   put(1,name.upper()+' / SETTINGS'+(' · unsaved' if draft!=original else ''),curses.color_pair(1)|curses.A_BOLD)
   tl,tr,bl,br,horiz,vert=frame(app)
   put(2,'Appearance · Widgets · Background services',curses.color_pair(5))
   put(3,'↑↓ Move · ←→ Adjust · Enter Options · C Colors',curses.color_pair(1))
   count=max(1,h-13);offset=min(offset,cursor)
   if cursor>=offset+count:offset=cursor-count+1
   for i,(key,label,choices,_,_) in enumerate(fields[offset:offset+count],offset):
    value=next(label for value,label in choices if draft[key]==value)
    label_width=max(12,min(25,w//3))
    shown=label if len(label)<=label_width else label[:label_width-1]+'…'
    line=('› ' if i==cursor else '  ')+shown.ljust(label_width)+f'  ‹ {value} ›'
    put(4+i-offset,line.ljust(max(0,w-4)),curses.color_pair(2) if i==cursor else 0)
   import textwrap
   for line,text in enumerate(textwrap.wrap(fields[cursor][1]+': '+fields[cursor][4],max(1,w-4))[:3]):put(h-7+line,text,curses.color_pair(1))
   put(h-4,notice or 'Theme colors preview here. Save applies; Esc discards.',curses.color_pair(7) if notice.startswith('Not saved:') else 0)
   labels=[('save','[ Save ]'),('colors','[ Colors ]'),('reset','[ Defaults ]'),('cancel','[ Back ]')]
   width=sum(len(label) for _,label in labels)+4;left=max(2,(w-width)//2);hits=[]
   for action,label in labels:
    try:win.addnstr(h-2,left,label,max(0,w-left-1),curses.color_pair(1)|curses.A_BOLD)
    except curses.error:pass
    hits.append((left,left+len(label),action));left+=len(label)+2
   win.refresh();key=win.getch();action=None
   if key==curses.KEY_MOUSE:
    try:_,x,y,_,state=curses.getmouse()
    except curses.error:continue
    if state & curses.BUTTON4_PRESSED:key=curses.KEY_UP
    elif state & getattr(curses,'BUTTON5_PRESSED',0):key=curses.KEY_DOWN
    elif state & (curses.BUTTON1_PRESSED|curses.BUTTON1_CLICKED):
     if y==h-2:action=next((a for lo,hi,a in hits if lo<=x<hi),None)
     elif 4<=y<4+min(count,len(fields)-offset):cursor=offset+y-4;key=10
     else:continue
    else:continue
   if key in (27,3,ord('q')) or action=='cancel':return
   if key==ord('c') or action=='colors':
    if custom_editor(win,draft['theme']):draft['theme']=current();original['theme']=current();notice='Custom theme saved.'
    continue
   if key==19 or action=='save':apply();continue
   if key==ord('r') or action=='reset':
    draft={key:default for key,_,_,default,_ in fields};notice='Defaults selected. Nothing changes until Save.';continue
   if key in (curses.KEY_DOWN,9):cursor=(cursor+1)%len(fields);notice=''
   elif key in (curses.KEY_UP,curses.KEY_BTAB):cursor=(cursor-1)%len(fields);notice=''
   elif key in (curses.KEY_NPAGE,curses.KEY_PPAGE):cursor=max(0,min(len(fields)-1,cursor+(count if key==curses.KEY_NPAGE else -count)))
   elif key in (curses.KEY_RIGHT,curses.KEY_LEFT,10,13,32):
    field,_,choices,_,_=fields[cursor];values=[value for value,_ in choices]
    if key in (10,13) and len(choices)>2:
     draft[field]=select_option(curses,win,fields[cursor][1],choices,draft[field]);notice='';continue
    step=5 if field=='check_minutes' else 1
    draft[field]=values[(values.index(draft[field])+(-step if key==curses.KEY_LEFT else step))%len(values)];notice=''
 try:run_screen(screen)
 except KeyboardInterrupt:pass


def color_prompt(curses,win,title,value=''):
 """Small editable field shared by color, name and file inputs."""
 text=value;replace=True
 while True:
  h,w=win.getmaxyx();win.erase();menu_frame(curses,win)
  for y,line in ((1,title),(3,text or ' '),(h-3,'Type or paste · Enter Accept · Esc Cancel · Ctrl+U Clear')):
   try:win.addnstr(y,2,line,max(1,w-4),curses.color_pair(1) if y!=3 else curses.color_pair(2))
   except curses.error:pass
  win.refresh();key=win.get_wch()
  if key in ('\x1b','\x03'):return None
  if key in ('\n','\r'):return text.strip()
  if key in (curses.KEY_BACKSPACE,'\x7f','\b'):text='' if replace else text[:-1];replace=False
  elif key=='\x15':text='';replace=False
  elif isinstance(key,str) and key.isprintable():text=key if replace else text+key;replace=False


def custom_editor(win,base=None):
 """Live custom colors with atomic saves; import and undo only modify the draft."""
 import curses,copy
 draft=custom_theme() if (base or current())=='Custom' else make_custom(base)
 baseline=copy.deepcopy(draft);undo=[];redo=[];cursor=0;offset=0;notice=''
 roles=list(ROLE_LABELS)
 def change(next_value):
  nonlocal draft
  next_value=validate_custom(next_value)
  if next_value!=draft:undo.append(copy.deepcopy(draft));redo.clear();draft=next_value
 def put(y,text,style=0):
  h,w=win.getmaxyx()
  if 0<=y<h-1:
   try:win.addnstr(y,2,text,max(0,w-4),style)
   except curses.error:pass
 while True:
  curses_colors(curses,win,draft);win.erase();h,w=win.getmaxyx();menu_frame(curses,win,values={**options(APP),'_custom_colors':True})
  if h<16 or w<48:
   put(1,'Resize to 48 columns × 16 rows. Esc cancels.');win.refresh()
   if win.getch() in (27,3):return False
   continue
  put(1,'CUSTOM COLORS / '+draft['name']+(' *' if draft!=baseline else ''),curses.color_pair(1)|curses.A_BOLD)
  put(2,'Enter Edit hex · N Name · U Undo · Y Redo · R Reset color',curses.color_pair(5))
  count=max(1,h-10);offset=min(offset,cursor)
  if cursor>=offset+count:offset=cursor-count+1
  for i,role in enumerate(roles[offset:offset+count],offset):
   color=draft['colors'][role];line=('› ' if i==cursor else '  ')+ROLE_LABELS[role].ljust(23)+' #'+color
   put(4+i-offset,line,curses.color_pair(2) if i==cursor else 0)
   try:
    pair=40+i
    if curses.can_change_color() and curses.COLORS>64 and curses.COLOR_PAIRS>64:
     curses.init_color(32+i,*(round(int(color[n:n+2],16)*1000/255) for n in (0,2,4)))
     curses.init_pair(pair,32+i,-1)
     win.addstr(4+i-offset,w-6,'██',curses.color_pair(pair))
   except curses.error:pass
  p=draft['colors'];ratio=contrast_ratio(p['text'],p['background']);selected=contrast_ratio(p['selection_text'],p['selection_background'])
  put(h-5,f'Contrast: text {ratio:.1f}:1 · selected {selected:.1f}:1'+(' · low contrast' if min(ratio,selected)<4.5 else ''),curses.color_pair(5))
  put(h-4,notice or 'Preview only. Save applies to this app and its widget.',curses.color_pair(7) if notice.startswith('Error:') else 0)
  labels=[('save','Save'),('import','Import'),('export','Export'),('base','Base'),('back','Back')]
  width=sum(len(label)+4 for _,label in labels);left=max(2,(w-width)//2);hits=[]
  for action,label in labels:
   text='[ '+label+' ]'
   try:win.addnstr(h-2,left,text,max(0,w-left-1),curses.color_pair(1))
   except curses.error:pass
   hits.append((left,left+len(text),action));left+=len(text)
  win.refresh();key=win.getch();action=None
  if key==curses.KEY_MOUSE:
   try:_,x,y,_,state=curses.getmouse()
   except curses.error:continue
   if state & curses.BUTTON4_PRESSED:key=curses.KEY_UP
   elif state & getattr(curses,'BUTTON5_PRESSED',0):key=curses.KEY_DOWN
   elif state & (curses.BUTTON1_PRESSED|curses.BUTTON1_CLICKED):
    if y==h-2:action=next((a for lo,hi,a in hits if lo<=x<hi),None)
    elif 4<=y<4+min(count,len(roles)-offset):cursor=offset+y-4;key=10
    else:continue
  if key in (27,3) or action=='back':return False
  try:
   if key==19 or action=='save':save_custom(draft);return True
   if key in (curses.KEY_DOWN,9):cursor=(cursor+1)%len(roles)
   elif key in (curses.KEY_UP,curses.KEY_BTAB):cursor=(cursor-1)%len(roles)
   elif key in (curses.KEY_NPAGE,curses.KEY_PPAGE):cursor=max(0,min(len(roles)-1,cursor+(count if key==curses.KEY_NPAGE else -count)))
   elif key in (10,13):
    role=roles[cursor];value=color_prompt(curses,win,ROLE_LABELS[role]+' / #RRGGBB','#'+draft['colors'][role])
    if value is not None:
     next_value=copy.deepcopy(draft);next_value['colors'][role]=value;change(next_value);notice=''
   elif key==ord('n'):
    value=color_prompt(curses,win,'THEME NAME',draft['name'])
    if value is not None:change(dict(draft,name=value))
   elif key in (ord('u'),26) and undo:redo.append(copy.deepcopy(draft));draft=undo.pop()
   elif key in (ord('y'),25) and redo:undo.append(copy.deepcopy(draft));draft=redo.pop()
   elif key==ord('r'):
    next_value=copy.deepcopy(draft);next_value['colors'][roles[cursor]]=baseline['colors'][roles[cursor]];change(next_value)
   elif key==ord('b') or action=='base':
    name=select_option(curses,win,'Copy preset',[(name,name) for name in THEMES]+[('cancel','Cancel')],'cancel')
    if name!='cancel':change(make_custom(name));notice='Preset copied into draft; edit any color.'
   elif key==ord('i') or action=='import':
    path=color_prompt(curses,win,'IMPORT THEME / JSON PATH')
    if path:change(read_theme(path));notice='Imported into preview. Save to apply.'
   elif key==ord('e') or action=='export':
    path=color_prompt(curses,win,'EXPORT THEME / JSON PATH',str(Path.home()/'Downloads/studentdaily-theme.json'))
    if path:export_theme(path,draft);notice='Theme exported. No schedule or personal data included.'
  except (ValueError,OSError,TypeError) as exc:notice='Error: '+str(exc)

# App releases are separate from operating-system package updates.
def release_version(value):
 import re
 match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',str(value))
 if not match:raise ValueError('Unsupported release version')
 return tuple(map(int,match.groups()))


def release_download(url,limit):
 from urllib.request import Request,urlopen
 from urllib.error import HTTPError,URLError
 try:
  with urlopen(Request(url,headers={'User-Agent':APP_NAME+' updater','Accept':'application/vnd.github+json' if '/api.github.com/' in url else 'application/octet-stream'}),timeout=20) as response:
   data=response.read(limit+1)
  if len(data)>limit:raise ValueError('Release download exceeds the size limit')
  return data
 except HTTPError as exc:
  if exc.code in (403,429):raise ValueError('GitHub rate limit reached. Try again later.') from exc
  if exc.code==404:raise ValueError('No published release is available yet.') from exc
  raise ValueError('GitHub returned HTTP '+str(exc.code)) from exc
 except (URLError,TimeoutError) as exc:raise ValueError('Could not reach GitHub. Check your connection and try again.') from exc


def latest_app_release():
 app=APP_NAME.lower();repo='JudokaCube/'+app
 data=json.loads(release_download('https://api.github.com/repos/'+repo+'/releases/latest',2*1024*1024))
 if not isinstance(data,dict) or data.get('draft') or data.get('prerelease'):raise ValueError('No stable release is available')
 tag=data.get('tag_name','');version=release_version(tag)
 if version<=release_version(VERSION):return None
 filename=app+'-installer-'+'.'.join(map(str,version))+'.tar.gz'
 base='https://github.com/'+repo+'/releases/download/'+tag+'/'
 assets={item.get('name'):item.get('browser_download_url') for item in data.get('assets',[]) if isinstance(item,dict)}
 for name in (filename,'SHA256SUMS'):
  if assets.get(name)!=base+name:raise ValueError('Release is missing its verified installer download')
 body=data.get('body') or 'No release notes were provided.'
 if not isinstance(body,str):raise ValueError('Invalid release notes')
 # Display text only, never terminal escape sequences from remote notes.
 body=''.join(c for c in body if c in '\n\t' or c.isprintable())[:30000]
 return {'version':'.'.join(map(str,version)),'notes':body,'filename':filename,'archive':assets[filename],'checksums':assets['SHA256SUMS']}


def app_update_method(executable):
 import shutil,subprocess
 app=APP_NAME.lower();path=Path(executable).resolve()
 command='classes' if APP=='classes' else 'system-update'
 if path==Path.home()/'.local/bin'/command:
  return {'kind':'local','description':'Update this app and installed widget code. Calendars, settings and bar layout stay unchanged.'}
 if shutil.which('pacman'):
  try:
   result=subprocess.run(['pacman','-Qqo',str(path)],capture_output=True,text=True,timeout=5)
   if result.returncode==0 and result.stdout.strip()==app:
    helper=next((shutil.which(name) for name in ('paru','yay') if shutil.which(name)),None)
    if helper:return {'kind':'package','command':[helper,'-Syu','--noconfirm',app], 'description':'Package-managed install: '+Path(helper).name+' will perform a full system upgrade, including this app. Your password may be requested. The new app version must also be available in your package sources.'}
    return {'kind':'manual','description':'This app is package-managed. Update it with your package manager; install yay or paru to launch that upgrade here.'}
  except (OSError,subprocess.TimeoutExpired):pass
 return {'kind':'manual','description':'This is a source checkout or custom install. Update it from its original source; the app will not overwrite development files.'}


def app_release_payload(release):
 import io,tarfile,hashlib,ast,re
 expected=None
 for line in release_download(release['checksums'],1024*1024).decode().splitlines():
  parts=line.split()
  if len(parts)==2 and parts[1].lstrip('*')==release['filename']:
   if not re.fullmatch(r'[a-fA-F0-9]{64}',parts[0]):raise ValueError('Invalid release checksum')
   expected=parts[0].lower()
 if expected is None:raise ValueError('Installer checksum is missing')
 blob=release_download(release['archive'],64*1024*1024)
 if hashlib.sha256(blob).hexdigest()!=expected:raise ValueError('Checksum mismatch. Nothing was installed.')
 files={};total=0
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:
  for member in archive:
   parts=Path(member.name).parts
   if not parts or member.name.startswith('/') or '..' in parts or member.issym() or member.islnk():raise ValueError('Unsafe installer archive')
   if member.isdir():continue
   if not member.isfile():raise ValueError('Unsupported installer archive entry')
   total+=member.size
   if total>128*1024*1024:raise ValueError('Unpacked release is too large')
   name='/'.join(parts[1:])
   if not name or name in files:raise ValueError('Invalid installer archive layout')
   files[name]=archive.extractfile(member).read()
 app=APP_NAME.lower();command='classes' if APP=='classes' else 'system-update'
 for name in ('bin/'+command,'bin/'+app+'_ui.py'):
  if name not in files:raise ValueError('Installer is missing app files')
  ast.parse(files[name].decode())
 values={}
 for node in ast.parse(files['bin/'+app+'_ui.py'].decode()).body:
  if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('VERSION','APP_NAME'):
   values[node.targets[0].id]=ast.literal_eval(node.value)
 if values.get('VERSION')!=release['version'] or values.get('APP_NAME')!=APP_NAME:raise ValueError('Installer app/version does not match this release')
 return files


def install_local_app_release(release,executable):
 import fcntl,stat
 if app_update_method(executable)['kind']!='local':raise ValueError('This installation must be updated through its original installer or package manager')
 app=APP_NAME.lower();command='classes' if APP=='classes' else 'system-update'
 cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/app;cache.mkdir(parents=True,exist_ok=True)
 with (cache/'app-update.lock').open('a') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise ValueError('An app update is already running')
  files=app_release_payload(release)
  config=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))
  data=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))
  targets=[(Path(executable).resolve(),files['bin/'+command],0o755),(Path(executable).resolve().parent/(app+'_ui.py'),files['bin/'+app+'_ui.py'],0o644)]
  plugin=data/'noctalia-plugins'/APP
  if plugin.is_dir():
   for name in ('plugin.toml','bar.luau'):
    key='plugins/'+APP+'/'+name
    if key in files:targets.append((plugin/name,files[key],0o644))
  units=['classes-reminders.service'] if APP=='classes' else ['system-update-check.service','system-update-check.timer']
  for name in units:
   path=config/'systemd/user'/name
   if path.exists() and 'services/'+name in files:targets.append((path,files['services/'+name],0o644))
  # Setup records an optional copied Caelestia component, without changing Bar.qml.
  manifest=data/app/'installation.json';info={}
  if manifest.exists():
   info=json.loads(manifest.read_text())
   if not isinstance(info,dict):raise ValueError('Invalid installation record')
   value=info.get('caelestia_widget')
   if value:
    path=Path(value);key='integrations/caelestia/'+APP_NAME+'Widget.qml'
    if path.name!=APP_NAME+'Widget.qml' or path.parent.name!=app:raise ValueError('Invalid installed widget location')
    if path.is_file() and key in files:targets.append((path,files[key],0o644))
  info.update(method='local',version=release['version'])
  targets.append((manifest,(json.dumps(info,indent=2)+'\n').encode(),0o600))
  originals=[]
  for path,content,mode in targets:
   if path.is_symlink():raise ValueError('Refusing to replace a symlink: '+str(path))
   originals.append((path,path.read_bytes() if path.exists() else None,stat.S_IMODE(path.stat().st_mode) if path.exists() else mode))
  try:
   for path,content,mode in targets:
    _write_bytes(path,content);path.chmod(mode)
  except BaseException:
   for path,content,mode in originals:
    if content is None:path.unlink(missing_ok=True)
    else:_write_bytes(path,content);path.chmod(mode)
   raise
 return 'Installed '+release['version']+'. Restart the app to load it.'


def app_update_dialog(title,body,choices):
 """Scrollable release notes with visible, mouse-accessible Yes/No controls."""
 import curses,textwrap
 def screen(win):
  curses.curs_set(0);win.keypad(True);curses.start_color();curses.use_default_colors();curses.mousemask(curses.ALL_MOUSE_EVENTS)
  offset=0;selected=0
  while True:
   curses_colors(curses,win);win.erase();h,w=win.getmaxyx();menu_frame(curses,win)
   def put(y,x,text,style=0):
    if 0<=y<h-1:
     try:win.addnstr(y,x,text,max(0,w-x-2),style)
     except curses.error:pass
   if h<12 or w<40:
    put(1,1,'Enlarge window; Esc cancels.');win.refresh()
    if win.getch() in (27,ord('q')):return None
    continue
   put(1,2,title,curses.color_pair(1)|curses.A_BOLD)
   lines=[line for part in body.splitlines() for line in (textwrap.wrap(part,max(1,w-6)) or [''])]
   visible=h-8;offset=min(max(0,offset),max(0,len(lines)-visible))
   for i,line in enumerate(lines[offset:offset+visible]):put(3+i,3,line)
   put(h-4,2,'↑↓ Scroll · Tab/←→ Choose · Enter Select · Esc Cancel',curses.color_pair(5))
   labels=['[ '+label+' ]' for _,label in choices];left=max(2,(w-sum(map(len,labels))-2*(len(labels)-1))//2);hits=[]
   for i,label in enumerate(labels):
    put(h-2,left,label,curses.color_pair(2 if i==selected else 1));hits.append((left,left+len(label),i));left+=len(label)+2
   win.refresh();key=win.getch()
   if key in (27,ord('q'),3):return None
   if key in (10,13):return choices[selected][0]
   if key in (9,curses.KEY_RIGHT,curses.KEY_LEFT):selected=(selected+(-1 if key==curses.KEY_LEFT else 1))%len(choices)
   elif key in (curses.KEY_DOWN,ord('j')):offset+=1
   elif key in (curses.KEY_UP,ord('k')):offset-=1
   elif key in (curses.KEY_NPAGE,curses.KEY_PPAGE):offset+=visible if key==curses.KEY_NPAGE else -visible
   elif key==curses.KEY_MOUSE:
    try:_,x,y,_,state=curses.getmouse()
    except curses.error:continue
    if state & curses.BUTTON4_PRESSED:offset-=3
    elif state & getattr(curses,'BUTTON5_PRESSED',0):offset+=3
    elif y==h-2 and state & (curses.BUTTON1_CLICKED|curses.BUTTON1_PRESSED):
     for start,end,i in hits:
      if start<=x<end:return choices[i][0]
 return run_screen(screen)


def app_update_wait(title,operation):
 import curses,threading,queue
 results=queue.Queue()
 def worker():
  try:results.put((True,operation()))
  except Exception as exc:results.put((False,exc))
 threading.Thread(target=worker,daemon=True).start()
 def screen(win):
  curses.raw();curses.curs_set(0);win.timeout(150);win.keypad(True);curses.start_color();curses.use_default_colors();tick=0
  while True:
   try:return results.get_nowait()
   except queue.Empty:pass
   curses_colors(curses,win);win.erase();h,w=win.getmaxyx();menu_frame(curses,win)
   for y,text in ((2,title),(4,'Please wait'+'.'*(tick%4)),(6,'Downloads have a timeout. App updates never run in the background.')):
    if y<h-1:
     try:win.addnstr(y,2,text,max(0,w-4),curses.color_pair(1))
     except curses.error:pass
   win.refresh();win.getch();tick+=1
 ok,result=run_screen(screen)
 if not ok:raise ValueError(str(result)) from result
 return result


def check_app_updates(executable):
 import sys,subprocess
 if not sys.stdin.isatty() or not sys.stdout.isatty():
  print('Open Check for app updates in an interactive terminal.');return False
 try:
  release=app_update_wait('CHECKING '+APP_NAME.upper(),latest_app_release)
  if release is None:
   app_update_dialog(APP_NAME+' '+VERSION,'You already have the latest stable release.',[('back','Back')]);return False
  method=app_update_method(executable)
  body='Installed: '+VERSION+'   Available: '+release['version']+'\n\n'+method['description']+'\n\nWHAT’S NEW\n'+release['notes']
  choices=[('no','No, not now'),('yes','Yes, install')] if method['kind']!='manual' else [('no','Back')]
  if app_update_dialog('UPDATE '+APP_NAME.upper(),body,choices)!='yes':return False
  if method['kind']=='local':
   message=app_update_wait('INSTALLING '+APP_NAME.upper(),lambda:install_local_app_release(release,executable))
   try:
    result=subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True,timeout=15)
    if result.returncode:message+=' Background services may need a session restart.'
    if APP=='classes':subprocess.run(['systemctl','--user','try-restart','classes-reminders.service'],capture_output=True,timeout=15)
    reload_widgets()
   except (OSError,subprocess.TimeoutExpired):message+=' Restart your desktop session to reload background services and widgets.'
   if preferences().get('bar')=='caelestia':message+=' Restart Caelestia to load updated widget code.'
  else:
   result=subprocess.run(method['command'])
   if result.returncode:raise ValueError('Package manager did not finish successfully. Your installed files remain package-managed.')
   message='Package upgrade finished. If this release is not yet packaged, your package manager may have kept the previous version.'
  return app_update_dialog('APP UPDATE COMPLETE',message,[('later','Later'),('restart','Restart app')])=='restart'
 except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as exc:
  app_update_dialog('APP UPDATE FAILED',str(exc),[('back','Back')]);return False
