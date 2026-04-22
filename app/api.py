"""
Heart Disease Prediction API - v2.0.0

API profesional para inferencia de riesgo cardiovascular.
Incluye dashboard web embebido, health checks, logging estructurado y CORS.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Logging estructurado
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("heart-api")


# -----------------------------------------------------------------------------
# Carga del modelo
# -----------------------------------------------------------------------------
API_VERSION = "2.0.0"
MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"

try:
    model = joblib.load(MODEL_PATH)
    MODEL_LOADED = True
    MODEL_ERROR = None
    logger.info(f"Model loaded from {MODEL_PATH}")
except Exception as exc:
    model = None
    MODEL_LOADED = False
    MODEL_ERROR = str(exc)
    logger.error(f"Failed to load model: {exc}")


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Heart Disease Prediction API",
    description=(
        "Servicio de inferencia para estimacion de riesgo de enfermedad cardiovascular "
        "basado en variables clinicas. Entrenado con pipeline de scikit-learn y "
        "validado mediante cross-validation estratificada."
    ),
    version=API_VERSION,
    contact={"name": "Heart Disease MLOps"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} "
        f"({elapsed_ms:.1f} ms)"
    )
    return response


# -----------------------------------------------------------------------------
# Schemas Pydantic
# -----------------------------------------------------------------------------
class HeartInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "Age": 58,
                    "Sex": "M",
                    "ChestPainType": "ASY",
                    "RestingBP": 150,
                    "Cholesterol": 270,
                    "FastingBS": 0,
                    "RestingECG": "Normal",
                    "MaxHR": 112,
                    "ExerciseAngina": "Y",
                    "Oldpeak": 2.5,
                    "ST_Slope": "Flat",
                }
            ]
        }
    )

    Age: int = Field(..., ge=18, le=100, description="Edad del paciente en anios")
    Sex: Literal["M", "F"] = Field(..., description="Sexo biologico: M o F")
    ChestPainType: Literal["ATA", "NAP", "ASY", "TA"] = Field(
        ..., description="Tipo de dolor de pecho"
    )
    RestingBP: int = Field(..., ge=50, le=250, description="Presion arterial en reposo (mmHg)")
    Cholesterol: int = Field(..., ge=0, le=700, description="Colesterol serico (mg/dl)")
    FastingBS: Literal[0, 1] = Field(..., description="Glucemia en ayunas > 120 mg/dl")
    RestingECG: Literal["Normal", "ST", "LVH"] = Field(..., description="Resultado ECG en reposo")
    MaxHR: int = Field(..., ge=60, le=220, description="Frecuencia cardiaca maxima alcanzada")
    ExerciseAngina: Literal["Y", "N"] = Field(..., description="Angina inducida por ejercicio")
    Oldpeak: float = Field(..., ge=-3.0, le=7.0, description="Depresion ST por ejercicio")
    ST_Slope: Literal["Up", "Flat", "Down"] = Field(..., description="Pendiente del segmento ST")


class PredictionOutput(BaseModel):
    prediction: int = Field(..., description="0 = sin enfermedad, 1 = con enfermedad")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de enfermedad")
    risk_level: str = Field(..., description="bajo | moderado | alto")
    model_version: str = Field(..., description="Version del servicio")


class HealthOutput(BaseModel):
    status: str
    model_loaded: bool
    version: str
    model_error: str | None = None


class VersionOutput(BaseModel):
    api_version: str
    model_loaded: bool


# -----------------------------------------------------------------------------
# Endpoints tecnicos
# -----------------------------------------------------------------------------
@app.get("/health", response_model=HealthOutput, tags=["system"])
def health():
    """Liveness probe para Kubernetes."""
    if MODEL_LOADED:
        return HealthOutput(status="ok", model_loaded=True, version=API_VERSION)
    return HealthOutput(
        status="degraded",
        model_loaded=False,
        version=API_VERSION,
        model_error=MODEL_ERROR,
    )


@app.get("/version", response_model=VersionOutput, tags=["system"])
def version():
    """Informacion de version del servicio."""
    return VersionOutput(api_version=API_VERSION, model_loaded=MODEL_LOADED)


@app.post("/predict", response_model=PredictionOutput, tags=["inference"])
def predict(data: HeartInput):
    """Inferencia de riesgo cardiovascular a partir de variables clinicas."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail=f"Modelo no disponible: {MODEL_ERROR}")

    input_df = pd.DataFrame([data.model_dump()])

    try:
        prediction = int(model.predict(input_df)[0])
        probability = float(model.predict_proba(input_df)[0, 1])
    except Exception as exc:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Error en inferencia: {exc}")

    if probability < 0.3:
        risk = "bajo"
    elif probability < 0.7:
        risk = "moderado"
    else:
        risk = "alto"

    logger.info(f"predict -> prediction={prediction} prob={probability:.3f} risk={risk}")

    return PredictionOutput(
        prediction=prediction,
        probability=round(probability, 4),
        risk_level=risk,
        model_version=API_VERSION,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para errores inesperados."""
    logger.exception(f"Unhandled error on {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)},
    )


# -----------------------------------------------------------------------------
# Dashboard HTML embebido
# -----------------------------------------------------------------------------
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Cardiograph — Risk Inference</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,300&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --ink: #0a0a0a;
    --paper: #fafaf7;
    --paper-soft: #f2f1eb;
    --rule: #1a1a1a;
    --muted: #6b6b6b;
    --accent-low: #5b6b48;
    --accent-mid: #9a7a3d;
    --accent-high: #a8362a;
  }

  html, body {
    background: var(--paper);
    color: var(--ink);
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 400;
    line-height: 1.4;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }

  /* Grano sutil */
  body::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1;
    opacity: 0.035;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  }

  .wrap {
    max-width: 1280px;
    margin: 0 auto;
    padding: 48px 56px 120px;
    position: relative;
    z-index: 2;
  }

  /* Header */
  header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid var(--rule);
    padding-bottom: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink);
  }

  header .brand {
    display: flex;
    align-items: baseline;
    gap: 10px;
  }

  header .brand .mark {
    width: 8px;
    height: 8px;
    background: var(--accent-high);
    border-radius: 50%;
    display: inline-block;
    animation: pulse 2.4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%      { transform: scale(1.4); opacity: 0.55; }
  }

  header .meta { color: var(--muted); }

  /* Hero */
  .hero {
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 80px;
    padding: 80px 0 100px;
    border-bottom: 1px solid var(--rule);
    align-items: end;
  }

  .hero h1 {
    font-size: clamp(54px, 8vw, 124px);
    font-weight: 300;
    line-height: 0.92;
    letter-spacing: -0.035em;
    font-variation-settings: "opsz" 144;
  }

  .hero h1 em {
    font-style: italic;
    font-weight: 400;
    color: var(--accent-high);
  }

  .hero .lede {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    line-height: 1.7;
    color: var(--muted);
    max-width: 380px;
    padding-top: 60px;
  }

  .hero .lede strong {
    color: var(--ink);
    font-weight: 500;
  }

  .hero .tagrow {
    margin-top: 24px;
    display: flex;
    gap: 24px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink);
  }

  .hero .tagrow span {
    border: 1px solid var(--rule);
    padding: 6px 12px;
  }

  /* Section heading */
  .section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 40px 0 28px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .section-label::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--rule);
    opacity: 0.2;
  }

  /* Form grid */
  .form-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    border-top: 1px solid var(--rule);
    border-left: 1px solid var(--rule);
  }

  .field {
    border-right: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: 24px 22px 20px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: var(--paper);
    transition: background 0.25s ease;
  }

  .field:hover { background: var(--paper-soft); }

  .field label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }

  .field label .hint {
    color: var(--ink);
    opacity: 0.4;
    font-size: 9px;
    letter-spacing: 0.1em;
  }

  .field input, .field select {
    border: none;
    background: transparent;
    font-family: 'Fraunces', serif;
    font-weight: 400;
    font-size: 26px;
    color: var(--ink);
    padding: 0;
    outline: none;
    letter-spacing: -0.01em;
  }

  .field input:focus, .field select:focus {
    color: var(--accent-high);
  }

  .field select {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 16px;
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
  }

  /* Action row */
  .action-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 40px 0 0;
  }

  .disclaimer {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    max-width: 420px;
    line-height: 1.7;
  }

  button.submit {
    background: var(--ink);
    color: var(--paper);
    border: none;
    padding: 22px 48px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
  }

  button.submit:hover {
    background: var(--accent-high);
    transform: translate(-2px, -2px);
    box-shadow: 4px 4px 0 var(--ink);
  }

  button.submit:active {
    transform: translate(0, 0);
    box-shadow: none;
  }

  button.submit:disabled { opacity: 0.35; cursor: wait; }

  /* Result */
  .result {
    margin-top: 80px;
    border-top: 1px solid var(--rule);
    padding-top: 48px;
    opacity: 0;
    transform: translateY(16px);
    transition: opacity 0.8s ease, transform 0.8s ease;
  }

  .result.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .result-grid {
    display: grid;
    grid-template-columns: 1.3fr 1fr;
    gap: 100px;
    align-items: start;
  }

  .result .score {
    font-family: 'Fraunces', serif;
    font-size: clamp(140px, 20vw, 280px);
    font-weight: 300;
    line-height: 0.88;
    letter-spacing: -0.05em;
    font-variation-settings: "opsz" 144;
    color: var(--ink);
    display: flex;
    align-items: baseline;
  }

  .result .score .pct {
    font-size: 0.25em;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 400;
    letter-spacing: 0;
    margin-left: 16px;
    color: var(--muted);
    align-self: flex-end;
    padding-bottom: 24px;
  }

  .result .score.bajo     { color: var(--accent-low); }
  .result .score.moderado { color: var(--accent-mid); }
  .result .score.alto     { color: var(--accent-high); }

  .result .meta-col {
    padding-top: 20px;
  }

  .result .meta-row {
    display: flex;
    justify-content: space-between;
    padding: 14px 0;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
  }

  .result .meta-row .k {
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .result .meta-row .v {
    color: var(--ink);
    font-weight: 500;
  }

  .result .verdict {
    font-family: 'Fraunces', serif;
    font-size: 22px;
    font-style: italic;
    font-weight: 300;
    margin-top: 32px;
    line-height: 1.5;
    color: var(--ink);
    padding-right: 20px;
  }

  /* Footer */
  footer {
    margin-top: 120px;
    padding-top: 24px;
    border-top: 1px solid var(--rule);
    display: flex;
    justify-content: space-between;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
  }

  footer a { color: var(--ink); text-decoration: none; border-bottom: 1px solid currentColor; }
  footer a:hover { color: var(--accent-high); }

  /* Responsive */
  @media (max-width: 900px) {
    .wrap { padding: 32px 24px 80px; }
    .hero { grid-template-columns: 1fr; gap: 32px; padding: 48px 0 64px; }
    .hero .lede { padding-top: 0; }
    .form-grid { grid-template-columns: repeat(2, 1fr); }
    .action-row { flex-direction: column; gap: 24px; align-items: stretch; }
    .result-grid { grid-template-columns: 1fr; gap: 40px; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <span class="mark"></span>
      <span>Cardiograph</span>
      <span class="meta">/ risk inference v2.0</span>
    </div>
    <div class="meta" id="status-indicator">Model · Ready</div>
  </header>

  <section class="hero">
    <div>
      <h1>Clinical risk,<br/>estimated with <em>precision.</em></h1>
    </div>
    <div class="lede">
      <strong>Cardiograph</strong> es un servicio de inferencia estadistica que estima
      la probabilidad de enfermedad cardiovascular a partir de once variables clinicas
      estandar. Entrenado con un pipeline de scikit-learn validado con cross-validation
      estratificada.
      <div class="tagrow">
        <span>KNN · AUC 0.95</span>
        <span>Docker · FastAPI</span>
      </div>
    </div>
  </section>

  <div class="section-label">01 · Patient record</div>

  <form id="form">
    <div class="form-grid">
      <div class="field">
        <label>Age <span class="hint">18–100</span></label>
        <input type="number" id="Age" value="58" min="18" max="100" required />
      </div>
      <div class="field">
        <label>Sex</label>
        <select id="Sex"><option value="M">M · Male</option><option value="F">F · Female</option></select>
      </div>
      <div class="field">
        <label>Chest pain</label>
        <select id="ChestPainType">
          <option value="ASY">ASY · Asymptomatic</option>
          <option value="NAP">NAP · Non-anginal</option>
          <option value="ATA">ATA · Atypical</option>
          <option value="TA">TA · Typical</option>
        </select>
      </div>
      <div class="field">
        <label>Resting BP <span class="hint">mmHg</span></label>
        <input type="number" id="RestingBP" value="150" min="50" max="250" required />
      </div>
      <div class="field">
        <label>Cholesterol <span class="hint">mg/dl</span></label>
        <input type="number" id="Cholesterol" value="270" min="0" max="700" required />
      </div>
      <div class="field">
        <label>Fasting BS <span class="hint">>120</span></label>
        <select id="FastingBS"><option value="0">0 · No</option><option value="1">1 · Yes</option></select>
      </div>
      <div class="field">
        <label>Resting ECG</label>
        <select id="RestingECG">
          <option value="Normal">Normal</option>
          <option value="ST">ST abnormality</option>
          <option value="LVH">LVH</option>
        </select>
      </div>
      <div class="field">
        <label>Max HR <span class="hint">bpm</span></label>
        <input type="number" id="MaxHR" value="112" min="60" max="220" required />
      </div>
      <div class="field">
        <label>Exercise angina</label>
        <select id="ExerciseAngina"><option value="Y">Y · Yes</option><option value="N">N · No</option></select>
      </div>
      <div class="field">
        <label>Oldpeak <span class="hint">ST dep.</span></label>
        <input type="number" id="Oldpeak" value="2.5" step="0.1" min="-3" max="7" required />
      </div>
      <div class="field">
        <label>ST slope</label>
        <select id="ST_Slope">
          <option value="Flat">Flat</option>
          <option value="Up">Up</option>
          <option value="Down">Down</option>
        </select>
      </div>
      <div class="field" style="background: var(--ink);">
        <label style="color: rgba(255,255,255,0.5);">Action</label>
        <span style="color: var(--paper); font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; padding-top: 6px;">
          Submit below →
        </span>
      </div>
    </div>

    <div class="action-row">
      <div class="disclaimer">
        Esta herramienta es un apoyo estadistico. No reemplaza el criterio clinico
        ni el diagnostico medico profesional.
      </div>
      <button class="submit" type="submit" id="btn">Compute risk</button>
    </div>
  </form>

  <section class="result" id="result">
    <div class="section-label">02 · Inference result</div>
    <div class="result-grid">
      <div>
        <div class="score" id="score"><span id="scoreNum">0</span><span class="pct">/100</span></div>
        <div class="verdict" id="verdict">—</div>
      </div>
      <div class="meta-col">
        <div class="meta-row"><span class="k">Prediction</span><span class="v" id="pred">—</span></div>
        <div class="meta-row"><span class="k">Probability</span><span class="v" id="prob">—</span></div>
        <div class="meta-row"><span class="k">Risk level</span><span class="v" id="risk">—</span></div>
        <div class="meta-row"><span class="k">Model version</span><span class="v" id="ver">—</span></div>
        <div class="meta-row"><span class="k">Latency</span><span class="v" id="lat">—</span></div>
      </div>
    </div>
  </section>

  <footer>
    <span>© Cardiograph · Heart Disease MLOps</span>
    <span><a href="/docs">Open API docs →</a></span>
  </footer>
</div>

<script>
  const $ = (id) => document.getElementById(id);

  const num = (id) => {
    const v = $(id).value;
    return id === "Oldpeak" ? parseFloat(v) : parseInt(v, 10);
  };
  const str = (id) => $(id).value;

  const VERDICTS = {
    bajo: "El perfil sugiere baja probabilidad de enfermedad. Mantener seguimiento rutinario.",
    moderado: "El perfil muestra factores de riesgo intermedios. Se recomienda evaluacion clinica adicional.",
    alto: "El perfil indica alta probabilidad de enfermedad. Requiere evaluacion medica prioritaria.",
  };

  function animateScore(target) {
    const el = $("scoreNum");
    const duration = 900;
    const start = performance.now();
    const from = parseFloat(el.textContent) || 0;
    function frame(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(from + (target - from) * eased);
      if (t < 1) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  $("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = $("btn");
    btn.disabled = true;
    btn.textContent = "Computing…";

    const payload = {
      Age: num("Age"),
      Sex: str("Sex"),
      ChestPainType: str("ChestPainType"),
      RestingBP: num("RestingBP"),
      Cholesterol: num("Cholesterol"),
      FastingBS: parseInt(str("FastingBS"), 10),
      RestingECG: str("RestingECG"),
      MaxHR: num("MaxHR"),
      ExerciseAngina: str("ExerciseAngina"),
      Oldpeak: num("Oldpeak"),
      ST_Slope: str("ST_Slope"),
    };

    const t0 = performance.now();
    try {
      const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const elapsed = (performance.now() - t0).toFixed(0);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const pct = Math.round(data.probability * 100);
      const scoreEl = $("score");
      scoreEl.classList.remove("bajo", "moderado", "alto");
      scoreEl.classList.add(data.risk_level);

      $("pred").textContent = data.prediction === 1 ? "POSITIVE" : "NEGATIVE";
      $("prob").textContent = data.probability.toFixed(4);
      $("risk").textContent = data.risk_level.toUpperCase();
      $("ver").textContent = data.model_version;
      $("lat").textContent = `${elapsed} ms`;
      $("verdict").textContent = VERDICTS[data.risk_level] || "—";

      $("result").classList.add("visible");
      animateScore(pct);

      setTimeout(() => {
        $("result").scrollIntoView({ behavior: "smooth", block: "start" });
      }, 120);
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Compute risk";
    }
  });

  // Ping health on load
  fetch("/health").then(r => r.json()).then(d => {
    $("status-indicator").textContent = d.model_loaded
      ? `Model · Ready · v${d.version}`
      : "Model · Degraded";
  }).catch(() => {
    $("status-indicator").textContent = "Model · Offline";
  });
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def dashboard():
    """Dashboard web embebido para inferencia interactiva."""
    return DASHBOARD_HTML
