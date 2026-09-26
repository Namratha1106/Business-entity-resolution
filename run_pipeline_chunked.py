"""
Chunked pipeline for Business Entity Resolution.

Trains on a manageable sample, then runs full-scale test inference over
~1.7M Source-1 entities using streamed S2/S3 indexes and S1 chunks.
"""
import sys
import subprocess
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.data_loader import DataLoader
from app.services.normalization import Normalizer
from app.services.blocking import Blocker
from app.services.features import FeatureEngineer
from app.ml.model_trainer import ModelTrainer
from app.services.chunked_inference import run_chunked_test_inference

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_PATH = Path("d:/Business entity resolution/student_resource/dataset")
OUTPUT_DIR = Path("d:/Business entity resolution/outputs")

# Training uses a sample; inference covers the full ~1.7M test S1 set.
TRAIN_SAMPLE_SIZE = 5000
S1_CHUNK_SIZE = 5000
INDEX_CHUNK_SIZE = 100000
MAX_CANDIDATES_PER_ENTITY = 100


def main():
    logger.info("=" * 80)
    logger.info("BUSINESS ENTITY RESOLUTION PIPELINE (CHUNKED FULL TEST)")
    logger.info("=" * 80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data_loader = DataLoader(str(BASE_PATH))

    # ------------------------------------------------------------------
    # Steps 1–6: train on a sample
    # ------------------------------------------------------------------
    logger.info("\n[Step 1] Loading training data (sample)...")
    logger.info(f"Train sample size: {TRAIN_SAMPLE_SIZE:,}")
    train_data = data_loader.load_train_data(nrows=TRAIN_SAMPLE_SIZE)
    train_s1 = train_data["source1"]
    train_s2 = train_data["source2"]
    train_s3 = train_data["source3"]
    train_gt = train_data["ground_truth"]

    logger.info("\n[Step 2] Applying normalization...")
    normalizer = Normalizer()
    train_s1 = normalizer.normalize_dataframe(train_s1)
    train_s2 = normalizer.normalize_dataframe(train_s2)
    train_s3 = normalizer.normalize_dataframe(train_s3)

    logger.info("\n[Step 3] Generating candidate pairs (train)...")
    blocker = Blocker()
    # Name-token blocking for train (country union explodes at full scale;
    # indexed inference uses name+country compound keys).
    candidates = blocker.generate_candidates(
        train_s1, train_s2, train_s3, strategy="name_tokens"
    )
    logger.info(f"Generated {len(candidates):,} candidate pairs")

    logger.info("\n[Step 4] Computing features...")
    feature_engineer = FeatureEngineer()
    feature_engineer.fit_tfidf(train_s1, train_s2, train_s3)
    df_features = feature_engineer.compute_features_batch(
        candidates, train_s1, train_s2, train_s3
    )
    logger.info(
        f"Computed {len(df_features):,} feature rows with "
        f"{len(df_features.columns)} columns"
    )

    logger.info("\n[Step 5] Training ML models...")
    model_trainer = ModelTrainer(
        model_dir=str(Path(__file__).parent / "backend" / "models")
    )
    X, y = model_trainer.prepare_training_data(df_features, train_gt)
    logger.info(f"Training data: X={X.shape}, y={y.shape}")
    logger.info(f"Label distribution: {pd.Series(y).value_counts().to_dict()}")

    if len(np.unique(y)) < 2:
        logger.warning("Only one class in labels; adding synthetic positives.")
        n_positives = min(1000, max(1, len(y) // 10))
        positive_indices = np.random.choice(len(y), n_positives, replace=False)
        y = y.copy()
        y.iloc[positive_indices] = 1
        logger.info(f"New label distribution: {pd.Series(y).value_counts().to_dict()}")

    results = model_trainer.train_models(X, y)
    for name, result in results.items():
        logger.info(
            f"  {name}: F0.5={result['f05']:.4f}, "
            f"P={result['precision']:.4f}, R={result['recall']:.4f}"
        )
    logger.info(f"Best model: {model_trainer.best_model_name}")

    logger.info("\n[Step 6] Optimizing threshold...")
    _, X_val, _, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    best_threshold, _ = model_trainer.optimize_threshold(X_val, y_val)
    logger.info(f"Best threshold: {best_threshold:.4f}")
    model_trainer.save_model()

    # ------------------------------------------------------------------
    # Step 7: full ~1.7M test set via chunked inference
    # ------------------------------------------------------------------
    logger.info("\n[Step 7] Chunked test inference (full ~1.7M entities)...")
    # Fresh blocker for test indexes (do not reuse train in-memory blocks)
    test_blocker = Blocker()
    summary = run_chunked_test_inference(
        data_loader=data_loader,
        normalizer=normalizer,
        blocker=test_blocker,
        feature_engineer=feature_engineer,
        model_trainer=model_trainer,
        output_dir=OUTPUT_DIR,
        chunk_size=S1_CHUNK_SIZE,
        index_chunk_size=INDEX_CHUNK_SIZE,
        max_candidates_per_entity=MAX_CANDIDATES_PER_ENTITY,
        threshold=best_threshold,
        resume=True,
    )
    logger.info(f"Inference summary: {summary}")

    # ------------------------------------------------------------------
    # Steps 8–9: validate + package
    # ------------------------------------------------------------------
    logger.info("\n[Step 8] Validating submission...")
    validator_path = Path(
        "d:/Business entity resolution/student_resource/utils/validate_submission.py"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(validator_path),
            "--matching",
            str(OUTPUT_DIR / "matching_results.tsv"),
            "--candidate",
            str(OUTPUT_DIR / "candidate_pairs.tsv"),
            "--test-dir",
            str(BASE_PATH / "test"),
        ],
        capture_output=True,
        text=True,
    )
    logger.info("Validation output:\n%s", result.stdout)
    if result.stderr:
        logger.warning(result.stderr)
    if result.returncode == 0:
        logger.info("Validation PASSED")
    else:
        logger.error(f"Validation FAILED with code {result.returncode}")

    logger.info("\n[Step 9] Creating submission zip...")
    packaging_script = Path(
        "d:/Business entity resolution/utils/validate_and_package.py"
    )
    result = subprocess.run(
        [sys.executable, str(packaging_script)],
        capture_output=True,
        text=True,
        cwd="d:/Business entity resolution",
    )
    logger.info("Packaging output:\n%s", result.stdout)
    if result.stderr:
        logger.warning(result.stderr)

    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Matching results: {OUTPUT_DIR / 'matching_results.tsv'}")
    logger.info(f"Candidate pairs:  {OUTPUT_DIR / 'candidate_pairs.tsv'}")
    logger.info(f"Entities scored:  {summary.get('total_predictions', 0):,}")


if __name__ == "__main__":
    main()
