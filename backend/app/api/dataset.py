from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.utils.state_manager import state

router = APIRouter()

# Default sample for interactive UI — full train is ~12M+ rows and will OOM.
DEFAULT_LOAD_ROWS = 10000


def get_data_loader():
    return state.data_loader


@router.get("/stats")
async def get_dataset_stats():
    """Get dataset statistics."""
    try:
        if state.data_loader.train_s1 is None:
            state.data_loader.load_train_data(nrows=DEFAULT_LOAD_ROWS)
        stats = state.data_loader.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/load", methods=["GET", "POST"])
async def load_dataset(
    nrows: Optional[int] = Query(
        DEFAULT_LOAD_ROWS,
        description="Rows per source to load. Omit or pass null for full files (not recommended).",
    ),
    full: bool = Query(
        False,
        description="If true, load entire train files (very memory-heavy).",
    ),
):
    """Load training dataset into memory (sampled by default for UI use)."""
    try:
        # Force reload so a previous sample doesn't stick when params change
        state.data_loader.train_s1 = None
        state.data_loader.train_s2 = None
        state.data_loader.train_s3 = None
        state.data_loader.train_gt = None

        load_nrows = None if full else nrows
        train_data = state.data_loader.load_train_data(nrows=load_nrows)
        return {
            "status": "success",
            "sampled": load_nrows is not None,
            "nrows": load_nrows,
            "train_rows": {
                "source1": len(train_data["source1"]),
                "source2": len(train_data["source2"]),
                "source3": len(train_data["source3"]),
                "ground_truth": len(train_data["ground_truth"]),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sample/{source}")
async def get_sample(source: str, n: int = 10):
    """Get sample rows from a source."""
    try:
        if state.data_loader.train_s1 is None:
            state.data_loader.load_train_data(nrows=DEFAULT_LOAD_ROWS)

        if source == "source1":
            df = state.data_loader.train_s1.head(n)
        elif source == "source2":
            df = state.data_loader.train_s2.head(n)
        elif source == "source3":
            df = state.data_loader.train_s3.head(n)
        elif source == "ground_truth":
            df = state.data_loader.train_gt.head(n)
        else:
            raise HTTPException(status_code=400, detail="Invalid source")

        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
