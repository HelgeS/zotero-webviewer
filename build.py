#!/usr/bin/env python3
"""
Simple build script for the Literature Webviewer.
This script provides an easy way to build the static website.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def find_rdf_file():
    """Find RDF files in the current directory."""
    rdf_files = []
    
    # Common RDF file names
    common_names = ['library.rdf', 'full.rdf', 'sample.rdf', 'zotero.rdf']
    
    for name in common_names:
        if Path(name).exists():
            rdf_files.append(name)
    
    # Look for any .rdf or .xml files
    for pattern in ['*.rdf', '*.xml']:
        rdf_files.extend(Path('.').glob(pattern))
    
    return [str(f) for f in rdf_files]


def main():
    parser = argparse.ArgumentParser(
        description='Build Literature Webviewer static website',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                          # Auto-detect RDF file
  python build.py --input library.rdf     # Specify RDF file
  python build.py --production             # Production build
  python build.py --output my-site        # Custom output directory
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        help='Input RDF file path (auto-detected if not specified)'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory (default: output)'
    )
    parser.add_argument(
        '--production', '-p',
        action='store_true',
        help='Enable production optimizations (minification, compression)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate generated files (default: enabled)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip validation of generated files'
    )
    
    args = parser.parse_args()
    
    # Find RDF file if not specified
    if not args.input:
        rdf_files = find_rdf_file()
        if not rdf_files:
            print("Error: No RDF file found.")
            print("Please specify an RDF file with --input or place an RDF file in the current directory.")
            print("\nTo export from Zotero:")
            print("1. File → Export Library...")
            print("2. Choose 'Zotero RDF' format")
            print("3. Save as 'library.rdf' in this directory")
            return 1
        
        args.input = rdf_files[0]
        if len(rdf_files) > 1:
            print(f"Multiple RDF files found. Using: {args.input}")
            print(f"Other files: {', '.join(rdf_files[1:])}")
        else:
            print(f"Using RDF file: {args.input}")
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Build command
    cmd = [
        sys.executable, '-m', 'zotero_webviewer.cli',
        'build',
        '--input', args.input,
        '--output', args.output
    ]
    
    if args.production:
        cmd.append('--production')
    
    if args.verbose:
        cmd.append('--verbose')
    
    if args.no_validate:
        cmd.append('--no-validate')
    elif args.validate:
        cmd.append('--validate')
    
    # Print build information
    print("Building Literature Webviewer...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Production: {'Yes' if args.production else 'No'}")
    print()
    
    # Run build command
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✓ Build completed successfully!")
        print(f"Website generated in: {args.output}")
        
        if args.production:
            print("\nProduction optimizations applied:")
            print("- CSS and JavaScript minified")
            print("- JSON files compressed")
            print("- Gzip versions created")
            print("- GitHub Pages configuration added")
        
        print("\nTo view your site:")
        print(f"1. Open {args.output}/index.html in a web browser")
        print(f"2. Or serve with: python -m http.server -d {args.output}")
        
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed with exit code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        return 1
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())