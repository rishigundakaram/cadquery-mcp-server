#!/usr/bin/env python3
"""
Evaluation harness for the CAD verification MCP tool.

This script tests the verify_cad_query function against a set of test models
with known expected results to measure verification accuracy.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Import the server module
sys.path.append(str(Path(__file__).parent.parent))
import server


def load_test_cases() -> dict[str, dict[str, str]]:
    """Load test cases from folder structure."""
    test_cases_dir = Path(__file__).parent / "test_cases"
    if not test_cases_dir.exists():
        raise FileNotFoundError(f"Test cases directory not found: {test_cases_dir}")

    test_cases = {}
    for case_dir in test_cases_dir.iterdir():
        if not case_dir.is_dir():
            continue
            
        model_file = case_dir / "model.py"
        criteria_file = case_dir / "criteria.txt"
        result_file = case_dir / "result.txt"
        
        if all(f.exists() for f in [model_file, criteria_file, result_file]):
            test_cases[case_dir.name] = {
                "model_path": str(model_file),
                "criteria": criteria_file.read_text().strip(),
                "expected": result_file.read_text().strip()
            }
    
    return test_cases


def generate_visual_outputs(model_file: Path, output_dir: Path) -> dict[str, str]:
    """Generate SVG visual outputs for a model file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find the root project directory (where src/ is located)
    project_root = Path(__file__).parent.parent

    outputs = {}

    try:
        # Generate SVG views using the render_views script
        render_script = project_root / "src" / "ai_3d_print" / "render_views.py"
        if render_script.exists():
            result = subprocess.run(
                ["uv", "run", "python", str(render_script), str(model_file)],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Move generated SVG files to the output directory
                model_name = model_file.stem
                svg_patterns = [
                    f"{model_name}_top.svg",
                    f"{model_name}_front.svg",
                    f"{model_name}_right.svg",
                    f"{model_name}_iso.svg",
                ]

                for svg_file in svg_patterns:
                    src_path = project_root / "outputs" / svg_file
                    if src_path.exists():
                        dst_path = output_dir / svg_file
                        src_path.rename(dst_path)
                        outputs[svg_file] = str(dst_path)

                outputs["generation_status"] = "success"
            else:
                outputs["generation_status"] = f"failed: {result.stderr}"
        else:
            outputs["generation_status"] = "render script not found"

    except Exception as e:
        outputs["generation_status"] = f"error: {e}"

    return outputs


def run_single_test(test_name: str, test_data: dict[str, str], base_output_dir: Path) -> dict[str, Any]:
    """Run verification on a single test model."""
    model_file = Path(test_data["model_path"])
    print(f"📝 Testing: {test_name}")

    # Create output directory for this specific test within the timestamped directory
    model_output_dir = base_output_dir / test_name

    # Run the verification using the server function
    result = server.verify_cad_query(test_data["model_path"], test_data["criteria"])
    
    # Move generated outputs to the timestamped directory
    model_name = model_file.stem
    # Files are generated in evaluations/test_cases/outputs/model/ (always named "model")
    default_outputs_dir = Path(__file__).parent / "test_cases" / "outputs" / "model"
    
    if default_outputs_dir.exists():
        # Create the model-specific directory in our timestamped output
        model_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Move all files from default output to our timestamped directory
        for output_file in default_outputs_dir.iterdir():
            if output_file.is_file():
                dest_file = model_output_dir / output_file.name
                shutil.move(str(output_file), str(dest_file))
        
        # Remove the empty default directory
        default_outputs_dir.rmdir()

    # Generate visual outputs
    print(f"   Generating visual outputs...")
    visual_outputs = generate_visual_outputs(model_file, model_output_dir)

    # Check if result matches expectation
    actual_status = result["status"]
    expected_status = test_data["expected"]

    is_correct = actual_status == expected_status

    print(f"   Expected: {expected_status}")
    print(f"   Actual:   {actual_status}")
    print(f"   Result:   {'✅ PASS' if is_correct else '❌ FAIL'}")
    print(f"   Visual:   {visual_outputs.get('generation_status', 'unknown')}")

    if not is_correct:
        print(f"   Details:  {result.get('details', 'N/A')}")

    return {
        "test_name": test_name,
        "expected": expected_status,
        "actual": actual_status,
        "correct": is_correct,
        "result": result,
        "visual_outputs": visual_outputs,
        "output_dir": str(model_output_dir),
    }


def run_evaluation() -> tuple[dict[str, Any], Path]:
    """Run evaluation on all test models."""
    print("🚀 CAD Verification Evaluation Harness")
    print("=" * 50)
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output_dir = Path(__file__).parent / "test_outputs" / timestamp
    base_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {base_output_dir}")

    # Load test cases
    try:
        test_cases = load_test_cases()
        print(f"📋 Loaded {len(test_cases)} test cases")
    except Exception as e:
        print(f"❌ Error loading test cases: {e}")
        return {"error": str(e)}

    # Run tests
    results = []
    correct_count = 0
    total_count = 0
    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0

    print("\n🧪 Running Tests:")
    print("-" * 30)

    for test_name, test_data in test_cases.items():
        test_result = run_single_test(test_name, test_data, base_output_dir)
        results.append(test_result)

        if test_result["correct"]:
            correct_count += 1
            
        # Calculate confusion matrix values
        expected = test_result["expected"]
        actual = test_result["actual"]
        
        if expected == "PASS" and actual == "PASS":
            true_positives += 1
        elif expected == "FAIL" and actual == "FAIL":
            true_negatives += 1
        elif expected == "FAIL" and actual == "PASS":
            false_positives += 1
        elif expected == "PASS" and actual == "FAIL":
            false_negatives += 1
            
        total_count += 1
        print()  # Empty line for readability

    # Calculate metrics
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
    
    # Calculate precision, recall, F1
    precision = (true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 0
    recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) > 0 else 0
    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    # Print summary
    print("📊 Evaluation Summary:")
    print("=" * 30)
    print(f"Total Tests:    {total_count}")
    print(f"Correct:        {correct_count}")
    print(f"Incorrect:      {total_count - correct_count}")
    print(f"Accuracy:       {accuracy:.1f}%")
    print(f"Precision:      {precision:.3f}")
    print(f"Recall:         {recall:.3f}")
    print(f"F1 Score:       {f1_score:.3f}")
    print(f"Output Directory: {base_output_dir}")
    
    # Print confusion matrix
    print("\n📋 Confusion Matrix:")
    print("=" * 20)
    print(f"                Predicted")
    print(f"              PASS  FAIL")
    print(f"Actual PASS   {true_positives:4d}  {false_negatives:4d}")
    print(f"       FAIL   {false_positives:4d}  {true_negatives:4d}")

    if accuracy == 100:
        print("🎉 Perfect score! All tests passed.")
    elif accuracy >= 80:
        print("✅ Good performance, minor issues to address.")
    else:
        print("⚠️  Significant issues detected, verification logic needs improvement.")

    evaluation_summary = {
        "timestamp": timestamp,
        "output_directory": str(base_output_dir),
        "total_tests": total_count,
        "correct": correct_count,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "confusion_matrix": {
            "true_positives": true_positives,
            "true_negatives": true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        },
        "results": results,
    }
    
    return evaluation_summary, base_output_dir


def main():
    """Main function."""
    try:
        evaluation_results, output_dir = run_evaluation()

        # Save detailed results in the timestamped directory
        results_file = output_dir / "evaluation_results.json"
        with open(results_file, "w") as f:
            json.dump(evaluation_results, f, indent=2)

        # Also save a copy in the main evaluations directory for easy access
        latest_results_file = Path(__file__).parent / "latest_evaluation_results.json"
        with open(latest_results_file, "w") as f:
            json.dump(evaluation_results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")
        print(f"📄 Latest results also saved to: {latest_results_file}")

        # Exit with appropriate code
        if evaluation_results.get("accuracy", 0) == 100:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
