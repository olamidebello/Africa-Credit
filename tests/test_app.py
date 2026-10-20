import unittest,tempfile,os,threading,json,http.client,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class Access(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();app.DB=cls.tmp.name+'/test.db';os.environ['SETUP_TOKEN']='test-server-token';os.environ['COOKIE_SECURE']='0';app.init();cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);threading.Thread(target=cls.server.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
 def req(self,path,data=None,cookie='',csrf=''):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port);c.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,{'Content-Type':'application/json','Cookie':cookie,'X-CSRF-Token':csrf});r=c.getresponse();raw=r.read();status=r.status;headers=dict(r.getheaders());c.close();return status,json.loads(raw),headers
 def test_access_and_tenant_isolation(self):
  self.assertEqual(self.req('/api/admin')[0],401)
  d={'email':'admin@example.com','name':'Admin','password':'long-test-password','consent':True,'token':'wrong'}
  self.assertEqual(self.req('/api/setup',d)[0],403);d['token']='test-server-token';self.assertEqual(self.req('/api/setup',d)[0],201);self.assertEqual(self.req('/api/setup',d)[0],409)
  _,v,h=self.req('/api/login',d);cookie=h['Set-Cookie'].split(';')[0];csrf=v['csrf']
  self.assertEqual(self.req('/api/admin/tenant',{'id':'tenant-b','name':'Second'},cookie)[0],403)
  self.assertEqual(self.req('/api/admin/tenant',{'id':'tenant-b','name':'Second'},cookie,csrf)[0],200)
  u={'email':'user@example.com','name':'Member','password':'another-long-password','consent':True};self.assertEqual(self.req('/api/register',u)[0],201)
  _,v,h=self.req('/api/login',u);uc=h['Set-Cookie'].split(';')[0];ut=v['csrf']
  self.assertEqual(self.req('/api/admin',None,uc)[0],404)
  self.assertEqual(self.req('/api/admin/tenant',{'id':'illegal','name':'No'},uc,ut)[0],404)
  self.assertEqual(self.req('/api/records',{'module':'disputes','title':'Accuracy','body':'Review this item'},uc,ut)[0],200)
  with app.connect() as c:c.execute("INSERT INTO records VALUES('secret','tenant-b','someone','disputes','Secret','Other tenant','received',1)")
  _,overview,_=self.req('/api/overview',None,uc);self.assertEqual(len(overview['records']),1);self.assertIsNone(overview['credit']);self.assertEqual(overview['records'][0]['tenant'],'africa-credit')
  self.assertEqual(self.req('/api/logout',{},uc,ut)[0],200);self.assertEqual(self.req('/api/me',None,uc)[0],401)
 def test_password(self):
  p=app.password('abcdefghijkl');self.assertTrue(app.valid('abcdefghijkl',p));self.assertFalse(app.valid('bad',p))
