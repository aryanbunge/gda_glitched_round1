from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import base64, json, csv, io, threading, datetime, os

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'submissions.json'
STATE_FILE=ROOT/'test_state.json'
FULLSCREEN_FILE=ROOT/'fullscreen_events.json'
CONFIG=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
LOCK=threading.Lock()
def is_test_open():
    try: return bool(json.loads(STATE_FILE.read_text(encoding='utf-8')).get('open',False))
    except (OSError,json.JSONDecodeError): return False
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,fmt,*args): print('%s - %s'%(self.address_string(),fmt%args))
    def admin_ok(self):
        hdr=self.headers.get('Authorization','')
        try:
            scheme,token=hdr.split(' ',1)
            user,pw=base64.b64decode(token).decode().split(':',1)
            return scheme.lower()=='basic' and user=='admin' and pw==str(CONFIG['admin_password'])
        except Exception: return False
    def require_admin(self):
        if not self.admin_ok():
            self.send_response(401); self.send_header('WWW-Authenticate','Basic realm="Competition Admin"'); self.end_headers(); return False
        return True
    def send_json(self,obj,status=200):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/config': return self.send_json({'minutes':int(CONFIG.get('minutes_per_team',30))})
        if path=='/api/state': return self.send_json({'open':is_test_open()})
        if path=='/api/admin/state':
            if not self.require_admin(): return
            return self.send_json({'open':is_test_open(),'minutes':int(CONFIG.get('minutes_per_team',120))})
        if path=='/api/admin/questions':
            if not self.require_admin(): return
            return self.send_json(json.loads((ROOT/'challenges.json').read_text(encoding='utf-8')))
        if path=='/challenges.json' and not is_test_open(): return self.send_json({'error':'The organizer has not started the test.'},403)
        if path=='/api/admin/submissions':
            if not self.require_admin(): return
            return self.send_json(read_data())
        if path=='/api/admin/fullscreen-events':
            if not self.require_admin(): return
            return self.send_json(read_fullscreen_events())
        if path=='/api/admin/export.csv':
            if not self.require_admin(): return
            rows=read_data(); out=io.StringIO(); w=csv.writer(out); w.writerow(['Team','Submitted at','Elapsed seconds','Challenge','Title','Answer'])
            for row in rows:
                for a in row.get('answers',[]): w.writerow([row.get('team',''),row.get('submitted_at',''),row.get('elapsed_seconds',''),a.get('id',''),a.get('title',''),a.get('answer','')])
            data=out.getvalue().encode('utf-8-sig'); self.send_response(200); self.send_header('Content-Type','text/csv; charset=utf-8'); self.send_header('Content-Disposition','attachment; filename="competition_answers.csv"'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if path=='/admin':
            if not self.require_admin(): return
            self.path='/admin.html'
        elif path in ('/','/index.html'): self.path='/index.html'
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        if path.startswith('/api/admin/') and not self.require_admin(): return
        if path=='/api/fullscreen-event':
            try:
                if not is_test_open(): return self.send_json({'error':'The test is closed.'},403)
                data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                team=str(data.get('team','')).strip()[:80]
                device_id=str(data.get('device_id','')).strip()
                event=str(data.get('event',''))
                if not team or len(device_id)<12 or event not in ('fullscreen_enter','fullscreen_exit','fullscreen_return','fullscreen_unverified','tab_hidden','tab_visible'):
                    return self.send_json({'error':'Invalid fullscreen status event.'},400)
                row={'team':team,'device_id':device_id,'event':event,'at':datetime.datetime.now().astimezone().isoformat(timespec='seconds')}
                with LOCK:
                    events=read_fullscreen_events(); events.append(row)
                    FULLSCREEN_FILE.write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
                return self.send_json({'ok':True})
            except Exception as e: return self.send_json({'error':str(e)},400)
        if path=='/api/admin/state':
            try:
                data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                opened=bool(data.get('open',False))
                STATE_FILE.write_text(json.dumps({'open':opened}),encoding='utf-8')
                return self.send_json({'ok':True,'open':opened})
            except Exception as e: return self.send_json({'error':str(e)},400)
        if path=='/api/admin/question':
            try:
                data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                qid=int(data.get('id',0)); title=str(data.get('title','')).strip(); glitch=str(data.get('glitch','')).strip()
                if qid<1 or qid>30 or not title or not glitch: return self.send_json({'error':'Enter a title and description.'},400)
                if len(title)>120 or len(glitch)>1200: return self.send_json({'error':'Title or description is too long.'},400)
                questions=json.loads((ROOT/'challenges.json').read_text(encoding='utf-8'))
                questions[qid-1]['title']=title; questions[qid-1]['glitch']=glitch
                (ROOT/'challenges.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
                return self.send_json({'ok':True})
            except Exception as e: return self.send_json({'error':str(e)},400)
        if path=='/api/admin/config':
            try:
                data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                minutes=int(data.get('minutes',120))
                if minutes<1 or minutes>360: return self.send_json({'error':'Time limit must be 1 to 360 minutes.'},400)
                CONFIG['minutes_per_team']=minutes
                (ROOT/'config.json').write_text(json.dumps(CONFIG,indent=2),encoding='utf-8')
                return self.send_json({'ok':True,'minutes':minutes})
            except Exception as e: return self.send_json({'error':str(e)},400)
        if path=='/api/admin/image':
            try:
                from urllib.parse import parse_qs
                question_id=int(parse_qs(urlparse(self.path).query).get('id',['0'])[0])
                if question_id<1 or question_id>30: return self.send_json({'error':'Invalid question number.'},400)
                length=int(self.headers.get('Content-Length','0'))
                ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','image/gif':'.gif'}.get(self.headers.get('Content-Type','').split(';')[0].lower())
                if not ext: return self.send_json({'error':'Choose a PNG, JPG, WEBP, or GIF image.'},400)
                if length<1 or length>8*1024*1024: return self.send_json({'error':'Image must be smaller than 8 MB.'},400)
                (ROOT/'images').mkdir(exist_ok=True)
                name=f'question-{question_id:02d}{ext}'
                (ROOT/'images'/name).write_bytes(self.rfile.read(length))
                questions=json.loads((ROOT/'challenges.json').read_text(encoding='utf-8'))
                questions[question_id-1]['image']='/images/'+name
                (ROOT/'challenges.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2),encoding='utf-8')
                return self.send_json({'ok':True,'image':'/images/'+name})
            except Exception as e: return self.send_json({'error':str(e)},400)
        if path!='/api/submit': return self.send_json({'error':'Not found'},404)
        try:
            if not is_test_open(): return self.send_json({'error':'The organizer has closed the test.'},403)
            length=int(self.headers.get('Content-Length','0'))
            if length>250000: return self.send_json({'error':'Submission too large'},413)
            data=json.loads(self.rfile.read(length))
            team=str(data.get('team','')).strip()
            device_id=str(data.get('device_id','')).strip()
            answers=data.get('answers',[])
            if not team or len(team)>80: return self.send_json({'error':'Enter a team name (80 characters maximum).'},400)
            if len(device_id)<12 or len(device_id)>120: return self.send_json({'error':'This browser session could not be verified. Refresh and try again.'},400)
            if len(answers)!=30: return self.send_json({'error':'Please submit answers for all 30 questions.'},400)
            cleaned=[]
            for i,a in enumerate(answers,1):
                answer=str(a.get('answer','')).strip()
                if len(answer)>3000: return self.send_json({'error':'An answer is too long.'},400)
                cleaned.append({'id':i,'title':str(a.get('title',''))[:120],'answer':answer})
            row={'team':team,'submitted_at':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'elapsed_seconds':max(0,int(data.get('elapsed_seconds',0))),'answers':cleaned}
            with LOCK:
                rows=read_data()
                if any(x.get('device_id')==device_id for x in rows): return self.send_json({'error':'A submission has already been received from this browser.'},409)
                row['device_id']=device_id
                rows.append(row); DATA.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
            return self.send_json({'ok':True})
        except Exception as e: return self.send_json({'error':'Could not save submission: '+str(e)},500)
def read_data():
    try: return json.loads(DATA.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError): return []
def read_fullscreen_events():
    try: return json.loads(FULLSCREEN_FILE.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError): return []
if __name__=='__main__':
    print('Game Debugging Test is ready at http://localhost:8000')
    print('Admin page: http://localhost:8000/admin | username: admin | password:',CONFIG['admin_password'])
    print('Attendees connect to this laptop using its local network address, port 8000.')
    port=int(os.environ.get('PORT','8000'))
    print('Listening on port',port)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
