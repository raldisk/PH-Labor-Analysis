"""
Export ph_economic_eda.ipynb to a self-contained HTML report.

Usage:
    python scripts/export_html.py

Requires:
    - Notebook must be executed first (all outputs present)
    - pip install nbconvert

Output:
    output/ph_economic_eda.html
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

NB_PATH   = Path(__file__).parent.parent / "notebooks" / "ph_economic_eda.ipynb"
HTML_PATH = Path(__file__).parent.parent / "output" / "ph_economic_eda.html"
HTML_PATH.parent.mkdir(parents=True, exist_ok=True)


def run_notebook() -> None:
    """
    Execute the notebook and write outputs back to the same path.

    Uses --output instead of --inplace so that nbconvert only overwrites
    the file on success. With --inplace, a mid-execution failure (kernel
    crash, timeout, OOM) leaves the .ipynb in a partially-executed state
    with mixed outputs — hard to debug and inconsistent on the next run.
    """
    print("Executing notebook (this may take 1–2 minutes)...")
    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--output", str(NB_PATH),
            "--ExecutePreprocessor.timeout=300",
            "--ExecutePreprocessor.kernel_name=python3",
            str(NB_PATH),
        ],
        capture_output=False,
    )
    if result.returncode != 0:
        print("Notebook execution failed — check cell errors above.")
        sys.exit(1)
    print("Notebook executed successfully.")


def export_html() -> None:
    """Convert executed notebook to standalone HTML."""
    print("Exporting to HTML...")
    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "html",
            "--no-input",            # hide code cells in the report
            "--output", str(HTML_PATH),
            str(NB_PATH),
        ],
        capture_output=False,
    )
    if result.returncode != 0:
        print("HTML export failed.")
        sys.exit(1)
    size_kb = HTML_PATH.stat().st_size // 1024
    print(f"HTML report written: {HTML_PATH}  ({size_kb:,} KB)")


def export_html_with_code() -> None:
    """Export with code cells visible — for technical reviewers."""
    code_path = HTML_PATH.parent / "ph_economic_eda_with_code.html"
    subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "html",
            "--output", str(code_path),
            str(NB_PATH),
        ],
        capture_output=False,
    )
    size_kb = code_path.stat().st_size // 1024
    print(f"HTML with code:      {code_path}  ({size_kb:,} KB)")


if __name__ == "__main__":
    run_notebook()
    export_html()
    export_html_with_code()
    print("\nDone. Share output/ph_economic_eda.html with any stakeholder.")
    print("No Jupyter install required to view it.")
