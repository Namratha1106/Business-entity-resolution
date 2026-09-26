import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional, Iterator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENTITY_DTYPE = {
    'entity_id': 'string',
    'business_name': 'string',
    'business_address': 'string',
    'country': 'string'
}

GT_DTYPE = {
    'source1_entity_id': 'string',
    'matched_entity_ids': 'string'
}


class DataLoader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.train_path = self.base_path / "train"
        self.test_path = self.base_path / "test"
        
        self.train_s1: Optional[pd.DataFrame] = None
        self.train_s2: Optional[pd.DataFrame] = None
        self.train_s3: Optional[pd.DataFrame] = None
        self.train_gt: Optional[pd.DataFrame] = None
        self.test_s1: Optional[pd.DataFrame] = None
        self.test_s2: Optional[pd.DataFrame] = None
        self.test_s3: Optional[pd.DataFrame] = None
        
        self.stats: Dict = {}
    
    def load_train_data(self, nrows: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """Load training data from TSV files with memory-efficient dtypes."""
        if self.train_s1 is not None and nrows is None:
            return {"source1": self.train_s1, "source2": self.train_s2, "source3": self.train_s3, "ground_truth": self.train_gt}
        
        self.train_s1 = pd.read_csv(
            self.train_path / "train_source1.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        self.train_s2 = pd.read_csv(
            self.train_path / "train_source2.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        self.train_s3 = pd.read_csv(
            self.train_path / "train_source3.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        self.train_gt = pd.read_csv(
            self.train_path / "train_ground_truth.tsv", sep="\t", dtype=GT_DTYPE, nrows=nrows
        )
        
        logger.info(f"Loaded train S1: {len(self.train_s1):,} rows")
        logger.info(f"Loaded train S2: {len(self.train_s2):,} rows")
        logger.info(f"Loaded train S3: {len(self.train_s3):,} rows")
        logger.info(f"Loaded train GT: {len(self.train_gt):,} rows")
        
        return {"source1": self.train_s1, "source2": self.train_s2, "source3": self.train_s3, "ground_truth": self.train_gt}
    
    def load_test_data(self, nrows: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """Load all test data files. Prefer iter_test_s1_chunks for full-scale runs."""
        logger.info("Loading test data...")
        
        self.test_s1 = pd.read_csv(
            self.test_path / "test_source1.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        self.test_s2 = pd.read_csv(
            self.test_path / "test_source2.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        self.test_s3 = pd.read_csv(
            self.test_path / "test_source3.tsv", sep="\t", dtype=ENTITY_DTYPE, nrows=nrows
        )
        
        logger.info(f"Loaded test S1: {len(self.test_s1):,} rows")
        logger.info(f"Loaded test S2: {len(self.test_s2):,} rows")
        logger.info(f"Loaded test S3: {len(self.test_s3):,} rows")
        
        return {
            "source1": self.test_s1,
            "source2": self.test_s2,
            "source3": self.test_s3
        }

    def count_rows(self, path: Path) -> int:
        """Count data rows in a TSV (excludes header) without loading the file."""
        with open(path, "r", encoding="utf-8") as f:
            # subtract 1 for header
            return max(sum(1 for _ in f) - 1, 0)

    def count_test_s1_rows(self) -> int:
        """Return number of entities in test Source-1 (~1.7M on full set)."""
        return self.count_rows(self.test_path / "test_source1.tsv")

    def iter_test_s1_chunks(self, chunk_size: int = 5000) -> Iterator[pd.DataFrame]:
        """Stream test Source-1 in fixed-size chunks (correct header handling)."""
        path = self.test_path / "test_source1.tsv"
        logger.info(f"Streaming test S1 from {path} in chunks of {chunk_size:,}")
        reader = pd.read_csv(
            path, sep="\t", dtype=ENTITY_DTYPE, chunksize=chunk_size
        )
        for chunk in reader:
            yield chunk

    def iter_test_source_chunks(
        self, source: str, chunk_size: int = 100000
    ) -> Iterator[pd.DataFrame]:
        """Stream a test source file (source2 or source3) in chunks."""
        filename = f"test_{source}.tsv"
        path = self.test_path / filename
        if not path.exists():
            raise FileNotFoundError(path)
        reader = pd.read_csv(
            path, sep="\t", dtype=ENTITY_DTYPE, chunksize=chunk_size
        )
        for chunk in reader:
            yield chunk

    def load_test_s1_ids(self) -> pd.Series:
        """Load only test S1 entity IDs (memory-light)."""
        df = pd.read_csv(
            self.test_path / "test_source1.tsv",
            sep="\t",
            dtype={'entity_id': 'string'},
            usecols=['entity_id']
        )
        return df['entity_id']
    
    def get_statistics(self) -> Dict:
        """Compute dataset statistics."""
        if self.train_s1 is None:
            self.load_train_data()
        
        stats = {
            "train": {
                "source1_rows": len(self.train_s1),
                "source2_rows": len(self.train_s2),
                "source3_rows": len(self.train_s3),
                "ground_truth_rows": len(self.train_gt),
                "source1_columns": list(self.train_s1.columns),
                "source2_columns": list(self.train_s2.columns),
                "source3_columns": list(self.train_s3.columns),
                "ground_truth_columns": list(self.train_gt.columns),
                "missing_values": {
                    "source1": self.train_s1.isnull().sum().to_dict(),
                    "source2": self.train_s2.isnull().sum().to_dict(),
                    "source3": self.train_s3.isnull().sum().to_dict()
                },
                "duplicate_ids": {
                    "source1": int(self.train_s1['entity_id'].duplicated().sum()),
                    "source2": int(self.train_s2['entity_id'].duplicated().sum()),
                    "source3": int(self.train_s3['entity_id'].duplicated().sum())
                },
                "countries": {
                    "source1": self.train_s1['country'].value_counts().to_dict(),
                    "source2": self.train_s2['country'].value_counts().to_dict(),
                    "source3": self.train_s3['country'].value_counts().to_dict()
                }
            },
            "match_distribution": self._compute_match_distribution()
        }
        
        self.stats = stats
        return stats
    
    def _compute_match_distribution(self) -> Dict:
        """Compute match distribution from ground truth using chunking for memory efficiency."""
        if self.train_gt is None:
            return {}
        
        # Process in chunks to avoid memory issues
        chunk_size = 100000
        total = len(self.train_gt)
        
        entities_with_matches = 0
        entities_without_matches = 0
        total_matches = 0
        max_matches = 0
        distribution = {
            "0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6-10": 0, "11+": 0
        }
        
        for i in range(0, total, chunk_size):
            chunk = self.train_gt.iloc[i:i+chunk_size].copy()
            chunk['match_count'] = chunk['matched_entity_ids'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) and str(x) != '' else 0
            )
            
            entities_with_matches += (chunk['match_count'] > 0).sum()
            entities_without_matches += (chunk['match_count'] == 0).sum()
            total_matches += chunk['match_count'].sum()
            chunk_max = chunk['match_count'].max()
            if chunk_max > max_matches:
                max_matches = chunk_max
            
            distribution["0"] += (chunk['match_count'] == 0).sum()
            distribution["1"] += (chunk['match_count'] == 1).sum()
            distribution["2"] += (chunk['match_count'] == 2).sum()
            distribution["3"] += (chunk['match_count'] == 3).sum()
            distribution["4"] += (chunk['match_count'] == 4).sum()
            distribution["5"] += (chunk['match_count'] == 5).sum()
            distribution["6-10"] += ((chunk['match_count'] >= 6) & (chunk['match_count'] <= 10)).sum()
            distribution["11+"] += (chunk['match_count'] >= 11).sum()
        
        avg_matches = total_matches / total if total > 0 else 0
        
        return {
            "total_entities": total,
            "entities_with_matches": int(entities_with_matches),
            "entities_without_matches": int(entities_without_matches),
            "distribution": {k: int(v) for k, v in distribution.items()},
            "max_matches": int(max_matches),
            "avg_matches": float(avg_matches),
            "total_matches": int(total_matches)
        }
    
    def get_train_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Return all training dataframes."""
        if self.train_s1 is None:
            self.load_train_data()
        return self.train_s1, self.train_s2, self.train_s3, self.train_gt
    
    def get_test_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Return all test dataframes."""
        if self.test_s1 is None:
            self.load_test_data()
        return self.test_s1, self.test_s2, self.test_s3
