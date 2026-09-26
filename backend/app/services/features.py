import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from rapidfuzz import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self):
        self.tfidf_vectorizer_name = None
        self.tfidf_vectorizer_address = None
        self.tfidf_matrix_s1_name = None
        self.tfidf_matrix_s2_name = None
        self.tfidf_matrix_s3_name = None
        self.tfidf_matrix_s1_address = None
        self.tfidf_matrix_s2_address = None
        self.tfidf_matrix_s3_address = None
    
    def fit_tfidf(self, df_s1: pd.DataFrame, df_s2: pd.DataFrame, df_s3: pd.DataFrame):
        """Fit TF-IDF vectorizers on training data."""
        logger.info("Fitting TF-IDF vectorizers...")
        
        self.tfidf_vectorizer_name = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        self.tfidf_vectorizer_address = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
        
        # Fit on all names
        all_names = pd.concat([
            df_s1['business_name_normalized'],
            df_s2['business_name_normalized'],
            df_s3['business_name_normalized']
        ]).fillna('')
        self.tfidf_vectorizer_name.fit(all_names)
        
        # Fit on all addresses
        all_addresses = pd.concat([
            df_s1['business_address_normalized'],
            df_s2['business_address_normalized'],
            df_s3['business_address_normalized']
        ]).fillna('')
        self.tfidf_vectorizer_address.fit(all_addresses)
        
        # Transform
        self.tfidf_matrix_s1_name = self.tfidf_vectorizer_name.transform(df_s1['business_name_normalized'].fillna(''))
        self.tfidf_matrix_s2_name = self.tfidf_vectorizer_name.transform(df_s2['business_name_normalized'].fillna(''))
        self.tfidf_matrix_s3_name = self.tfidf_vectorizer_name.transform(df_s3['business_name_normalized'].fillna(''))
        
        self.tfidf_matrix_s1_address = self.tfidf_vectorizer_address.transform(df_s1['business_address_normalized'].fillna(''))
        self.tfidf_matrix_s2_address = self.tfidf_vectorizer_address.transform(df_s2['business_address_normalized'].fillna(''))
        self.tfidf_matrix_s3_address = self.tfidf_vectorizer_address.transform(df_s3['business_address_normalized'].fillna(''))
        
        logger.info("TF-IDF vectorizers fitted and transformed")
    
    def compute_name_features(self, name1: str, name2: str) -> Dict[str, float]:
        """Compute similarity features for business names."""
        if pd.isna(name1) or name1 == '':
            name1 = ''
        if pd.isna(name2) or name2 == '':
            name2 = ''
        
        features = {
            'name_exact_match': float(name1 == name2),
            'name_levenshtein': fuzz.ratio(name1, name2) / 100.0,
            'name_jaro_winkler': fuzz.ratio(name1, name2) / 100.0,  # Use ratio as approximation
            'name_token_sort_ratio': fuzz.token_sort_ratio(name1, name2) / 100.0,
            'name_token_set_ratio': fuzz.token_set_ratio(name1, name2) / 100.0,
        }
        
        # Jaccard similarity
        tokens1 = set(name1.split())
        tokens2 = set(name2.split())
        if tokens1 or tokens2:
            features['name_jaccard'] = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        else:
            features['name_jaccard'] = 0.0
        
        # Length difference
        features['name_length_diff'] = abs(len(name1) - len(name2))
        features['name_token_count_diff'] = abs(len(tokens1) - len(tokens2))
        
        return features
    
    def compute_address_features(self, addr1: str, addr2: str) -> Dict[str, float]:
        """Compute similarity features for addresses."""
        if pd.isna(addr1) or addr1 == '':
            addr1 = ''
        if pd.isna(addr2) or addr2 == '':
            addr2 = ''
        
        features = {
            'address_exact_match': float(addr1 == addr2),
            'address_levenshtein': fuzz.ratio(addr1, addr2) / 100.0,
            'address_jaro_winkler': fuzz.ratio(addr1, addr2) / 100.0,  # Use ratio as approximation
            'address_token_sort_ratio': fuzz.token_sort_ratio(addr1, addr2) / 100.0,
            'address_token_set_ratio': fuzz.token_set_ratio(addr1, addr2) / 100.0,
        }
        
        # Jaccard similarity
        tokens1 = set(addr1.split())
        tokens2 = set(addr2.split())
        if tokens1 or tokens2:
            features['address_jaccard'] = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        else:
            features['address_jaccard'] = 0.0
        
        # Length difference
        features['address_length_diff'] = abs(len(addr1) - len(addr2))
        features['address_token_count_diff'] = abs(len(tokens1) - len(tokens2))
        
        return features
    
    def compute_country_match(self, country1: str, country2: str) -> float:
        """Compute country match feature."""
        return float(country1 == country2)
    
    def compute_features_for_pair(self, row_s1: pd.Series, row_candidate: pd.Series) -> Dict[str, float]:
        """Compute all features for a single pair."""
        features = {}
        
        # Name features
        name_features = self.compute_name_features(
            row_s1['business_name_normalized'],
            row_candidate['business_name_normalized']
        )
        features.update({f'name_{k}': v for k, v in name_features.items()})
        
        # Address features
        address_features = self.compute_address_features(
            row_s1['business_address_normalized'],
            row_candidate['business_address_normalized']
        )
        features.update({f'address_{k}': v for k, v in address_features.items()})
        
        # Country feature
        features['country_match'] = self.compute_country_match(
            row_s1['country'],
            row_candidate['country']
        )
        
        return features
    
    def compute_features_batch(self, candidate_pairs: List[Tuple[str, str]],
                               df_s1: pd.DataFrame, df_s2: pd.DataFrame,
                               df_s3: pd.DataFrame) -> pd.DataFrame:
        """Compute features for all candidate pairs using dict lookups."""
        logger.info(f"Computing features for {len(candidate_pairs):,} candidate pairs...")

        s1_lookup = df_s1.set_index('entity_id').to_dict('index')
        s2_lookup = df_s2.set_index('entity_id').to_dict('index')
        s3_lookup = df_s3.set_index('entity_id').to_dict('index')
        entity_lookup = {**s2_lookup, **s3_lookup}

        return self.compute_features_from_lookups(candidate_pairs, s1_lookup, entity_lookup)

    def compute_features_from_lookups(
        self,
        candidate_pairs: List[Tuple[str, str]],
        s1_lookup: Dict[str, Dict],
        entity_lookup: Dict[str, Dict],
    ) -> pd.DataFrame:
        """
        Compute features using prebuilt entity dicts (used by chunked inference).
        Keys match compute_features_for_pair (name_/address_ prefixed once more
        for compatibility with the existing training feature schema).
        """
        if not candidate_pairs:
            return pd.DataFrame(columns=['source1_entity_id', 'candidate_entity_id'])

        logger.info(f"Computing features for {len(candidate_pairs):,} pairs from lookups...")
        features_list = []
        skipped = 0

        for s1_id, candidate_id in candidate_pairs:
            row_s1 = s1_lookup.get(s1_id)
            row_candidate = entity_lookup.get(candidate_id)
            if row_s1 is None or row_candidate is None:
                skipped += 1
                continue

            features = self.compute_features_for_pair(row_s1, row_candidate)
            features['source1_entity_id'] = s1_id
            features['candidate_entity_id'] = candidate_id
            features_list.append(features)

        df_features = pd.DataFrame(features_list)
        if skipped:
            logger.warning(f"Skipped {skipped:,} pairs with missing entity lookups")
        logger.info(
            f"Computed {len(df_features):,} feature rows with "
            f"{len(df_features.columns)} columns"
        )
        return df_features
    
    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [
            'name_exact_match', 'name_levenshtein', 'name_jaro_winkler',
            'name_token_sort_ratio', 'name_token_set_ratio', 'name_jaccard',
            'name_length_diff', 'name_token_count_diff',
            'address_exact_match', 'address_levenshtein', 'address_jaro_winkler',
            'address_token_sort_ratio', 'address_token_set_ratio', 'address_jaccard',
            'address_length_diff', 'address_token_count_diff',
            'country_match'
        ]
