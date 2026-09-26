"""
Centralized state manager for the application.
Ensures all API endpoints share the same instances.
"""
from pathlib import Path
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_path = Path("d:/Business entity resolution/student_resource/dataset")
        
        # Import services here to avoid circular imports
        from app.services.data_loader import DataLoader
        from app.services.normalization import Normalizer
        from app.services.blocking import Blocker
        from app.services.features import FeatureEngineer
        from app.ml.model_trainer import ModelTrainer
        
        self.data_loader = DataLoader(self.base_path)
        self.normalizer = Normalizer()
        self.blocker = Blocker()
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        
        # Feature dataframe (shared between features and training)
        self.df_features = None
        
        self._initialized = True
        logger.info("StateManager initialized")
    
    def reset(self):
        """Reset all state (for testing or re-running)."""
        self.data_loader = type(self.data_loader)(self.base_path)
        self.blocker = Blocker()
        self.feature_engineer = FeatureEngineer()
        self.model_trainer = ModelTrainer()
        self.df_features = None
        logger.info("StateManager reset")

# Global state manager instance
state = StateManager()
