#!/usr/bin/env python3
"""
Wrapper script to validate submission and generate submission zip.
"""
import sys
import os
import zipfile
from pathlib import Path

# Add student_resource to path to import their validator
sys.path.insert(0, str(Path(__file__).parent.parent / "student_resource"))
from utils.validate_submission import validate

def validate_submission():
    """Validate the submission files."""
    output_dir = Path("d:/Business entity resolution/outputs")
    test_dir = Path("d:/Business entity resolution/student_resource/dataset/test")
    
    matching_path = output_dir / "matching_results.tsv"
    candidate_path = output_dir / "candidate_pairs.tsv"
    
    print("Validating submission files...")
    print(f"  matching: {matching_path}")
    print(f"  candidate: {candidate_path}")
    print(f"  test dir: {test_dir}")
    
    errors, warnings = validate(
        str(matching_path),
        str(candidate_path),
        str(test_dir),
        check_ids=False
    )
    
    print()
    for warning in warnings:
        print(f"WARNING: {warning}")
    
    if errors:
        print(f"SUBMISSION INVALID — {len(errors)} issue(s) to fix:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    else:
        print("SUBMISSION VALID")
        return True

def create_submission_zip(team_name="team_submission"):
    """Create the submission zip file."""
    print(f"\nCreating submission zip: {team_name}_submission.zip")
    
    output_dir = Path("d:/Business entity resolution/outputs")
    zip_path = output_dir / f"{team_name}_submission.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add output files
        zipf.write(output_dir / "matching_results.tsv", "output/matching_results.tsv")
        zipf.write(output_dir / "candidate_pairs.tsv", "output/candidate_pairs.tsv")
        
        # Add backend code
        backend_dir = Path("d:/Business entity resolution/backend")
        for root, dirs, files in os.walk(backend_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    arcname = f"code/business_entity_resolution/{file_path.relative_to(backend_dir)}"
                    zipf.write(file_path, arcname)
        
        # Add README
        readme_path = Path("d:/Business entity resolution/backend/README.md")
        if readme_path.exists():
            zipf.write(readme_path, "code/business_entity_resolution/README.md")
        
        # Add requirements
        req_path = Path("d:/Business entity resolution/backend/requirements.txt")
        if req_path.exists():
            zipf.write(req_path, "code/business_entity_resolution/requirements.txt")
        
        # Add documentation template
        doc_path = Path("d:/Business entity resolution/student_resource/Documentation_template.md")
        if doc_path.exists():
            zipf.write(doc_path, "Documentation_template.md")
    
    print(f"Submission zip created: {zip_path}")
    return str(zip_path)

def main():
    """Main function."""
    # Validate first
    is_valid = validate_submission()
    
    if is_valid:
        # Create zip
        zip_path = create_submission_zip()
        print(f"\n✓ Submission ready: {zip_path}")
        return 0
    else:
        print("\n✗ Fix validation errors before creating submission")
        return 1

if __name__ == "__main__":
    sys.exit(main())
