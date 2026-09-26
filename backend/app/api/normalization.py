from fastapi import APIRouter, HTTPException
from app.utils.state_manager import state

router = APIRouter()

def get_instances():
    return state.data_loader, state.normalizer

@router.post("/apply")
async def apply_normalization():
    """Apply normalization to all dataframes."""
    try:
        if state.data_loader.train_s1 is None:
            state.data_loader.load_train_data()
        
        # Normalize all dataframes
        state.data_loader.train_s1 = state.normalizer.normalize_dataframe(state.data_loader.train_s1)
        state.data_loader.train_s2 = state.normalizer.normalize_dataframe(state.data_loader.train_s2)
        state.data_loader.train_s3 = state.normalizer.normalize_dataframe(state.data_loader.train_s3)
        
        return {
            "status": "success",
            "message": "Normalization applied to all dataframes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_normalization_stats():
    """Get normalization statistics."""
    try:
        if state.data_loader.train_s1 is None or 'business_name_normalized' not in state.data_loader.train_s1.columns:
            raise HTTPException(status_code=400, detail="Normalization not applied yet")
        
        stats = {
            "source1": state.normalizer.get_normalization_stats(
                state.data_loader.train_s1[['business_name', 'business_address']],
                state.data_loader.train_s1[['business_name_normalized', 'business_address_normalized']]
            ),
            "source2": state.normalizer.get_normalization_stats(
                state.data_loader.train_s2[['business_name', 'business_address']],
                state.data_loader.train_s2[['business_name_normalized', 'business_address_normalized']]
            ),
            "source3": state.normalizer.get_normalization_stats(
                state.data_loader.train_s3[['business_name', 'business_address']],
                state.data_loader.train_s3[['business_name_normalized', 'business_address_normalized']]
            )
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
