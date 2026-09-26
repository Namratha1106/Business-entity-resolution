from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state

router = APIRouter()

def get_instances():
    return state.data_loader, state.blocker, state.feature_engineer, state.model_trainer

@router.get("/metrics")
async def get_evaluation_metrics():
    """Get evaluation metrics for the trained model."""
    try:
        if state.model_trainer.best_model is None:
            raise HTTPException(status_code=400, detail="Model not trained yet")
        
        results = state.model_trainer.training_history
        
        formatted_results = {}
        for name, result in results.items():
            formatted_results[name] = {
                "precision": result["precision"],
                "recall": result["recall"],
                "f1": result["f1"],
                "f05": result["f05"]
            }
        
        return {
            "best_model": state.model_trainer.best_model_name,
            "best_threshold": state.model_trainer.best_threshold,
            "results": formatted_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
