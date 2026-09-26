from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state

router = APIRouter()

def get_instances():
    return state.data_loader, state.blocker

@router.post("/generate")
async def generate_candidates(strategy: str = "combined", sample_size: int = 10000):
    """Generate candidate pairs using specified strategy with optional sampling for memory efficiency."""
    try:
        if state.data_loader.train_s1 is None or 'business_name_normalized' not in state.data_loader.train_s1.columns:
            raise HTTPException(status_code=400, detail="Data not loaded or normalized")
        
        candidates = state.blocker.generate_candidates(
            state.data_loader.train_s1,
            state.data_loader.train_s2,
            state.data_loader.train_s3,
            strategy=strategy,
            sample_size=sample_size
        )
        
        return {
            "status": "success",
            "candidate_count": len(candidates),
            "strategy": strategy,
            "sample_size": sample_size,
            "stats": state.blocker.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_blocking_stats():
    """Get blocking statistics."""
    try:
        return state.blocker.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/candidates")
async def get_candidates(limit: int = 100):
    """Get candidate pairs (sample)."""
    try:
        if state.blocker.candidate_pairs is None:
            raise HTTPException(status_code=400, detail="No candidates generated yet")
        
        df = state.blocker.get_candidate_pairs_dataframe()
        return df.head(limit).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
