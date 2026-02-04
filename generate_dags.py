#!/usr/bin/env python3
"""
Generate HTML DAG visualizations from Rhylthyme program files.

Usage:
    python generate_dags.py                           # All examples → dag_outputs/
    python generate_dags.py program.json              # Single file
    python generate_dags.py *.json -o output/         # Multiple files to output dir
    python generate_dags.py ../rhylthyme-examples/programs/  # Entire directory
"""

#!/usr/bin/env python3
"""
Generate HTML DAG visualizations from Rhylthyme program files.

Usage:
    python generate_dags.py                           # All examples → dag_outputs/
    python generate_dags.py program.json              # Single file
    python generate_dags.py *.json -o output/         # Multiple files to output dir
    python generate_dags.py ../rhylthyme-examples/programs/  # Entire directory
"""
import sys
import argparse
from pathlib import Path

from rhylthyme_web.web.web_visualizer import generate_dag_visualization


def find_program_files(paths):
    """Find all JSON/YAML program files from given paths."""
    files = []
    for path in paths:
        p = Path(path)
        if p.is_dir():
            files.extend(p.glob("*.json"))
            files.extend(p.glob("*.yaml"))
            files.extend(p.glob("*.yml"))
        elif p.is_file() and p.suffix in (".json", ".yaml", ".yml"):
            files.append(p)
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML DAG visualizations from Rhylthyme programs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    Generate DAGs for all examples
  %(prog)s program.json                       Single file (opens in browser)
  %(prog)s *.json -o output/                  Multiple files to output directory
  %(prog)s ../rhylthyme-examples/programs/    Process entire directory
  %(prog)s program.json --no-browser          Don't open browser
        """,
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=["../rhylthyme-examples/programs"],
        help="Program files or directories (default: ../rhylthyme-examples/programs)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="dag_outputs",
        help="Output directory (default: dag_outputs)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser (default for multiple files)",
    )

    args = parser.parse_args()

    # Find all program files
    program_files = find_program_files(args.files)

    if not program_files:
        print("No program files found.", file=sys.stderr)
        return 1

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Only open browser for single file unless --no-browser
    open_browser = len(program_files) == 1 and not args.no_browser

    success = 0
    failed = 0

    for program_file in program_files:
        output_path = output_dir / f"{program_file.stem}.html"
        try:
            generate_dag_visualization(
                str(program_file),
                str(output_path),
                open_browser=open_browser,
            )
            print(f"✓ {program_file.name}")
            success += 1
        except Exception as e:
            print(f"✗ {program_file.name}: {e}", file=sys.stderr)
            failed += 1

    # Summary
    print(f"\nGenerated {success} DAGs in {output_dir}/", end="")
    if failed:
        print(f" ({failed} failed)")
        return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
