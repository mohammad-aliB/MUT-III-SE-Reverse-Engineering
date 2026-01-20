#!/usr/bin/env python3
"""
Decrypt all .exdf files in a folder to XML format.
Also recursively copies all non-exdf files to the output folder.

Usage:
    python decrypt_exdf.py <input_folder> <output_folder>
    
Example:
    python decrypt_exdf.py ./mut-3-s3 ./mut-3-s3-with-decrypted-exdfs
"""

import sys
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET


def reverse_bits(byte: int) -> int:
    """Reverse the bits in a byte (bit 0 -> bit 7, bit 1 -> bit 6, etc.)."""
    result = 0
    if byte & 0x01:
        result |= 0x80
    if byte & 0x02:
        result |= 0x40
    if byte & 0x04:
        result |= 0x20
    if byte & 0x08:
        result |= 0x10
    if byte & 0x10:
        result |= 0x08
    if byte & 0x20:
        result |= 0x04
    if byte & 0x40:
        result |= 0x02
    if byte & 0x80:
        result |= 0x01
    return result


def decrypt_exdf(data: bytes) -> bytes:
    """
    Decrypt exdf data using the two-step algorithm:
    1. Reverse bits in each byte
    2. XOR each byte with 0xAA
    """
    # Step 1: Bit reversal
    reversed_data = bytes(reverse_bits(b) for b in data)
    
    # Step 2: XOR with 0xAA
    decrypted = bytes(b ^ 0xAA for b in reversed_data)
    
    return decrypted


def pretty_print_xml(xml_string: str) -> str:
    """Parse and pretty-print XML string."""
    try:
        root = ET.fromstring(xml_string)
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding='unicode')
    except ET.ParseError:
        # If parsing fails, return original string
        return xml_string


def decrypt_exdf_file(input_path: Path, output_path: Path) -> bool:
    """Decrypt a single .exdf file and save as XML."""
    try:
        # Read encrypted data
        encrypted_data = input_path.read_bytes()
        
        # Decrypt
        decrypted_data = decrypt_exdf(encrypted_data)
        
        # Convert to string
        xml_string = decrypted_data.decode('utf-8')
        
        # Pretty print
        formatted_xml = pretty_print_xml(xml_string)
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formatted_xml, encoding='utf-8')
        
        return True
    except Exception as e:
        print(f"  ✗ {input_path.name}: {str(e)}")
        return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python decrypt_exdf.py <input_folder> <output_folder>")
        print("Example: python decrypt_exdf.py ./encrypted ./decrypted")
        sys.exit(1)
    
    input_folder = Path(sys.argv[1]).resolve()
    output_folder = Path(sys.argv[2]).resolve()
    
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        sys.exit(1)
    
    # Find all .exdf files recursively
    exdf_files = list(input_folder.rglob("*.exdf"))
    
    print(f"Found {len(exdf_files)} .exdf files in {input_folder}")
    print(f"Output directory: {output_folder}")
    print("-" * 50)
    
    # Create output directory
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Decrypt each .exdf file
    success = 0
    failed = 0
    
    for exdf_file in sorted(exdf_files):
        # Calculate relative path from input folder
        rel_path = exdf_file.relative_to(input_folder)
        
        # Change extension from .exdf to .xml
        output_rel_path = rel_path.with_suffix('.xml')
        output_path = output_folder / output_rel_path
        
        if decrypt_exdf_file(exdf_file, output_path):
            print(f"  ✓ {rel_path}")
            success += 1
        else:
            failed += 1
    
    print("-" * 50)
    print("Copying non-exdf files...")
    
    # Copy all files that are not .exdf, preserving directory structure
    copied_count = 0
    for file_path in input_folder.rglob("*"):
        if file_path.is_file():
            # Skip .exdf files (already processed)
            if file_path.suffix.lower() == '.exdf':
                continue
            
            # Calculate relative path from input folder
            rel_path = file_path.relative_to(input_folder)
            dest_path = output_folder / rel_path
            
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(file_path, dest_path)
            copied_count += 1
    
    print(f"  ✓ Copied {copied_count} non-exdf files")
    print("-" * 50)
    print(f"Done: {success} files decrypted, {failed} failed, {copied_count} files copied")


if __name__ == "__main__":
    main()

