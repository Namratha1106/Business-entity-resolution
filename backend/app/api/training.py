from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state

router = APIRouter()

def get_instances():
    return state.data_loader, state.blocker, state.feature_engineer, state.model_trainer

@router.post("/train")
async def train_models():
    """Train ML models on computed features."""
    try:
        if state.df_features is None:
            raise HTTPException(status_code=400, detail="Features not computed yet")
        
        # Prepare training data
        X, y = state.model_trainer.prepare_training_data(state.df_features, state.data_loader.train_gt)
        
        # Train models
        results = state.model_trainer.train_models(X, y)
        
        # Format results for response
        formatted_results = {}
        for name, result in results.items():
            formatted_results[name] = {
                "precision": result["precision"],
                "recall": result["recall"],
                "f1": result["f1"],
                "f05": result["f05"]
            }
        
        return {
            "status": "success",
            "best_model": state.model_trainer.best_model_name,
            "results": formatted_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_threshold():
    """Optimize decision threshold for F0.5."""
    try:
        if state.df_features is None:
            raise HTTPException(status_code=400, detail="Features not computed yet")
        
        # Prepare training data
        X, y = state.model_trainer.prepare_training_data(state.df_features, state.data_loader.train_gt)
        
        # Split for validation
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Optimize threshold
        best_threshold, threshold_results = state.model_trainer.optimize_threshold(X_val, y_val)
        
        return {
            "status": "success",
            "best_threshold": best_threshold,
            "threshold_results": threshold_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_model():
    """Save the trained model."""
    try:
        state.model_trainer.save_model()
        return {"status": "success", "message": "Model saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
