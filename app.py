import os,json,sqlite3,secrets,hashlib,hmac,time,re,math
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
ROOT=Path(__file__).parent
DB=os.environ.get('DATABASE_PATH',str(ROOT/'data.sqlite3'))
MODULES={'disputes','support','privacy','identity','credit-building','banking','tax','business','bills','complaints','applications','connections','fraud-alerts','freeze'}
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
def init():
 with connect() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,name TEXT,country TEXT,currency TEXT,status TEXT DEFAULT 'active');
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,tenant TEXT,email TEXT UNIQUE,name TEXT,password TEXT,role TEXT,status TEXT DEFAULT 'active');
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user TEXT,expires INTEGER,csrf TEXT);
CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,tenant TEXT,user TEXT,module TEXT,title TEXT,body TEXT,status TEXT,created INTEGER);
CREATE TABLE IF NOT EXISTS offers(id TEXT PRIMARY KEY,tenant TEXT,category TEXT,title TEXT,body TEXT,url TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,tenant TEXT,actor TEXT,action TEXT,created INTEGER);
CREATE TABLE IF NOT EXISTS consents(user TEXT,version TEXT,created INTEGER);
CREATE TABLE IF NOT EXISTS providers(id TEXT PRIMARY KEY,tenant TEXT,name TEXT,status TEXT);
''')
  c.execute("INSERT OR IGNORE INTO tenants(id,name,country,currency) VALUES('africa-credit','Africa Credit','NG','NGN')")
def password(p,salt=None):
 salt=salt or secrets.token_hex(16);return salt+':'+hashlib.scrypt(p.encode(),salt=salt.encode(),n=16384,r=8,p=1).hex()
def valid(p,stored):return hmac.compare_digest(password(p,stored.split(':')[0]),stored)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def send(self,status,data,headers=None):
  raw=json.dumps(data).encode();self.send_response(status)
  for k,v in {'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff',**(headers or {})}.items():self.send_header(k,v)
  self.end_headers();self.wfile.write(raw)
 def body(self):
  n=int(self.headers.get('Content-Length',0))
  if n>65536:raise ValueError('Request too large')
  data=json.loads(self.rfile.read(n) or b'{}')
  if not isinstance(data,dict):raise ValueError('JSON object required')
  return data
 def user(self):
  ck=SimpleCookie();ck.load(self.headers.get('Cookie',''));token=ck['session'].value if 'session' in ck else ''
  with connect() as c:
   r=c.execute('SELECT u.*,s.csrf FROM sessions s JOIN users u ON u.id=s.user JOIN tenants t ON t.id=u.tenant WHERE s.token=? AND s.expires>? AND u.status=? AND t.status=?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()),'active','active')).fetchone()
  return dict(r) if r else None
 def do_GET(self):
  path=self.path.split('?')[0]
  if path=='/health':return self.send(200,{'status':'ok','service':'africa-credit'})
  if path=='/api/setup':
   with connect() as c:return self.send(200,{'required':not bool(c.execute("SELECT 1 FROM users WHERE role='superadmin'").fetchone())})
  if path.startswith('/api/'):
   u=self.user()
   if not u:return self.send(401,{'error':'Sign in required'})
   with connect() as c:
    if path=='/api/me':return self.send(200,{k:v for k,v in u.items() if k!='password'})
    if path=='/api/overview':
     return self.send(200,{'credit':None,'provider_status':'not_connected','records':[dict(x) for x in c.execute('SELECT * FROM records WHERE tenant=? AND user=? ORDER BY created DESC',(u['tenant'],u['id']))],'offers':[dict(x) for x in c.execute("SELECT * FROM offers WHERE tenant=? AND status='published'",(u['tenant'],))]})
    if path=='/api/admin' and u['role'] in ('superadmin','tenantadmin'):
     scope='' if u['role']=='superadmin' else ' WHERE tenant=?';args=() if not scope else (u['tenant'],)
     return self.send(200,{'users':[dict(x) for x in c.execute('SELECT id,tenant,email,name,role,status FROM users'+scope,args)],'records':[dict(x) for x in c.execute('SELECT * FROM records'+scope,args)],'offers':[dict(x) for x in c.execute('SELECT * FROM offers'+scope,args)],'audit':[dict(x) for x in c.execute('SELECT * FROM audit'+scope+' ORDER BY id DESC LIMIT 100',args)],'tenants':[dict(x) for x in c.execute('SELECT * FROM tenants'+('' if u['role']=='superadmin' else ' WHERE id=?'),args)]})
   return self.send(404,{'error':'Not found'})
  f=ROOT/'static'/('index.html' if path=='/' or path=='/admin' else path.lstrip('/'))
  if not f.resolve().is_relative_to((ROOT/'static').resolve()) or not f.is_file():return self.send(404,{'error':'File not found'})
  import mimetypes
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(str(f))[0] or 'application/octet-stream');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'");self.end_headers();self.wfile.write(f.read_bytes())
 def do_POST(self):
  try:self.post()
  except (ValueError,KeyError,json.JSONDecodeError) as e:self.send(400,{'error':str(e)})
  except sqlite3.IntegrityError:self.send(409,{'error':'Record already exists'})
 def post(self):
  d=self.body();path=self.path;now=int(time.time());u=self.user()
  with connect() as c:
   if path in ('/api/register','/api/setup'):
    if len(d.get('password',''))<12:raise ValueError('Use at least 12 password characters')
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',d.get('email','')):raise ValueError('Valid email required')
    role='user'
    if path=='/api/setup':
     expected=os.environ.get('SETUP_TOKEN','')
     if not expected or not hmac.compare_digest(expected,d.get('token','')):return self.send(403,{'error':'Server setup token required'})
     c.execute('BEGIN IMMEDIATE')
     if c.execute("SELECT 1 FROM users WHERE role='superadmin'").fetchone():return self.send(409,{'error':'Setup complete'})
     role='superadmin'
    if not d.get('consent'):raise ValueError('Terms and privacy consent required')
    uid=secrets.token_hex(12);c.execute('INSERT INTO users(id,tenant,email,name,password,role) VALUES(?,?,?,?,?,?)',(uid,'africa-credit',d['email'].lower().strip(),d.get('name','Member')[:100],password(d['password']),role));c.execute('INSERT INTO consents VALUES(?,?,?)',(uid,'2026-10-20',now));return self.send(201,{'message':'Account created. Sign in.'})
   if path=='/api/login':
    # Persistent rate limit by hashed IP, no plaintext credentials in logs.
    key=hashlib.sha256((self.client_address[0]+d.get('email','')).encode()).hexdigest()
    attempts=c.execute("SELECT COUNT(*) FROM audit WHERE actor=? AND action='login_failed' AND created>?",(key,now-900)).fetchone()[0]
    if attempts>=10:return self.send(429,{'error':'Try again in 15 minutes'})
    r=c.execute('SELECT * FROM users WHERE email=? AND status=?',(d.get('email','').lower().strip(),'active')).fetchone()
    if not r or not valid(d.get('password',''),r['password']):
     c.execute('INSERT INTO audit(tenant,actor,action,created) VALUES(?,?,?,?)',('',key,'login_failed',now));c.commit();return self.send(401,{'error':'Invalid credentials'})
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24);c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),r['id'],now+28800,csrf));secure='; Secure' if os.environ.get('COOKIE_SECURE','1')=='1' else '';return self.send(200,{'csrf':csrf},{'Set-Cookie':f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})
   if not u:return self.send(401,{'error':'Sign in required'})
   if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),u['csrf']):return self.send(403,{'error':'Invalid CSRF token'})
   if path=='/api/logout':
    c.execute('DELETE FROM sessions WHERE user=?',(u['id'],));return self.send(200,{'message':'Signed out'},{'Set-Cookie':'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
   if path=='/api/records':
    if d['module'] not in MODULES:raise ValueError('Unknown module')
    title=d.get('title','').strip();body=d.get('body','').strip()
    if not title or not body:raise ValueError('Title and details required')
    rid=secrets.token_hex(12);c.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?)',(rid,u['tenant'],u['id'],d['module'],title[:200],body[:12000],'received',now));action='request:'+d['module'];message='Request saved. Provider actions require an authorized connected service.'
   elif path.startswith('/api/admin/') and u['role'] in ('superadmin','tenantadmin'):
    action=path.rsplit('/',1)[1];message='Saved'
    if action=='tenant' and u['role']=='superadmin':
     tid=d['id'];
     if not re.fullmatch('[a-z0-9-]{3,50}',tid):raise ValueError('Invalid tenant identifier')
     c.execute('INSERT INTO tenants(id,name,country,currency) VALUES(?,?,?,?)',(tid,d['name'],d.get('country','NG'),d.get('currency','NGN')))
    elif action=='offer':
     url=d.get('url','')
     if not url.startswith('https://'):raise ValueError('HTTPS partner URL required')
     tenant=d.get('tenant',u['tenant']) if u['role']=='superadmin' else u['tenant']
     if not c.execute("SELECT 1 FROM tenants WHERE id=? AND status='active'",(tenant,)).fetchone():raise ValueError('Active tenant required')
     c.execute('INSERT INTO offers VALUES(?,?,?,?,?,?,?)',(secrets.token_hex(12),tenant,d['category'],d['title'][:200],d['body'][:4000],url,'published'))
    elif action=='case':
     if d['status'] not in ('received','in_review','awaiting_information','resolved','closed'):raise ValueError('Invalid status')
     c.execute('UPDATE records SET status=? WHERE id=?'+('' if u['role']=='superadmin' else ' AND tenant=?'),(d['status'],d['id'])+(() if u['role']=='superadmin' else (u['tenant'],)))
    elif action=='user':
     if d['status'] not in ('active','suspended'):raise ValueError('Invalid status')
     if d['id']==u['id']:raise ValueError('Cannot suspend yourself')
     c.execute("UPDATE users SET status=? WHERE id=? AND role='user'"+('' if u['role']=='superadmin' else ' AND tenant=?'),(d['status'],d['id'])+(() if u['role']=='superadmin' else (u['tenant'],)))
    else:return self.send(403,{'error':'Action unavailable'})
   else:return self.send(404,{'error':'Not found'})
   c.execute('INSERT INTO audit(tenant,actor,action,created) VALUES(?,?,?,?)',(u['tenant'],u['id'],action,now));return self.send(200,{'message':message})
if __name__=='__main__':
 init();ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'),int(os.environ.get('PORT','18840'))),Handler).serve_forever()
