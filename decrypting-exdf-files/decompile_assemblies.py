#!/usr/bin/env python3
"""
Decompile all .NET assemblies (DLL, EXE) in a folder using ILSpy command-line tool.
In addition to the decompiled assemblies, this script also recursively copies all non-decompiled files to the output folder.

Usage:
    python decompile_assemblies.py <input_folder> <output_folder>
    
Example:
    python decompile_assemblies.py desktop/mut-3-deobfuscated desktop/decompiled
"""

import argparse
import subprocess
import sys
import shutil
from pathlib import Path

# File extensions to decompile
EXTENSIONS = {".dll", ".exe"}


def decompile_assembly(assembly_path: Path, output_dir: Path) -> bool:
    """Decompile a single .NET assembly using ilspycmd."""
    # Create output subdirectory named after the assembly
    assembly_name = assembly_path.stem
    output_subdir = output_dir / assembly_name
    output_subdir.mkdir(parents=True, exist_ok=True)
    
    cmd = ["ilspycmd", "-r", str(assembly_path.parent), "-o", str(output_subdir), str(assembly_path)]
    # Note: ilspycmd generates files named <AssemblyName>.decompiled.cs
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"  ✓ {assembly_path}")
            return True
        else:
            print(f"  ✗ {assembly_path}: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ {assembly_path}: Timeout")
        return False
    except FileNotFoundError:
        print("Error: ilspycmd not found. Install with: dotnet tool install -g ilspycmd")
        sys.exit(1)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Decompile .NET assemblies using ILSpy command-line tool."
    )
    parser.add_argument("input_folder", type=Path, help="Folder containing assemblies")
    parser.add_argument("output_folder", type=Path, help="Output folder for decompiled code")
    return parser.parse_args()


def main():
    args = parse_args()
    input_folder = args.input_folder.resolve()
    output_folder = args.output_folder.resolve()
    
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        sys.exit(1)
    
    # Find all .NET assembly files recursively
    assemblies = [f for f in input_folder.rglob("*") if f.suffix.lower() in EXTENSIONS]
    
    print(f"Found {len(assemblies)} assemblies in {input_folder} (recursive)")
    print(f"  Extensions: {', '.join(EXTENSIONS)}")
    print(f"Output directory: {output_folder}")
    print("-" * 50)
    
    # Create output directory
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Track decompiled files
    decompiled_files = set()
    
    # Decompile each assembly
    success = 0
    failed = 0
    
    for assembly in sorted(assemblies):
        # Calculate relative path from input folder
        rel_path = assembly.relative_to(input_folder)
        # Output directory maintains the same structure as input
        assembly_output_base = output_folder / rel_path.parent
        
        if decompile_assembly(assembly, assembly_output_base):
            decompiled_files.add(assembly)
            success += 1
        else:
            failed += 1
    
    print("-" * 50)
    print("Copying non-decompiled files...")
    
    # Copy all files that are not decompiled, preserving directory structure
    copied_count = 0
    for file_path in input_folder.rglob("*"):
        if file_path.is_file():
            # Skip if this file was decompiled
            if file_path in decompiled_files:
                continue
            
            # Calculate relative path from input folder
            rel_path = file_path.relative_to(input_folder)
            dest_path = output_folder / rel_path
            
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(file_path, dest_path)
            copied_count += 1
    
    print(f"  ✓ Copied {copied_count} non-decompiled files")
    print("-" * 50)
    print(f"Done: {success} assemblies decompiled, {failed} failed, {copied_count} files copied")
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

