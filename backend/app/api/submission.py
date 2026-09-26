from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys
import subprocess

router = APIRouter()

@router.post("/validate")
async def validate_submission():
    """Validate submission files using the provided validator."""
    try:
        output_dir = Path("d:/Business entity resolution/outputs")
        test_dir = Path("d:/Business entity resolution/student_resource/dataset/test")
        
        matching_path = output_dir / "matching_results.tsv"
        candidate_path = output_dir / "candidate_pairs.tsv"
        
        if not matching_path.exists():
            raise HTTPException(status_code=400, detail="matching_results.tsv not found. Generate predictions first.")
        
        # Run the validator
        validator_path = Path("d:/Business entity resolution/student_resource/utils/validate_submission.py")
        result = subprocess.run(
            [
                sys.executable,
                str(validator_path),
                "--matching", str(matching_path),
                "--candidate", str(candidate_path),
                "--test-dir", str(test_dir)
            ],
            capture_output=True,
            text=True
        )
        
        # Parse output
        output = result.stdout + result.stderr
        is_valid = result.returncode == 0
        
        return {
            "valid": is_valid,
            "output": output,
            "return_code": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-zip")
async def create_submission_zip():
    """Create submission zip file."""
    try:
        # Run the validation and packaging script
        script_path = Path("d:/Business entity resolution/utils/validate_and_package.py")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd="d:/Business entity resolution"
        )
        
        if result.returncode == 0:
            output_dir = Path("d:/Business entity resolution/outputs")
            zip_files = list(output_dir.glob("*_submission.zip"))
            if zip_files:
                return {
                    "success": True,
                    "zip_path": str(zip_files[0]),
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "output": "Zip file not created"
                }
        else:
            return {
                "success": False,
                "output": result.stdout + result.stderr
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
