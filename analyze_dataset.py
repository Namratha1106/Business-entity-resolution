import pandas as pd
import os
from pathlib import Path

# Define paths
base_path = Path("d:/Business entity resolution/student_resource/dataset")
train_path = base_path / "train"
test_path = base_path / "test"

print("=" * 80)
print("DATASET ANALYSIS - Amazon ML Challenge")
print("=" * 80)

# Load train files
print("\n[1] LOADING TRAIN FILES...")
train_s1 = pd.read_csv(train_path / "train_source1.tsv", sep="\t")
train_s2 = pd.read_csv(train_path / "train_source2.tsv", sep="\t")
train_s3 = pd.read_csv(train_path / "train_source3.tsv", sep="\t")
train_gt = pd.read_csv(train_path / "train_ground_truth.tsv", sep="\t")

print(f"✓ train_source1.tsv: {len(train_s1):,} rows, {len(train_s1.columns)} columns")
print(f"✓ train_source2.tsv: {len(train_s2):,} rows, {len(train_s2.columns)} columns")
print(f"✓ train_source3.tsv: {len(train_s3):,} rows, {len(train_s3.columns)} columns")
print(f"✓ train_ground_truth.tsv: {len(train_gt):,} rows, {len(train_gt.columns)} columns")

# Load test files with chunking for memory efficiency
print("\n[2] LOADING TEST FILES...")
def count_rows_tsv(filepath):
    count = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            count += 1
    return count - 1  # Subtract header

test_s1_rows = count_rows_tsv(test_path / "test_source1.tsv")
test_s2_rows = count_rows_tsv(test_path / "test_source2.tsv")
test_s3_rows = count_rows_tsv(test_path / "test_source3.tsv")

# Load just first few rows to get columns
test_s1 = pd.read_csv(test_path / "test_source1.tsv", sep="\t", nrows=100)
test_s2 = pd.read_csv(test_path / "test_source2.tsv", sep="\t", nrows=100)
test_s3 = pd.read_csv(test_path / "test_source3.tsv", sep="\t", nrows=100)

print(f"✓ test_source1.tsv: {test_s1_rows:,} rows, {len(test_s1.columns)} columns")
print(f"✓ test_source2.tsv: {test_s2_rows:,} rows, {len(test_s2.columns)} columns")
print(f"✓ test_source3.tsv: {test_s3_rows:,} rows, {len(test_s3.columns)} columns")

# Column information
print("\n[3] COLUMN INFORMATION")
print("\nSource 1 columns:", list(train_s1.columns))
print("Source 2 columns:", list(train_s2.columns))
print("Source 3 columns:", list(train_s3.columns))
print("Ground truth columns:", list(train_gt.columns))

# Missing values
print("\n[4] MISSING VALUES")
print("\nTrain Source 1 missing values:")
print(train_s1.isnull().sum())
print("\nTrain Source 2 missing values:")
print(train_s2.isnull().sum())
print("\nTrain Source 3 missing values:")
print(train_s3.isnull().sum())

# Duplicate IDs
print("\n[5] DUPLICATE ID ANALYSIS")
print(f"\nTrain Source 1 duplicate IDs: {train_s1.iloc[:, 0].duplicated().sum()}")
print(f"Train Source 2 duplicate IDs: {train_s2.iloc[:, 0].duplicated().sum()}")
print(f"Train Source 3 duplicate IDs: {train_s3.iloc[:, 0].duplicated().sum()}")
print(f"Test Source 1 duplicate IDs: {test_s1.iloc[:, 0].duplicated().sum()}")
print(f"Test Source 2 duplicate IDs: {test_s2.iloc[:, 0].duplicated().sum()}")
print(f"Test Source 3 duplicate IDs: {test_s3.iloc[:, 0].duplicated().sum()}")

# Country analysis (if country column exists)
print("\n[6] COUNTRY ANALYSIS")
if 'country' in train_s1.columns:
    print(f"\nTrain Source 1 unique countries: {train_s1['country'].nunique()}")
    print("Top 10 countries in Source 1:")
    print(train_s1['country'].value_counts().head(10))
if 'country' in train_s2.columns:
    print(f"\nTrain Source 2 unique countries: {train_s2['country'].nunique()}")
    print("Top 10 countries in Source 2:")
    print(train_s2['country'].value_counts().head(10))
if 'country' in train_s3.columns:
    print(f"\nTrain Source 3 unique countries: {train_s3['country'].nunique()}")
    print("Top 10 countries in Source 3:")
    print(train_s3['country'].value_counts().head(10))

# Business name analysis
print("\n[7] BUSINESS NAME ANALYSIS")
if 'name' in train_s1.columns:
    print(f"\nTrain Source 1 unique business names: {train_s1['name'].nunique()}")
if 'name' in train_s2.columns:
    print(f"Train Source 2 unique business names: {train_s2['name'].nunique()}")
if 'name' in train_s3.columns:
    print(f"Train Source 3 unique business names: {train_s3['name'].nunique()}")

# Ground truth structure
print("\n[8] GROUND TRUTH STRUCTURE")
print(f"\nGround truth shape: {train_gt.shape}")
print("Ground truth sample rows:")
print(train_gt.head(10))

# Match distribution
print("\n[9] MATCH DISTRIBUTION")
if len(train_gt.columns) >= 2:
    # Parse comma-separated matched_entity_ids
    train_gt['match_count'] = train_gt.iloc[:, 1].apply(lambda x: len(str(x).split(',')) if pd.notna(x) and str(x) != '' else 0)
    
    print(f"\nSource 1 entities with matches: {(train_gt['match_count'] > 0).sum()}")
    print(f"Source 1 entities with no matches: {(train_gt['match_count'] == 0).sum()}")
    print(f"\nMatch distribution:")
    print(f"  0 matches: {(train_gt['match_count'] == 0).sum()} ({(train_gt['match_count'] == 0).sum()/len(train_gt)*100:.2f}%)")
    print(f"  1 match: {(train_gt['match_count'] == 1).sum()} ({(train_gt['match_count'] == 1).sum()/len(train_gt)*100:.2f}%)")
    print(f"  2 matches: {(train_gt['match_count'] == 2).sum()} ({(train_gt['match_count'] == 2).sum()/len(train_gt)*100:.2f}%)")
    print(f"  3 matches: {(train_gt['match_count'] == 3).sum()} ({(train_gt['match_count'] == 3).sum()/len(train_gt)*100:.2f}%)")
    print(f"  4 matches: {(train_gt['match_count'] == 4).sum()} ({(train_gt['match_count'] == 4).sum()/len(train_gt)*100:.2f}%)")
    print(f"  5 matches: {(train_gt['match_count'] == 5).sum()} ({(train_gt['match_count'] == 5).sum()/len(train_gt)*100:.2f}%)")
    print(f"  6-10 matches: {((train_gt['match_count'] >= 6) & (train_gt['match_count'] <= 10)).sum()} ({((train_gt['match_count'] >= 6) & (train_gt['match_count'] <= 10)).sum()/len(train_gt)*100:.2f}%)")
    print(f"  11+ matches: {(train_gt['match_count'] >= 11).sum()} ({(train_gt['match_count'] >= 11).sum()/len(train_gt)*100:.2f}%)")
    print(f"\nMax matches for a single entity: {train_gt['match_count'].max()}")
    print(f"Average matches per entity: {train_gt['match_count'].mean():.2f}")
    print(f"Total matches across all entities: {train_gt['match_count'].sum():,}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
