"""Command-line interface for the literature webviewer."""

import sys
import time
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import click

from .rdf_parser import RDFParser, RDFParsingError
from .data_transformer import DataTransformer, DataTransformationError
from .collection_builder import CollectionHierarchyBuilder, CollectionHierarchyError
from .json_generator import JSONGenerator, JSONGenerationError
from .build_pipeline import BuildPipeline, BuildConfig, BuildPipelineError


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def validate_input_file(input_path: str) -> Path:
    """Validate that the input RDF file exists and is readable."""
    path = Path(input_path)
    if not path.exists():
        raise click.ClickException(f"Input file does not exist: {input_path}")
    if not path.is_file():
        raise click.ClickException(f"Input path is not a file: {input_path}")
    if not path.suffix.lower() in ['.rdf', '.xml']:
        click.echo(f"Warning: Input file '{input_path}' does not have .rdf or .xml extension", err=True)
    return path


def validate_output_directory(output_path: str) -> Path:
    """Validate and create output directory if needed."""
    path = Path(output_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except PermissionError:
        raise click.ClickException(f"Permission denied creating output directory: {output_path}")
    except Exception as e:
        raise click.ClickException(f"Failed to create output directory: {str(e)}")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Literature Webviewer - Generate static websites from Zotero RDF exports."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@cli.command()
@click.option('--input', '-i', required=True, help='Input RDF file path')
@click.option('--output', '-o', default='output', help='Output directory path (default: output)')
@click.option('--data-only', is_flag=True, help='Generate only JSON data files, skip HTML/CSS/JS')
@click.option('--combined', is_flag=True, help='Generate single combined JSON file instead of separate files')
@click.option('--validate/--no-validate', default=True, help='Validate generated JSON files (default: enabled)')
@click.option('--incremental/--no-incremental', default=True, help='Enable incremental builds (default: enabled)')
@click.pass_context
def build(ctx, input, output, data_only, combined, validate, incremental):
    """Build a static website from Zotero RDF export."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Validate inputs
        input_path = validate_input_file(input)
        output_path = validate_output_directory(output)
        
        click.echo(f"Building literature webviewer from {input_path}")
        click.echo(f"Output directory: {output_path}")
        
        # Create build configuration
        config = BuildConfig(
            input_file=str(input_path),
            output_dir=str(output_path),
            data_only=data_only,
            combined_json=combined,
            validate_output=validate,
            incremental=incremental,
            verbose=verbose
        )
        
        # Initialize build pipeline
        pipeline = BuildPipeline(config)
        
        # Progress callback for click progress bar
        progress_bar = None
        
        def progress_callback(percentage: int, message: str):
            nonlocal progress_bar
            if progress_bar is None:
                progress_bar = click.progressbar(length=100, label='Building')
                progress_bar.__enter__()
            
            # Update progress bar
            current_progress = progress_bar.pos or 0
            progress_bar.update(percentage - current_progress)
            
            # Show message
            if percentage == 100:
                click.echo(f"\n{message}")
            else:
                click.echo(f"[{percentage}%] {message}")
        
        try:
            # Execute build
            result = pipeline.build(progress_callback)
            
            if progress_bar:
                progress_bar.__exit__(None, None, None)
            
            # Display results
            if result.success:
                click.echo(f"\n✓ Build completed successfully in {result.duration:.2f} seconds")
                click.echo(f"Generated {result.items_count} bibliography items")
                click.echo(f"Generated {result.collections_count} collections")
                
                if result.files_generated:
                    click.echo("\nGenerated files:")
                    for file_path in result.files_generated:
                        file_size = Path(file_path).stat().st_size / 1024
                        click.echo(f"  {Path(file_path).name}: {file_size:.1f} KB")
                
                if result.warnings:
                    click.echo(f"\nWarnings ({len(result.warnings)}):")
                    for warning in result.warnings:
                        click.echo(f"  ⚠ {warning}")
            else:
                click.echo(f"\n✗ Build failed after {result.duration:.2f} seconds")
                for error in result.errors:
                    click.echo(f"  Error: {error}")
                raise click.ClickException("Build failed")
                
        finally:
            pipeline.cleanup()
        
    except BuildPipelineError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Build failed: {str(e)}")


@cli.command()
@click.option('--input', '-i', required=True, help='Input RDF file path')
@click.pass_context
def validate_rdf(ctx, input):
    """Validate an RDF file without building the website."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        input_path = validate_input_file(input)
        
        click.echo(f"Validating RDF file: {input_path}")
        
        parser = RDFParser()
        graph = parser.parse_rdf_file(str(input_path))
        
        # Extract and count items
        items_data = parser.extract_bibliography_items(graph)
        collections_data = parser.extract_collections(graph)
        
        click.echo(f"✓ RDF file is valid")
        click.echo(f"  Found {len(items_data)} bibliography items")
        click.echo(f"  Found {len(collections_data)} collections")
        click.echo(f"  Total RDF triples: {len(graph)}")
        
        # Show item type breakdown
        type_counts = {}
        for item in items_data:
            item_type = item.get('type', 'unknown')
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        
        if type_counts:
            click.echo("\nItem types:")
            for item_type, count in sorted(type_counts.items()):
                click.echo(f"  {item_type}: {count}")
        
    except RDFParsingError as e:
        raise click.ClickException(f"RDF validation failed: {str(e)}")
    except Exception as e:
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Validation failed: {str(e)}")


@cli.command()
@click.option('--input', '-i', required=True, help='Input RDF file path')
@click.option('--output', '-o', default='output', help='Output directory path (default: output)')
@click.option('--data-only', is_flag=True, help='Generate only JSON data files, skip HTML/CSS/JS')
@click.option('--combined', is_flag=True, help='Generate single combined JSON file instead of separate files')
@click.option('--validate/--no-validate', default=True, help='Validate generated JSON files (default: enabled)')
@click.pass_context
def watch(ctx, input, output, data_only, combined, validate):
    """Watch RDF file for changes and rebuild automatically."""
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Validate inputs
        input_path = validate_input_file(input)
        output_path = validate_output_directory(output)
        
        click.echo(f"Starting watch mode for {input_path}")
        click.echo(f"Output directory: {output_path}")
        click.echo("Press Ctrl+C to stop watching")
        
        # Create build configuration
        config = BuildConfig(
            input_file=str(input_path),
            output_dir=str(output_path),
            data_only=data_only,
            combined_json=combined,
            validate_output=validate,
            incremental=True,  # Always use incremental builds in watch mode
            watch_mode=True,
            verbose=verbose
        )
        
        # Initialize build pipeline
        pipeline = BuildPipeline(config)
        
        def progress_callback(percentage: int, message: str):
            timestamp = datetime.now().strftime("%H:%M:%S")
            click.echo(f"[{timestamp}] {message}")
        
        try:
            # Start watch mode
            pipeline.start_watch_mode(progress_callback)
            
            # Keep the process running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                click.echo("\nStopping watch mode...")
                
        finally:
            pipeline.cleanup()
            
    except BuildPipelineError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Watch mode failed: {str(e)}")


@cli.command()
@click.option('--output', '-o', default='output', help='Output directory to check')
def info(output):
    """Show information about generated files."""
    output_path = Path(output)
    
    if not output_path.exists():
        click.echo(f"Output directory does not exist: {output_path}")
        return
    
    data_dir = output_path / "data"
    if not data_dir.exists():
        click.echo(f"No data directory found in: {output_path}")
        return
    
    json_generator = JSONGenerator(str(data_dir))
    json_files = json_generator.get_output_files()
    
    if not json_files:
        click.echo("No JSON files found in output directory")
        return
    
    click.echo(f"Literature webviewer files in {output_path}:")
    
    # Show JSON files with sizes and validation
    file_sizes = json_generator.get_file_sizes()
    validation_results = json_generator.validate_json_files()
    
    for file_path in json_files:
        file_name = Path(file_path).name
        size = file_sizes.get(file_path, 0)
        size_kb = size / 1024
        is_valid = validation_results.get(file_path, False)
        status = "✓" if is_valid else "✗"
        
        click.echo(f"  {status} {file_name}: {size_kb:.1f} KB")
    
    # Show static files if they exist
    static_files = ['index.html', 'styles.css', 'app.js']
    for static_file in static_files:
        static_path = output_path / static_file
        if static_path.exists():
            size_kb = static_path.stat().st_size / 1024
            click.echo(f"  ✓ {static_file}: {size_kb:.1f} KB")


@cli.command()
@click.option('--output', '-o', default='output', help='Output directory to clean')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def clean(output, confirm):
    """Clean generated files from output directory."""
    output_path = Path(output)
    
    if not output_path.exists():
        click.echo(f"Output directory does not exist: {output_path}")
        return
    
    # Find files to clean
    files_to_clean = []
    
    # JSON data files
    data_dir = output_path / "data"
    if data_dir.exists():
        files_to_clean.extend(data_dir.glob("*.json"))
    
    # Static files
    static_files = ['index.html', 'styles.css', 'app.js']
    for static_file in static_files:
        static_path = output_path / static_file
        if static_path.exists():
            files_to_clean.append(static_path)
    
    if not files_to_clean:
        click.echo("No generated files found to clean")
        return
    
    # Show files to be cleaned
    click.echo(f"Files to be cleaned from {output_path}:")
    for file_path in files_to_clean:
        click.echo(f"  {file_path.relative_to(output_path)}")
    
    # Confirm deletion
    if not confirm:
        if not click.confirm(f"\nDelete {len(files_to_clean)} files?"):
            click.echo("Clean operation cancelled")
            return
    
    # Delete files
    deleted_count = 0
    for file_path in files_to_clean:
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            click.echo(f"Failed to delete {file_path}: {str(e)}", err=True)
    
    # Clean up empty directories
    if data_dir.exists() and not any(data_dir.iterdir()):
        try:
            data_dir.rmdir()
        except Exception:
            pass  # Ignore errors when removing empty directory
    
    click.echo(f"Cleaned {deleted_count} files")


# Maintain backward compatibility with the old main function
@click.command()
@click.option('--input', '-i', help='Input RDF file path')
@click.option('--output', '-o', help='Output directory path', default='output')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(input, output, verbose):
    """Generate a static website from Zotero RDF export (legacy interface)."""
    setup_logging(verbose)
    
    if not input:
        click.echo("Literature Webviewer CLI")
        click.echo("Use 'literature-webviewer build --help' for usage information")
        click.echo("Or use the legacy format: literature-webviewer --input <file> --output <dir>")
        return
    
    # Call the build command with the provided arguments
    ctx = click.Context(build)
    ctx.obj = {'verbose': verbose}
    ctx.invoke(build, input=input, output=output, data_only=False, combined=False, validate=False)


if __name__ == '__main__':
    # Check if we're being called with legacy arguments
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-') and sys.argv[1] not in ['build', 'watch', 'info', 'clean', 'validate-rdf']:
        # This looks like a legacy call, redirect to main function
        main()
    else:
        cli()