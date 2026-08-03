#!/usr/bin/env python3
"""Compile Typst with bounded terminal diagnostics and durable artifacts."""
import argparse, subprocess, sys
from pathlib import Path

def compile_typst(input_file, output=None, strict=False):
    output = output or str(Path(input_file).with_suffix(".pdf"))
    cmd = ["typst", "compile", str(input_file), output]
    if strict:
        cmd.insert(2, "--strict")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
        return False
    print(f"✓ PDF generated: {output}")
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compile Typst to PDF")
    p.add_argument("input_file", type=Path)
    p.add_argument("-o", "--output", type=Path)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()
    sys.exit(0 if compile_typst(args.input_file, args.output, args.strict) else 1)
