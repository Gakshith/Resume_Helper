from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Depends
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
import json
import os
import secrets
from typing import List, Dict, Any, Optional
from pathlib import Path
from pypdf import PdfReader
import pickle
import os
import nltk
from dotenv import load_dotenv

load_dotenv()


import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def ensure_nltk_resource(resource_path: str, package_name: str, fallback_paths: Optional[List[Path]] = None):
    if fallback_paths and any(path.exists() for path in fallback_paths):
        return

    try:
        nltk.data.find(resource_path)
    except (LookupError, OSError):
        nltk.download(package_name)


ensure_nltk_resource('tokenizers/punkt', "punkt")
ensure_nltk_resource(
    'tokenizers/punkt_tab',
    "punkt_tab",
    [Path.home() / "nltk_data" / "tokenizers" / "punkt_tab"],
)
ensure_nltk_resource('corpora/stopwords', "stopwords")
ensure_nltk_resource(
    'corpora/wordnet',
    "wordnet",
    [Path.home() / "nltk_data" / "corpora" / "wordnet.zip"],
)

from Models import Login, Register
import analysis
import sys
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

class SimpleTextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.combined_noise_pattern = re.compile(
            r'http\S+|www\S+|https\S+|<.*?>|[^a-zA-Z\s]'
        )

    def clean_text(self, text):
        if not text:
            return ""

        text = str(text).lower()
        text = self.combined_noise_pattern.sub(' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = word_tokenize(text)

        final_tokens = []
        for word in tokens:
            if word not in self.stop_words and len(word) > 2:
                lemma = self.lemmatizer.lemmatize(word)
                final_tokens.append(lemma)

        return ' '.join(final_tokens)

# Create global instance as anticipated by the pickled function closure/global reference
preprocessor = SimpleTextPreprocessor()

def apply_custom_cleaning(X):
    # The training code used: return X.apply(preprocessor.clean_text)
    # This expects X to be a pandas Series.
    # We support Series or direct text (wrapping it if needed, but the pickled function likely calls .apply)
    if hasattr(X, 'apply'):
        return X.apply(preprocessor.clean_text)
    # Fallback if passed a list or other iterable that isn't a Series (though we should pass Series)
    return [preprocessor.clean_text(x) for x in X]

# Inject into __main__ so pickle finds them
try:
    import __main__
    setattr(__main__, "SimpleTextPreprocessor", SimpleTextPreprocessor)
    setattr(__main__, "preprocessor", preprocessor)
    setattr(__main__, "apply_custom_cleaning", apply_custom_cleaning)
except ImportError:
    pass

app = FastAPI()


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
JSON_FILE = "Login_Db.json"
MODEL_PATH = os.getenv("MODEL_PATH", "resume_classification_model1.pkl")

# --- Static & Templates ---
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# --- Global State ---
users_db: List[Dict[str, Any]] = []
sessions: Dict[str, str] = {}
ml_components: Dict[str, Any] = {}
model_ready: bool = False
# Per-session result of the most recent upload (drives dashboard + editor + JD match).
analysis_store: Dict[str, Dict[str, Any]] = {}

# --- Data Loading ---
def load_data_from_json():
    global users_db
    if os.path.exists(JSON_FILE) and os.path.getsize(JSON_FILE) > 0:
        try:
            with open(JSON_FILE, "r") as f:
                users_db = json.load(f)
        except json.JSONDecodeError:
            print(f"WARNING: {JSON_FILE} corrupted. Starting empty.")
            users_db = []
    else:
        print(f"INFO: {JSON_FILE} not found or empty. Starting empty.")
        users_db = []

def save_data_to_json():
    with open(JSON_FILE, "w") as f:
        json.dump(users_db, f, indent=4)

load_data_from_json()

# --- ML Loading (Startup) ---
@app.on_event("startup")
async def load_ml_model():
    """Load the classifier once at startup and verify it can predict."""
    global model_ready
    if not os.path.exists(MODEL_PATH):
        print(f"WARNING: Model file '{MODEL_PATH}' not found. Resume classification disabled.")
        return
    try:
        with open(MODEL_PATH, "rb") as model_file:
            data = pickle.load(model_file)
        # The artifact may be a bare estimator/pipeline or a dict wrapper.
        pipeline = data.get("pipeline") or data.get("model") if isinstance(data, dict) else data
        if pipeline is None or not hasattr(pipeline, "predict"):
            print("ERROR: Loaded model has no .predict(); classification disabled.")
            return
        ml_components["pipeline"] = pipeline
        # Health check: a model that can't predict a sample is not usable.
        try:
            pipeline.predict(["health check sample resume text"])
            model_ready = True
            print("ML model loaded and health check passed.")
        except Exception as e:
            print(f"WARNING: Model loaded but failed its health-check prediction: {e}")
            print("Resume classification will be disabled until a fitted model is provided.")
    except Exception as e:
        print(f"ERROR: Failed to load ML model: {e}")

# --- Resume Classification ---
# Sorted so integer class indices map deterministically to a category name.
CATEGORIES = sorted([
    "HR", "Designer", "Information-Technology", "Teacher", "Advocate",
    "Business-Development", "Healthcare", "Fitness", "Agriculture", "BPO",
    "Sales", "Consultant", "Digital-Media", "Automobile", "Chef",
    "Finance", "Apparel", "Engineering", "Accountant", "Construction",
    "Public-Relations", "Banking", "Arts", "Aviation"
])


def _label_for(raw_label: Any) -> str:
    """Map a raw model class (string label or integer index) to a category name."""
    if isinstance(raw_label, str):
        return raw_label
    if hasattr(raw_label, "__index__"):
        idx = int(raw_label)
        return CATEGORIES[idx] if 0 <= idx < len(CATEGORIES) else f"{raw_label} (Unknown)"
    return str(raw_label)


def classify_resume(text: str):
    """Classify resume text into a job category.

    Returns (prediction, confidence, top_roles) where:
      - prediction:  best-matching category name (str)
      - confidence:  float percent (0-100) or None if the model has no probabilities
      - top_roles:   list of {"role": str, "prob": float|None}, highest first

    Raises RuntimeError if the model is not ready, or re-raises prediction errors.
    """
    pipeline = ml_components.get("pipeline")
    if not model_ready or pipeline is None:
        raise RuntimeError("Resume classification model is not ready.")

    # Preferred path: a probability distribution gives us confidence + ranking.
    if hasattr(pipeline, "predict_proba"):
        try:
            probs = pipeline.predict_proba([text])[0]
            classes = getattr(pipeline, "classes_", list(range(len(probs))))
            ranked = sorted(
                ((_label_for(c), float(p)) for c, p in zip(classes, probs)),
                key=lambda pair: pair[1],
                reverse=True,
            )
            top_roles = [{"role": r, "prob": round(p * 100, 1)} for r, p in ranked[:3]]
            best_role, best_prob = ranked[0]
            return best_role, round(best_prob * 100, 1), top_roles
        except Exception as e:
            print(f"predict_proba failed, falling back to predict(): {e}")

    # Fallback: bare label, no confidence available.
    prediction = _label_for(pipeline.predict([text])[0])
    return prediction, None, [{"role": prediction, "prob": None}]


def get_current_user_from_cookie(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("session_token")
    if not token:
        return None
    username = sessions.get(token)
    if not username:
        return None
    user = next((u for u in users_db if u.get("UserName") == username), None)
    return user

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = {
            "/", "/login", "/register", "/logout",
            "/docs", "/openapi.json", "/static/style.css",
            "/chat" 
        }
        if request.url.path.startswith("/static"):
             return await call_next(request)

        if request.url.path in public_paths:
            return await call_next(request)

        user = get_current_user_from_cookie(request)
        if user is None:
            return RedirectResponse(url="/login", status_code=302)
        return await call_next(request)

app.add_middleware(AuthMiddleware)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, UserName: str = Form(...), Password: str = Form(...)):
    try:
        reg_data = Register(UserName=UserName, Password=Password)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": f"Invalid data: {e}"}, status_code=400)

    if any(u.get("UserName") == reg_data.UserName for u in users_db):
         return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken."}, status_code=409)

    new_user = {"UserName": reg_data.UserName, "Password": reg_data.Password}
    users_db.append(new_user)
    save_data_to_json()

    return RedirectResponse(url="/login", status_code=303) 

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, UserName: str = Form(...), Password: str = Form(...)):
    user = next((u for u in users_db if u.get("UserName") == UserName), None)
    
    if user is None or user.get("Password") != Password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"}, status_code=401)

    token = secrets.token_urlsafe(32)
    sessions[token] = UserName
    resp = RedirectResponse(url="/home", status_code=303)
    resp.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
    )
    return resp

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
         return RedirectResponse(url="/login", status_code=302)
         
    return templates.TemplateResponse("home.html", {"request": request, "username": user.get("UserName")})

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token and token in sessions:
        sessions.pop(token, None)
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("session_token")
    return resp

@app.post("/upload-pdf", response_class=HTMLResponse)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
         return templates.TemplateResponse("home.html", {"request": request, "username": user.get("UserName"), "error": "Only PDF files are allowed."})
    safe_name = f"{secrets.token_hex(8)}_{file.filename}"
    save_path = UPLOAD_DIR / safe_name
    
    try:
        content = await file.read()
        save_path.write_bytes(content)
    except Exception as e:
         return templates.TemplateResponse("home.html", {"request": request, "username": user.get("UserName"), "error": f"Upload failed: {e}"})

    extracted_text = ""
    try:
        reader = PdfReader(str(save_path))
        for page in reader.pages:
            extracted_text += (page.extract_text() or "") + "\n"
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return templates.TemplateResponse("home.html", {"request": request, "username": user.get("UserName"), "error": "Could not extract text from PDF."})
    
    if not model_ready or ml_components.get("pipeline") is None:
        return templates.TemplateResponse("home.html", {
            "request": request,
            "username": user.get("UserName"),
            "error": "Resume classification is temporarily unavailable (model not ready). "
                     "Your file was uploaded but could not be analyzed.",
        })

    try:
        predicted_category, confidence, top_roles = classify_resume(extracted_text)
    except Exception as e:
        print(f"Prediction error: {e}")
        return templates.TemplateResponse("home.html", {
            "request": request,
            "username": user.get("UserName"),
            "error": "Could not classify this resume. Please try a different file.",
        })

    print(f"User: {user.get('UserName')} | File: {filename} | Prediction: {predicted_category} "
          f"| Confidence: {confidence}")

    report = analysis.analyze(extracted_text)

    token = request.cookies.get("session_token")
    pdf_url = f"/uploads/{safe_name}"
    record = {
        "username": user.get("UserName"),
        "filename": file.filename,
        "prediction": predicted_category,
        "confidence": confidence,
        "top_roles": top_roles,
        "pdf_url": pdf_url,
        "extracted_text": extracted_text,
        "report": report,
    }
    if token:
        chat_context[token] = extracted_text
        analysis_store[token] = record

    return templates.TemplateResponse("dashboard.html", {"request": request, **record})


def _record_for(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("session_token")
    return analysis_store.get(token) if token else None


@app.get("/editor", response_class=HTMLResponse)
async def editor(request: Request):
    record = _record_for(request)
    if not record:
        return RedirectResponse(url="/home", status_code=302)
    return templates.TemplateResponse("editor.html", {"request": request, **record})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    record = _record_for(request)
    if not record:
        return RedirectResponse(url="/home", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request, **record})


class JDRequest(BaseModel):
    jd_text: str


@app.post("/match-jd")
async def match_jd(request: Request, jd_req: JDRequest):
    record = _record_for(request)
    if not record:
        return {"score": 0, "matched": [], "missing": [], "error": "No resume uploaded yet."}
    return analysis.match_job_description(record["extracted_text"], jd_req.jd_text)
chat_context: Dict[str, str] = {}

try:
    from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except Exception as e:
    print(f"Failed to import chat dependencies: {e}")
    HuggingFaceEndpoint = None
    ChatHuggingFace = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None


repo_id = "meta-llama/Meta-Llama-3-8B-Instruct"
api_token = os.getenv("HUGGINGFACE_API_TOKEN")

try:
    if HuggingFaceEndpoint is None or ChatHuggingFace is None:
        raise RuntimeError("Chat dependencies are unavailable.")
    endpoint = HuggingFaceEndpoint(
        repo_id=repo_id,
        huggingfacehub_api_token=api_token,
        temperature=0.5,
        max_new_tokens=512, 
    )
    chat_model = ChatHuggingFace(llm=endpoint)
    print("Chat model initialized successfully.")
except Exception as e:
    print(f"Failed to initialize chat model: {e}")
    chat_model = None
user_chat_histories: Dict[str, List[Any]] = {}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    token = request.cookies.get("session_token")
    
    if not token or token not in sessions:
        return {"reply": "Please login to use the chat."}
    
    if token not in chat_context:
        return {"reply": "I don't see a resume uploaded. Please upload a PDF resume first so I can analyze it."}

    if not chat_model:
        return {"reply": "Chat service is currently unavailable (Model not initialized)."}

    user_query = chat_req.message
    resume_text = chat_context[token]

    if token not in user_chat_histories:
        system_prompt = (
            "You are a Senior Career Strategy Consultant and UI/UX Specialist. "
            "Your objective is to help the user refine their resume for elite tech roles. "
            "Focus on: UI ownership, technical terminology, and user-centric impact.\n\n"
            "--- RESUME CONTEXT ---\n"
            f"{resume_text}\n"
            "--- END RESUME CONTEXT ---\n\n"
            "UI/UX Content Rules:\n"
            "1. Lead with UI Ownership: Always start project bullets with design ownership (e.g., 'Designed a clean, intuitive interface...').\n"
            "2. Use UI Terminology: Replace vague phrases with terms like 'Feedback states', 'User flows', 'Confirmation states', and 'Screen design'.\n"
            "3. Emphasize State Handling: Suggest bullets for loading indicators, success confirmations, and error states.\n"
            "4. Structure Flows: Focus on minimizing steps and optimizing user paths.\n"
            "5. Include Accessibility: Suggest mentions of consistent layouts, readability, and high-contrast color schemes.\n"
            "6. Device Awareness: Highlight responsive design across mobile/web.\n\n"
            "General Guidelines:\n"
            "- Provide specific, actionable improvements for resume sections.\n"
            "- Use a professional, highly competent, and tech-forward tone.\n"
            "- Suggest phrasing that highlights leadership and technical design ownership.\n"
            "- Keep responses concise and focused on high-end career success."
        )
        user_chat_histories[token] = [
            SystemMessage(content=system_prompt)
        ]

    history = user_chat_histories[token]
    history.append(HumanMessage(content=user_query))

    try:
        response = chat_model.invoke(history)
        ai_reply = response.content
        history.append(AIMessage(content=ai_reply))
        if len(history) > 20: 
            user_chat_histories[token] = [history[0]] + history[-19:]

        return {"reply": ai_reply}

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"LLM Error: {e}")
        return {"reply": "I encountered an error while processing your request. Please try again."}
