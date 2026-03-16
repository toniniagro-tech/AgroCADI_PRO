
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import sqlite3, re

app = FastAPI(title="AgroCADI PRO v3")
DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS soil_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ph REAL,
        p REAL,
        k REAL,
        ca REAL,
        mg REAL,
        ctc REAL
    )
    """)
    conn.commit()
    conn.close()

init_db()

class SoilInput(BaseModel):
    ph: float
    p: float
    k: float
    ca: float
    mg: float
    ctc: float

def calcular_v_percent(ca, mg, k, ctc):
    return ((ca + mg + k) / ctc) * 100

def recomendar_adubacao(p, k):
    rec = {}
    if p < 10:
        rec["fosforo"] = "120 kg/ha P2O5"
    elif p < 20:
        rec["fosforo"] = "80 kg/ha P2O5"
    else:
        rec["fosforo"] = "Manutenção"

    if k < 50:
        rec["potassio"] = "100 kg/ha K2O"
    elif k < 100:
        rec["potassio"] = "60 kg/ha K2O"
    else:
        rec["potassio"] = "Manutenção"
    return rec

@app.get("/")
def root():
    return {"system": "AgroCADI PRO v3 API"}

@app.post("/soil-analysis")
def analyze_soil(data: SoilInput):
    v = calcular_v_percent(data.ca, data.mg, data.k, data.ctc)
    rec = recomendar_adubacao(data.p, data.k)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO soil_analysis (ph,p,k,ca,mg,ctc) VALUES (?,?,?,?,?,?)",
              (data.ph,data.p,data.k,data.ca,data.mg,data.ctc))
    conn.commit()
    conn.close()

    return {
        "v_percent": v,
        "recommendation": rec
    }

@app.post("/import-pdf")
async def import_pdf(file: UploadFile = File(...)):
    text = (await file.read()).decode(errors="ignore")
    data = {}

    ph = re.search(r"pH\s*([0-9\.]+)", text)
    if ph:
        data["ph"] = float(ph.group(1))

    p = re.search(r"P\s*([0-9\.]+)", text)
    if p:
        data["p"] = float(p.group(1))

    k = re.search(r"K\s*([0-9\.]+)", text)
    if k:
        data["k"] = float(k.group(1))

    return {"extracted": data}
