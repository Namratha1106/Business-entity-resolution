import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score
import joblib
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self, model_dir: str = "backend/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.best_threshold = 0.5
        self.feature_names = []
        self.training_history = {}
    
    def prepare_training_data(self, df_features: pd.DataFrame, 
                              df_ground_truth: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data with labels from ground truth."""
        logger.info("Preparing training data...")
        
        # Parse ground truth to get positive pairs
        positive_pairs = set()
        for _, row in df_ground_truth.iterrows():
            s1_id = row['source1_entity_id']
            matched_ids = str(row['matched_entity_ids']).split(',')
            for matched_id in matched_ids:
                matched_id = matched_id.strip()
                if matched_id:
                    positive_pairs.add((s1_id, matched_id))
        
        # Label candidates
        df_features['label'] = df_features.apply(
            lambda row: 1 if (row['source1_entity_id'], row['candidate_entity_id']) in positive_pairs else 0,
            axis=1
        )
        
        # Get feature columns (exclude non-feature columns)
        feature_cols = [col for col in df_features.columns 
                       if col not in ['source1_entity_id', 'candidate_entity_id', 'label']]
        self.feature_names = feature_cols
        
        X = df_features[feature_cols].fillna(0)
        y = df_features['label']
        
        logger.info(f"Training data: {len(X)} samples, {X.sum()} positives, {(len(X) - X.sum())} negatives")
        
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series, 
                     test_size: float = 0.2) -> Dict[str, Dict]:
        """Train multiple models and compare performance."""
        logger.info("Training models...")
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        models = {
            'logistic_regression': LogisticRegression(
                max_iter=1000, class_weight='balanced', random_state=42
            ),
            'random_forest': RandomForestClassifier(
                n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1
            ),
            'gradient_boosting': GradientBoostingClassifier(
                n_estimators=100, random_state=42
            )
        }
        
        results = {}
        
        for name, model in models.items():
            logger.info(f"Training {name}...")
            model.fit(X_train, y_train)
            
            # Predict probabilities
            y_pred_proba = model.predict_proba(X_val)[:, 1]
            
            # Calculate metrics at default threshold
            y_pred = (y_pred_proba >= 0.5).astype(int)
            precision = precision_score(y_val, y_pred, zero_division=0)
            recall = recall_score(y_val, y_pred, zero_division=0)
            f1 = f1_score(y_val, y_pred, zero_division=0)
            f05 = self.calculate_f05(precision, recall)
            
            results[name] = {
                'model': model,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'f05': f05,
                'probabilities': y_pred_proba
            }
            
            logger.info(f"{name}: P={precision:.4f}, R={recall:.4f}, F0.5={f05:.4f}")
            
            self.models[name] = model
        
        # Select best model by F0.5
        best_name = max(results.keys(), key=lambda k: results[k]['f05'])
        self.best_model = results[best_name]['model']
        self.best_model_name = best_name
        
        logger.info(f"Best model: {best_name} with F0.5={results[best_name]['f05']:.4f}")
        
        self.training_history = results
        return results
    
    def calculate_f05(self, precision: float, recall: float) -> float:
        """Calculate F0.5 score."""
        if precision == 0 and recall == 0:
            return 0.0
        return (1.25 * precision * recall) / (0.25 * precision + recall)
    
    def optimize_threshold(self, X_val: pd.DataFrame, y_val: pd.Series) -> Tuple[float, Dict]:
        """Optimize decision threshold for F0.5 score."""
        logger.info("Optimizing threshold...")
        
        y_pred_proba = self.best_model.predict_proba(X_val)[:, 1]
        
        thresholds = np.arange(0.50, 0.96, 0.01)
        threshold_results = {}
        
        for threshold in thresholds:
            y_pred = (y_pred_proba >= threshold).astype(int)
            precision = precision_score(y_val, y_pred, zero_division=0)
            recall = recall_score(y_val, y_pred, zero_division=0)
            f05 = self.calculate_f05(precision, recall)
            
            threshold_results[float(threshold)] = {
                'threshold': float(threshold),
                'precision': precision,
                'recall': recall,
                'f05': f05
            }
        
        # Select best threshold
        best_threshold = max(threshold_results.keys(), key=lambda k: threshold_results[k]['f05'])
        self.best_threshold = best_threshold
        
        logger.info(f"Best threshold: {best_threshold:.2f} with F0.5={threshold_results[best_threshold]['f05']:.4f}")
        
        return best_threshold, threshold_results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict match probabilities."""
        if self.best_model is None:
            raise ValueError("No model trained. Call train_models first.")
        
        return self.best_model.predict_proba(X)[:, 1]
    
    def save_model(self, model_name: Optional[str] = None):
        """Save the best model to disk."""
        if model_name is None:
            model_name = self.best_model_name
        
        if model_name is None:
            raise ValueError("No model to save")
        
        model_path = self.model_dir / f"{model_name}.joblib"
        joblib.dump(self.models[model_name], model_path)
        
        # Save metadata
        metadata = {
            'model_name': model_name,
            'best_threshold': self.best_threshold,
            'feature_names': self.feature_names
        }
        metadata_path = self.model_dir / "metadata.joblib"
        joblib.dump(metadata, metadata_path)
        
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self, model_name: str):
        """Load a model from disk."""
        model_path = self.model_dir / f"{model_name}.joblib"
        metadata_path = self.model_dir / "metadata.joblib"
        
        self.models[model_name] = joblib.load(model_path)
        metadata = joblib.load(metadata_path)
        
        self.best_model = self.models[model_name]
        self.best_model_name = model_name
        self.best_threshold = metadata['best_threshold']
        self.feature_names = metadata['feature_names']
        
        logger.info(f"Model loaded from {model_path}")
