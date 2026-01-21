from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import uvicorn
import shutil
import os
from parser import parse_pdf_to_json
from llm_service import LLMProvider

app = FastAPI()

class GenerateRequest(BaseModel):
    context: dict
    prompt: str
    model: str

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if file.filename.endswith(".pdf"):
            data = parse_pdf_to_json(temp_file)
        else:
            data = {"error": "Unsupported format"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    return data

@app.post("/generate")
async def generate_content(req: GenerateRequest):
    response = LLMProvider.generate(req.model, req.prompt, req.context)
    return {"response": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
