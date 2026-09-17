from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import uvicorn

app = FastAPI(title="ADS Quiz API", description="Servidor de API para el Quiz interactivo de ADS")

# Base directory for absolute path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Helper to load questions
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

# Endpoints
@app.get("/api/questions")
async def get_questions():
    questions = load_questions()
    if not questions:
        raise HTTPException(status_code=500, detail="Base de datos de preguntas no encontrada o vacía.")
    return questions

@app.get("/api/questions/{q_id}")
async def get_question(q_id: str):
    questions = load_questions()
    for q in questions:
        if q["id"] == q_id:
            return q
    raise HTTPException(status_code=404, detail=f"Pregunta con id {q_id} no encontrada.")

@app.get("/api/categories")
async def get_categories():
    questions = load_questions()
    categories = sorted(list(set(q["category"] for q in questions if "category" in q)))
    return categories

# Serve static files from frontend UI
# We mount static directory at "/" so it serves index.html at root
# But first, check if static directory exists; if not, create it
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Mount static files at root or serve index.html directly
@app.get("/")
async def read_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Servidor backend corriendo. La carpeta 'static/' está vacía o no tiene index.html."}

# Mount the static directory for CSS/JS
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    # Start the server on port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
