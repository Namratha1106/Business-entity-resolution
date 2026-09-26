from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state
from app.services.chunked_inference import run_chunked_test_inference
from app.services.blocking import Blocker
from pathlib import Path
import pandas as pd

router = APIRouter()

def get_instances():
    return state.data_loader, state.blocker, state.feature_engineer, state.model_trainer

@router.post("/predict")
async def generate_predictions(chunk_size: int = 5000, max_candidates: int = 100):
    """
    Generate predictions on the full test set using chunked inference.

    Streams S2/S3 into blocking indexes once, then processes ~1.7M S1
    entities in chunks to avoid loading all test frames into memory.
    """
    try:
        if state.model_trainer.best_model is None:
            raise HTTPException(
                status_code=400,
                detail="No trained model available. Train a model first.",
            )

        output_dir = Path("d:/Business entity resolution/outputs")
        # Use a dedicated blocker so train-time candidates are not mixed in
        test_blocker = Blocker()

        summary = run_chunked_test_inference(
            data_loader=state.data_loader,
            normalizer=state.normalizer,
            blocker=test_blocker,
            feature_engineer=state.feature_engineer,
            model_trainer=state.model_trainer,
            output_dir=output_dir,
            chunk_size=chunk_size,
            max_candidates_per_entity=max_candidates,
            threshold=state.model_trainer.best_threshold,
            resume=True,
        )
        # Keep latest blocker indexes available for inspection if desired
        state.blocker = test_blocker
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results")
async def get_results(limit: int = 100):
    """Get prediction results (sample)."""
    try:
        output_path = Path("d:/Business entity resolution/outputs/matching_results.tsv")
        if not output_path.exists():
            raise HTTPException(status_code=400, detail="Results not generated yet")
        
        df = pd.read_csv(output_path, sep="\t")
        return df.head(limit).to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
