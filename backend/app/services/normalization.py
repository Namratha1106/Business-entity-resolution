import pandas as pd
import re
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Normalizer:
    def __init__(self):
        self.legal_suffixes = [
            'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
            'llc', 'co', 'company', 'pty', 'pvt', 'private', 'plc', 'gmbh',
            'ag', 'sa', 'sarl', 'spa', 'sro', 'kft', 'zoo', 'ood', 'ad'
        ]
    
    def normalize_text(self, text: str) -> str:
        """Normalize text by lowercasing, removing punctuation, and standardizing whitespace."""
        if pd.isna(text) or text == '':
            return ''
        
        text = str(text).lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with space
        text = re.sub(r'\s+', ' ', text)  # Standardize whitespace
        text = text.strip()
        
        return text
    
    def normalize_name(self, name: str) -> str:
        """Normalize business name with additional rules."""
        if pd.isna(name) or name == '':
            return ''
        
        normalized = self.normalize_text(name)
        
        # Replace "&" with "and"
        normalized = normalized.replace('&', ' and ')
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove legal suffixes
        words = normalized.split()
        filtered_words = [w for w in words if w not in self.legal_suffixes]
        normalized = ' '.join(filtered_words)
        
        return normalized
    
    def normalize_address(self, address: str) -> str:
        """Normalize address with additional rules."""
        if pd.isna(address) or address == '':
            return ''
        
        normalized = self.normalize_text(address)
        
        # Replace common abbreviations
        abbrev_map = {
            'st': 'street',
            'rd': 'road',
            'ave': 'avenue',
            'blvd': 'boulevard',
            'ln': 'lane',
            'dr': 'drive',
            'ct': 'court',
            'pl': 'place',
            'sq': 'square',
            'apt': 'apartment',
            'suite': 'suite',
            'ste': 'suite',
            'fl': 'floor',
            'bldg': 'building'
        }
        
        words = normalized.split()
        normalized_words = [abbrev_map.get(w, w) for w in words]
        normalized = ' '.join(normalized_words)
        
        return normalized
    
    def normalize_dataframe(self, df: pd.DataFrame, keep_original: bool = True) -> pd.DataFrame:
        """Normalize all text columns in a dataframe."""
        df = df.copy()
        
        if keep_original:
            df['business_name_original'] = df['business_name']
            df['business_address_original'] = df['business_address']
        
        df['business_name_normalized'] = df['business_name'].apply(self.normalize_name)
        df['business_address_normalized'] = df['business_address'].apply(self.normalize_address)
        
        return df
    
    def get_normalization_stats(self, df_original: pd.DataFrame, df_normalized: pd.DataFrame) -> Dict:
        """Compute normalization statistics."""
        stats = {
            "total_rows": len(df_original),
            "name_changes": int((df_original['business_name'] != df_normalized['business_name_normalized']).sum()),
            "address_changes": int((df_original['business_address'] != df_normalized['business_address_normalized']).sum()),
            "empty_names_after_norm": int((df_normalized['business_name_normalized'] == '').sum()),
            "empty_addresses_after_norm": int((df_normalized['business_address_normalized'] == '').sum())
        }
        return stats
