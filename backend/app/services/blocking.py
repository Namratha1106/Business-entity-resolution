import pandas as pd
from typing import Dict, List, Tuple, Set, Optional, Iterable
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Blocker:
    def __init__(self):
        self.blocks: Dict[str, Set[Tuple[str, str]]] = defaultdict(set)
        self.candidate_pairs: List[Tuple[str, str]] = []
        self.stats: Dict = {}
        # Prebuilt indexes for chunked full-scale inference
        self.token_index: Dict[str, List[str]] = {}
        self.entity_lookup: Dict[str, Dict[str, str]] = {}
        self.index_stats: Dict = {}

    @staticmethod
    def _name_tokens(name: str) -> List[str]:
        tokens = str(name).split()[:2] if name else []
        return [t for t in tokens if t]

    @staticmethod
    def _block_keys(name: str, country: str) -> List[str]:
        """
        Blocking keys for scale: (first_token|country) and optionally
        (first_two_tokens|country). Country is part of the key so we avoid
        the combinatorial explosion of pure country blocking.
        """
        tokens = Blocker._name_tokens(name)
        if not tokens:
            return []
        country_key = str(country) if country is not None and not pd.isna(country) else ""
        keys = [f"{tokens[0]}|{country_key}"]
        if len(tokens) >= 2:
            keys.append(f"{tokens[0]}|{tokens[1]}|{country_key}")
        return keys

    def _index_dataframe(self, df: pd.DataFrame) -> Tuple[int, int]:
        """Add normalized S2/S3 rows into token_index and entity_lookup."""
        added = 0
        for row in df.itertuples(index=False):
            entity_id = row.entity_id
            name = getattr(row, "business_name_normalized", "") or ""
            address = getattr(row, "business_address_normalized", "") or ""
            country = row.country if hasattr(row, "country") else ""
            if pd.isna(country):
                country = ""

            self.entity_lookup[entity_id] = {
                "business_name_normalized": name,
                "business_address_normalized": address,
                "country": str(country),
            }
            for key in self._block_keys(name, country):
                self.token_index.setdefault(key, []).append(entity_id)
            added += 1
        return added, len(self.token_index)

    def build_indexes(
        self,
        df_s2: pd.DataFrame,
        df_s3: pd.DataFrame,
    ) -> Dict:
        """Build inverted indexes and entity lookups from in-memory S2/S3."""
        logger.info("Building blocking indexes from in-memory S2/S3...")
        self.token_index = {}
        self.entity_lookup = {}
        n2, _ = self._index_dataframe(df_s2)
        n3, n_keys = self._index_dataframe(df_s3)
        self.index_stats = {
            "s2_entities": n2,
            "s3_entities": n3,
            "total_entities": n2 + n3,
            "block_keys": n_keys,
        }
        logger.info(
            f"Indexes built: S2={n2:,}, S3={n3:,}, keys={n_keys:,}"
        )
        return self.index_stats

    def build_indexes_streaming(
        self,
        s2_chunks: Iterable[pd.DataFrame],
        s3_chunks: Iterable[pd.DataFrame],
        normalizer,
    ) -> Dict:
        """
        Stream-normalize S2/S3 and build indexes without holding full frames.
        Suitable for ~10M S2+S3 entities against the 1.7M S1 test set.
        """
        logger.info("Building blocking indexes by streaming S2/S3...")
        self.token_index = {}
        self.entity_lookup = {}
        n2 = n3 = 0

        for i, chunk in enumerate(s2_chunks, start=1):
            chunk = normalizer.normalize_dataframe(chunk, keep_original=False)
            added, _ = self._index_dataframe(chunk)
            n2 += added
            if i % 5 == 0 or added:
                logger.info(f"  Indexed S2 chunk {i}: total S2={n2:,}")

        for i, chunk in enumerate(s3_chunks, start=1):
            chunk = normalizer.normalize_dataframe(chunk, keep_original=False)
            added, _ = self._index_dataframe(chunk)
            n3 += added
            if i % 5 == 0 or added:
                logger.info(f"  Indexed S3 chunk {i}: total S3={n3:,}")

        self.index_stats = {
            "s2_entities": n2,
            "s3_entities": n3,
            "total_entities": n2 + n3,
            "block_keys": len(self.token_index),
        }
        logger.info(
            f"Streaming indexes complete: S2={n2:,}, S3={n3:,}, "
            f"keys={len(self.token_index):,}"
        )
        return self.index_stats

    def generate_candidates_from_indexes(
        self,
        df_s1: pd.DataFrame,
        max_candidates_per_entity: Optional[int] = 100,
    ) -> List[Tuple[str, str]]:
        """Generate candidates for an S1 chunk using prebuilt indexes."""
        if not self.token_index:
            raise ValueError("Indexes not built. Call build_indexes first.")

        candidates: List[Tuple[str, str]] = []
        for row in df_s1.itertuples(index=False):
            s1_id = row.entity_id
            name = getattr(row, "business_name_normalized", "") or ""
            country = row.country if hasattr(row, "country") else ""
            if pd.isna(country):
                country = ""

            seen: Set[str] = set()
            for key in self._block_keys(name, country):
                for cand_id in self.token_index.get(key, ()):
                    if cand_id not in seen:
                        seen.add(cand_id)
                        candidates.append((s1_id, cand_id))
                        if (
                            max_candidates_per_entity is not None
                            and len(seen) >= max_candidates_per_entity
                        ):
                            break
                if (
                    max_candidates_per_entity is not None
                    and len(seen) >= max_candidates_per_entity
                ):
                    break

        self.candidate_pairs = candidates
        self.stats = {
            "strategy": "indexed_name_country",
            "s1_count": len(df_s1),
            "candidate_count": len(candidates),
            "candidates_per_s1": len(candidates) / len(df_s1) if len(df_s1) else 0,
            "index_entities": len(self.entity_lookup),
        }
        return candidates

    def create_name_token_blocks(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, 
                                  df_s3: pd.DataFrame) -> List[Tuple[str, str]]:
        """Create blocks based on name tokens (first 2 tokens)."""
        logger.info("Creating name token blocks...")
        
        # Build inverted index for S2 and S3
        s2_index = defaultdict(list)
        s3_index = defaultdict(list)
        
        for _, row in df_s2.iterrows():
            tokens = str(row['business_name_normalized']).split()[:2]
            for token in tokens:
                if token:
                    s2_index[token].append(row['entity_id'])
        
        for _, row in df_s3.iterrows():
            tokens = str(row['business_name_normalized']).split()[:2]
            for token in tokens:
                if token:
                    s3_index[token].append(row['entity_id'])
        
        # Generate candidates
        candidates = set()
        for _, row in df_s1.iterrows():
            s1_id = row['entity_id']
            tokens = str(row['business_name_normalized']).split()[:2]
            
            for token in tokens:
                if token in s2_index:
                    for s2_id in s2_index[token]:
                        candidates.add((s1_id, s2_id))
                if token in s3_index:
                    for s3_id in s3_index[token]:
                        candidates.add((s1_id, s3_id))
        
        logger.info(f"Name token blocks generated {len(candidates):,} candidates")
        return list(candidates)
    
    def create_country_blocks(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, 
                               df_s3: pd.DataFrame) -> List[Tuple[str, str]]:
        """Create blocks based on country."""
        logger.info("Creating country blocks...")
        
        # Group by country
        s2_by_country = df_s2.groupby('country')['entity_id'].apply(list).to_dict()
        s3_by_country = df_s3.groupby('country')['entity_id'].apply(list).to_dict()
        
        candidates = set()
        for _, row in df_s1.iterrows():
            s1_id = row['entity_id']
            country = row['country']
            
            if country in s2_by_country:
                for s2_id in s2_by_country[country]:
                    candidates.add((s1_id, s2_id))
            
            if country in s3_by_country:
                for s3_id in s3_by_country[country]:
                    candidates.add((s1_id, s3_id))
        
        logger.info(f"Country blocks generated {len(candidates):,} candidates")
        return list(candidates)
    
    def create_combined_blocks(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, 
                                df_s3: pd.DataFrame) -> List[Tuple[str, str]]:
        """Create blocks combining multiple strategies."""
        logger.info("Creating combined blocks...")
        
        # Get candidates from multiple strategies
        name_candidates = set(self.create_name_token_blocks(df_s1, df_s2, df_s3))
        country_candidates = set(self.create_country_blocks(df_s1, df_s2, df_s3))
        
        # Union of all strategies
        combined = name_candidates | country_candidates
        
        logger.info(f"Combined blocks generated {len(combined):,} candidates")
        return list(combined)
    
    def generate_candidates(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, 
                            df_s3: pd.DataFrame, strategy: str = "combined", sample_size: int = None) -> List[Tuple[str, str]]:
        """Generate candidate pairs using blocking strategy with optional sampling for memory efficiency."""
        # Apply sampling if specified to reduce memory usage
        if sample_size and len(df_s1) > sample_size:
            df_s1 = df_s1.sample(n=sample_size, random_state=42)
        
        self.candidate_pairs = []
        self.stats = {"strategy": strategy, "s1_count": len(df_s1), "s2_count": len(df_s2), "s3_count": len(df_s3)}
        
        if strategy == "name_tokens":
            self.candidate_pairs = self.create_name_token_blocks(df_s1, df_s2, df_s3)
        elif strategy == "country":
            self.candidate_pairs = self.create_country_blocks(df_s1, df_s2, df_s3)
        elif strategy == "combined":
            self.candidate_pairs = self.create_combined_blocks(df_s1, df_s2, df_s3)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        self.stats["candidate_count"] = len(self.candidate_pairs)
        self._compute_stats(df_s1, df_s2, df_s3)
        return self.candidate_pairs
    
    def _compute_stats(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, 
                       df_s3: pd.DataFrame):
        """Compute blocking statistics."""
        total_possible = len(df_s1) * (len(df_s2) + len(df_s3))
        reduction_ratio = 1 - (len(self.candidate_pairs) / total_possible) if total_possible else 0
        
        self.stats = {
            "total_s1_entities": len(df_s1),
            "total_s2_entities": len(df_s2),
            "total_s3_entities": len(df_s3),
            "candidate_pairs": len(self.candidate_pairs),
            "total_possible_pairs": total_possible,
            "reduction_ratio": reduction_ratio,
            "candidates_per_s1": len(self.candidate_pairs) / len(df_s1) if len(df_s1) > 0 else 0
        }
    
    def get_candidate_pairs_dataframe(self) -> pd.DataFrame:
        """Return candidate pairs as a dataframe."""
        if not self.candidate_pairs:
            return pd.DataFrame(columns=['source1_entity_id', 'candidate_entity_id'])
        
        df = pd.DataFrame(self.candidate_pairs, columns=['source1_entity_id', 'candidate_entity_id'])
        return df
    
    def get_stats(self) -> Dict:
        """Return blocking statistics."""
        return self.stats
