from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent.orchestrator import RepoRankAgent
from dotenv import load_dotenv
import uvicorn

load_dotenv()


app = FastAPI(title="RepoRank", description="Open Source Impact & Funding Readiness Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")

agent = RepoRankAgent()


class AnalyzeRequest(BaseModel):
    repo: str          # e.g. "owner/repo"
    ecosystem: str     # "python" | "npm" | "other"


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if "/" not in req.repo:
        raise HTTPException(status_code=400, detail="Repo must be in 'owner/repo' format")
    try:
        result = await agent.run(repo=req.repo, ecosystem=req.ecosystem)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "sailing"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
