from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dataset, normalization, blocking, features, training, evaluation, results, submission

app = FastAPI(title="Business Entity Resolution API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dataset.router, prefix="/api/dataset", tags=["dataset"])
app.include_router(normalization.router, prefix="/api/normalization", tags=["normalization"])
app.include_router(blocking.router, prefix="/api/blocking", tags=["blocking"])
app.include_router(features.router, prefix="/api/features", tags=["features"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(results.router, prefix="/api/results", tags=["results"])
app.include_router(submission.router, prefix="/api/submission", tags=["submission"])

@app.get("/")
async def root():
    return {"message": "Business Entity Resolution API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
