from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state

router = APIRouter()

def get_instances():
    return state.data_loader, state.blocker, state.feature_engineer

@router.post("/compute")
async def compute_features():
    """Compute features for all candidate pairs."""
    try:
        if state.blocker.candidate_pairs is None:
            raise HTTPException(status_code=400, detail="No candidates generated yet")
        
        # Fit TF-IDF if not already done
        if state.feature_engineer.tfidf_vectorizer_name is None:
            state.feature_engineer.fit_tfidf(state.data_loader.train_s1, state.data_loader.train_s2, state.data_loader.train_s3)
        
        # Compute features
        df_features = state.feature_engineer.compute_features_batch(
            state.blocker.candidate_pairs,
            state.data_loader.train_s1,
            state.data_loader.train_s2,
            state.data_loader.train_s3
        )
        
        # Store in state for training
        state.df_features = df_features
        
        return {
            "status": "success",
            "feature_rows": len(df_features),
            "feature_columns": len(df_features.columns),
            "feature_names": df_features.columns.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/names")
async def get_feature_names():
    """Get list of feature names."""
    try:
        return {"feature_names": state.feature_engineer.get_feature_names()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
