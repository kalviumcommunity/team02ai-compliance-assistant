from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, timezone
import json,re,uuid
try:
 from pypdf import PdfReader
except: PdfReader=None
BASE=Path(__file__).parent
DATA=BASE/"data"; DATA.mkdir(exist_ok=True)
DOCS=DATA/"documents.json"; AUDIT=DATA/"audit.json"
app=FastAPI(title="AI Compliance Assistant - Squad 69")
app.mount("/static",StaticFiles(directory=BASE.parent/"frontend"),name="static")
def load(p): 
 try:return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []
 except:return []
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding="utf-8")
def audit(action,detail):
 a=load(AUDIT);a.insert(0,{"time":datetime.now(timezone.utc).isoformat(timespec="seconds"),"user":"Demo User","action":action,"detail":detail});save(AUDIT,a[:500])
def toks(s):return set(w for w in re.findall(r"[a-z0-9]+",s.lower()) if len(w)>2 and w not in {"the","and","for","what","which","does","with","from","that","this","are","was","were","how","can","should"})
def retrieve(q):
 terms=toks(q); hits=[]
 for d in load(DOCS):
  for i,c in enumerate(re.split(r"(?<=[.!?])\s+|\n+",d["text"])):
   overlap=terms & toks(c)
   if overlap and len(c.strip())>20:hits.append({"title":d["title"],"status":d.get("status","Unknown"),"effective_date":d.get("effective_date",""),"excerpt":c.strip(),"score":round(len(overlap)/max(1,len(terms)),2),"section":f"Passage {i+1}"})
 return sorted(hits,key=lambda h:h["score"],reverse=True)[:5]
class Ask(BaseModel):question:str
class Txn(BaseModel):transaction_type:str;amount_band:str="";transaction_date:str="";jurisdiction:str="";product:str=""
@app.get("/",response_class=HTMLResponse)
def home():return (BASE.parent/"frontend/index.html").read_text()
@app.get("/api/health")
def health():return {"status":"ok","documents":len(load(DOCS))}
@app.get("/api/documents")
def docs():return [{k:d.get(k,"") for k in ["id","title","issuer","document_type","effective_date","version","status","filename"]} for d in load(DOCS)]
@app.post("/api/demo")
def demo():
 ds=load(DOCS)
 if ds:return {"message":"Demo documents already loaded"}
 examples=[
 ("Fictional Transfer Policy v2","Internal Policy","2026-07-01","2.0","Current","For high value transfers above INR 500000, a second authorized officer must review the transfer before processing. The reviewer must record review date and reviewer identifier. All transfer requests must include transaction date, amount, beneficiary, and originating account verification. This is fictional demo content."),
 ("Fictional Transfer Policy v1","Internal Policy","2025-01-15","1.0","Superseded","Historical fictional policy superseded by Fictional Transfer Policy v2 effective 2026-07-01. Under the old demo workflow, transfers above INR 300000 required a second officer review. This is not a current or real banking rule."),
 ("Fictional Audit Evidence Note","Audit Report","2026-08-15","1.0","Current","A transfer review record should include transaction reference, reviewer identity, review timestamp, and policy version consulted. If effective date or governing policy cannot be verified, escalate to compliance manager. Synthetic demo audit note.")
 ]
 for title,typ,date,ver,status,txt in examples:ds.append({"id":str(uuid.uuid4())[:8],"title":title,"issuer":"Fictional Demo Bank","document_type":typ,"effective_date":date,"version":ver,"status":status,"text":txt,"filename":"seed"})
 save(DOCS,ds);audit("DEMO_SEED",f"Loaded {len(examples)} fictional docs");return {"message":"Loaded 3 fictional demo documents"}
@app.post("/api/upload")
async def upload(file:UploadFile=File(...),title:str=Form(""),issuer:str=Form("Uploaded source"),document_type:str=Form("Policy"),effective_date:str=Form(""),version:str=Form("1.0"),status:str=Form("Unknown")):
 name=Path(file.filename or "file.txt").name; ext=Path(name).suffix.lower(); raw=await file.read()
 if ext not in [".txt",".pdf"]:raise HTTPException(400,"Upload TXT or text-based PDF only.")
 if len(raw)>8*1024*1024:raise HTTPException(413,"Maximum file size is 8 MB.")
 if ext==".txt":text=raw.decode("utf-8",errors="replace")
 else:
  if not PdfReader:raise HTTPException(500,"Install requirements for PDF support.")
  import io
  text="\\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
 if not text.strip():raise HTTPException(400,"No text extracted; image-only PDFs/OCR are not supported.")
 d={"id":str(uuid.uuid4())[:8],"title":title or Path(name).stem,"issuer":issuer,"document_type":document_type,"effective_date":effective_date,"version":version,"status":status,"text":text,"filename":name}
 ds=load(DOCS);ds.append(d);save(DOCS,ds);audit("UPLOAD",d["title"]);return {"message":"Uploaded and indexed"}
@app.post("/api/ask")
def ask(q:Ask):
 hits=retrieve(q.question);audit("QUESTION",q.question[:250])
 if not hits:return {"answer":"Insufficient evidence found in the indexed demo documents. Upload an authorized source or escalate to a compliance reviewer.","warning":"No compliance conclusion is made.","citations":[]}
 warning="Prototype only. Verify the original source and applicability with an authorized reviewer."
 statuses={h["status"] for h in hits}
 if "Current" in statuses and "Superseded" in statuses:warning+=" Results include current and superseded sources; check verified document lineage."
 if "Unknown" in statuses:warning+=" Some source status is unknown."
 answer="Based on matching source passages:\\n\\n"+"\\n\\n".join("• "+h["excerpt"]+" [Source: "+h["title"]+"]" for h in hits[:3])
 return {"answer":answer,"warning":warning,"citations":hits}
@app.post("/api/transaction")
def transaction(t:Txn):
 missing=[label for key,label in [("transaction_type","transaction type"),("transaction_date","transaction date"),("jurisdiction","jurisdiction"),("product","product/category")] if not getattr(t,key)]
 if not t.amount_band:missing.append("amount band")
 hits=retrieve(" ".join(t.model_dump().values()));audit("TRANSACTION_REVIEW",t.transaction_type)
 notes=[]
 if missing:notes.append("Missing details: "+", ".join(missing))
 notes.append("Review cited passages with an authorized person. This is not an approval decision." if hits else "No relevant source found; do not infer compliance or non-compliance.")
 return {"summary":"Preliminary research support only — not a compliance decision.","notes":notes,"citations":hits}
@app.get("/api/audit")
def logs():return load(AUDIT)
