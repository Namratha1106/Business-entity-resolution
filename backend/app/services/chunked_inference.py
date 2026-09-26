"""
Chunked full-scale test inference for ~1.7M Source-1 entities.

Builds S2/S3 blocking indexes once (streamed), then processes S1 in chunks,
writing matching_results.tsv and candidate_pairs.tsv incrementally.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from app.services.blocking import Blocker
from app.services.data_loader import DataLoader
from app.services.features import FeatureEngineer
from app.services.normalization import Normalizer
from app.ml.model_trainer import ModelTrainer

logger = logging.getLogger(__name__)

MATCHING_HEADER = ["source1_entity_id", "matched_entity_ids"]
CANDIDATE_HEADER = ["source1_entity_id", "candidate_entity_ids"]


def _aggregate_candidates(
    pairs: List[Tuple[str, str]], s1_ids: List[str]
) -> Dict[str, List[str]]:
    """Group (s1, cand) pairs into s1 -> [cand, ...] preserving order."""
    grouped: Dict[str, List[str]] = {s1_id: [] for s1_id in s1_ids}
    seen: Dict[str, set] = {s1_id: set() for s1_id in s1_ids}
    for s1_id, cand_id in pairs:
        if s1_id not in seen:
            grouped[s1_id] = []
            seen[s1_id] = set()
        if cand_id not in seen[s1_id]:
            seen[s1_id].add(cand_id)
            grouped[s1_id].append(cand_id)
    return grouped


def run_chunked_test_inference(
    data_loader: DataLoader,
    normalizer: Normalizer,
    blocker: Blocker,
    feature_engineer: FeatureEngineer,
    model_trainer: ModelTrainer,
    output_dir: Path,
    chunk_size: int = 5000,
    index_chunk_size: int = 100000,
    max_candidates_per_entity: int = 100,
    threshold: Optional[float] = None,
    resume: bool = True,
    max_chunks: Optional[int] = None,
) -> Dict:
    """
    Process the full test set (~1.7M S1 entities) in chunks.

    Returns a summary dict with counts and output paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    matching_path = output_dir / "matching_results.tsv"
    candidate_path = output_dir / "candidate_pairs.tsv"
    checkpoint_path = output_dir / "chunk_checkpoint.json"

    if threshold is None:
        threshold = getattr(model_trainer, "best_threshold", 0.5) or 0.5

    full_s1_count = data_loader.count_test_s1_rows()
    num_chunks = (full_s1_count + chunk_size - 1) // chunk_size if full_s1_count else 0
    if max_chunks is not None:
        num_chunks = min(num_chunks, max_chunks)
    expected_entities = min(full_s1_count, num_chunks * chunk_size) if num_chunks else 0
    logger.info(
        f"Full test S1 size: {full_s1_count:,} entities "
        f"(processing {num_chunks:,} chunks of {chunk_size:,})"
    )

    # --- Build S2/S3 indexes once ---
    if not blocker.token_index:
        logger.info("Building S2/S3 blocking indexes (streamed)...")
        blocker.build_indexes_streaming(
            data_loader.iter_test_source_chunks("source2", index_chunk_size),
            data_loader.iter_test_source_chunks("source3", index_chunk_size),
            normalizer,
        )
    else:
        logger.info(
            f"Reusing existing indexes "
            f"({len(blocker.entity_lookup):,} entities)"
        )

    start_chunk = 0
    matched_entities = 0
    total_candidates = 0
    if resume and checkpoint_path.exists() and matching_path.exists():
        try:
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
            start_chunk = int(ckpt.get("next_chunk", 0))
            matched_entities = int(ckpt.get("matched_entities", 0))
            total_candidates = int(ckpt.get("total_candidates", 0))
            logger.info(f"Resuming from chunk {start_chunk + 1}/{num_chunks}")
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f"Could not read checkpoint, starting fresh: {e}")
            start_chunk = 0
            matched_entities = 0
            total_candidates = 0

    write_header = start_chunk == 0
    if write_header:
        matching_path.write_text(
            "\t".join(MATCHING_HEADER) + "\n", encoding="utf-8"
        )
        candidate_path.write_text(
            "\t".join(CANDIDATE_HEADER) + "\n", encoding="utf-8"
        )

    entities_processed = start_chunk * chunk_size
    feature_cols = list(model_trainer.feature_names) if model_trainer.feature_names else None

    for chunk_idx, s1_chunk in enumerate(data_loader.iter_test_s1_chunks(chunk_size)):
        if chunk_idx < start_chunk:
            continue
        if max_chunks is not None and chunk_idx >= max_chunks:
            logger.info(f"Reached max_chunks={max_chunks}, stopping.")
            break

        logger.info(
            f"Processing chunk {chunk_idx + 1}/{num_chunks} "
            f"({len(s1_chunk):,} entities)..."
        )

        s1_chunk = normalizer.normalize_dataframe(s1_chunk, keep_original=False)
        s1_ids = s1_chunk["entity_id"].tolist()

        candidates = blocker.generate_candidates_from_indexes(
            s1_chunk, max_candidates_per_entity=max_candidates_per_entity
        )
        logger.info(f"  Candidates: {len(candidates):,}")
        total_candidates += len(candidates)

        s1_lookup = s1_chunk.set_index("entity_id").to_dict("index")
        matches: Dict[str, List[str]] = {s1_id: [] for s1_id in s1_ids}

        if candidates:
            df_features = feature_engineer.compute_features_from_lookups(
                candidates, s1_lookup, blocker.entity_lookup
            )
            if len(df_features) > 0:
                if feature_cols is None:
                    feature_cols = [
                        c for c in df_features.columns
                        if c not in (
                            "source1_entity_id",
                            "candidate_entity_id",
                            "label",
                            "probability",
                            "prediction",
                        )
                    ]
                # Align columns with training schema
                for col in feature_cols:
                    if col not in df_features.columns:
                        df_features[col] = 0.0
                X_test = df_features[feature_cols].fillna(0)
                probs = model_trainer.predict(X_test)
                df_features["probability"] = probs
                df_features["prediction"] = (probs >= threshold).astype(int)

                pos = df_features[df_features["prediction"] == 1]
                for s1_id, group in pos.groupby("source1_entity_id"):
                    matches[s1_id] = group["candidate_entity_id"].tolist()

        cand_grouped = _aggregate_candidates(candidates, s1_ids)

        with open(matching_path, "a", encoding="utf-8") as mf, open(
            candidate_path, "a", encoding="utf-8"
        ) as cf:
            for s1_id in s1_ids:
                matched = matches.get(s1_id, [])
                if matched:
                    matched_entities += 1
                mf.write(f"{s1_id}\t{','.join(matched)}\n")
                cf.write(f"{s1_id}\t{','.join(cand_grouped.get(s1_id, []))}\n")

        entities_processed += len(s1_ids)

        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "next_chunk": chunk_idx + 1,
                    "entities_processed": entities_processed,
                    "matched_entities": matched_entities,
                    "total_candidates": total_candidates,
                    "total_s1": full_s1_count,
                    "expected_entities": expected_entities,
                },
                f,
            )

        logger.info(
            f"  Chunk done. Processed {entities_processed:,}/{expected_entities:,} "
            f"({100.0 * entities_processed / expected_entities:.1f}%), "
            f"matched so far: {matched_entities:,}"
        )

    # Clear checkpoint on successful completion
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    summary = {
        "status": "success",
        "total_predictions": entities_processed,
        "matched_entities": matched_entities,
        "unmatched_entities": entities_processed - matched_entities,
        "total_candidates": total_candidates,
        "chunk_size": chunk_size,
        "threshold": threshold,
        "index_stats": blocker.index_stats,
        "matching_path": str(matching_path),
        "candidate_path": str(candidate_path),
        "output_path": str(output_dir),
    }
    logger.info(
        f"Chunked inference complete: {entities_processed:,} entities, "
        f"{matched_entities:,} with matches, {total_candidates:,} candidates"
    )
    return summary
