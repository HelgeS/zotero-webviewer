"""Build pipeline orchestration and file watching functionality."""

import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes when watchdog is not available
    class FileSystemEventHandler:
        def on_modified(self, event):
            pass
    
    class Observer:
        def schedule(self, handler, path, recursive=False):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def join(self):
            pass

from .rdf_parser import RDFParser, RDFParsingError
from .data_transformer import DataTransformer, DataTransformationError
from .collection_builder import CollectionHierarchyBuilder, CollectionHierarchyError
from .json_generator import JSONGenerator, JSONGenerationError
from .site_generator import SiteGenerator, SiteGenerationError, SiteConfig


@dataclass
class BuildConfig:
    """Configuration for the build pipeline."""
    input_file: str
    output_dir: str
    data_only: bool = False
    combined_json: bool = False
    validate_output: bool = True
    incremental: bool = True
    watch_mode: bool = False
    production: bool = False
    verbose: bool = False


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    duration: float
    items_count: int
    collections_count: int
    files_generated: List[str]
    errors: List[str]
    warnings: List[str]
    timestamp: datetime


class BuildValidationError(Exception):
    """Exception raised when build validation fails."""
    pass


class BuildPipelineError(Exception):
    """Exception raised when build pipeline fails."""
    pass


class RDFFileWatcher(FileSystemEventHandler):
    """File system event handler for watching RDF file changes."""
    
    def __init__(self, rdf_file_path: str, callback: Callable[[], None]):
        self.rdf_file_path = Path(rdf_file_path).resolve()
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        self._last_modified = 0
        self._debounce_delay = 1.0  # 1 second debounce
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        event_path = Path(event.src_path).resolve()
        
        # Check if this is our target RDF file
        if event_path == self.rdf_file_path:
            current_time = time.time()
            
            # Debounce rapid file changes
            if current_time - self._last_modified > self._debounce_delay:
                self._last_modified = current_time
                self.logger.info(f"RDF file changed: {event_path}")
                
                # Small delay to ensure file write is complete
                time.sleep(0.5)
                
                try:
                    self.callback()
                except Exception as e:
                    self.logger.error(f"Error during rebuild: {str(e)}")


class BuildPipeline:
    """Orchestrates the complete RDF-to-website build pipeline."""
    
    def __init__(self, config: BuildConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Initialize components
        self.parser = RDFParser()
        self.transformer = DataTransformer()
        self.hierarchy_builder = CollectionHierarchyBuilder()
        self.json_generator = JSONGenerator(str(Path(config.output_dir) / "data"))
        self.site_generator = SiteGenerator(config.output_dir)
        
        # Build state tracking
        self._last_build_hash: Optional[str] = None
        self._build_history: List[BuildResult] = []
        
        # File watcher
        self._observer: Optional[Observer] = None
        self._file_watcher: Optional[RDFFileWatcher] = None
    
    def _setup_logging(self):
        """Configure logging based on verbosity setting."""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def build(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> BuildResult:
        """
        Execute the complete build pipeline.
        
        Args:
            progress_callback: Optional callback for progress updates (percentage, message)
            
        Returns:
            BuildResult with build information and status
            
        Raises:
            BuildPipelineError: If the build fails
        """
        start_time = time.time()
        errors = []
        warnings = []
        files_generated = []
        
        def update_progress(percentage: int, message: str):
            if progress_callback:
                progress_callback(percentage, message)
            self.logger.info(f"[{percentage}%] {message}")
        
        try:
            self.logger.info(f"Starting build pipeline for {self.config.input_file}")
            
            # Validate inputs
            self._validate_inputs()
            update_progress(5, "Validating inputs")
            
            # Check if incremental build is possible
            if self.config.incremental and self._should_skip_build():
                self.logger.info("No changes detected, skipping build")
                # Return the last successful build result
                if self._build_history:
                    return self._build_history[-1]
            
            # Step 1: Parse RDF file
            update_progress(10, "Parsing RDF file")
            try:
                graph = self.parser.parse_rdf_file(self.config.input_file)
            except RDFParsingError as e:
                errors.append(f"RDF parsing failed: {str(e)}")
                raise BuildPipelineError(f"RDF parsing failed: {str(e)}")
            
            # Step 2: Extract data
            update_progress(25, "Extracting bibliography items and collections")
            try:
                items_data = self.parser.extract_bibliography_items(graph)
                collections_data = self.parser.extract_collections(graph)
                
                # Validate extracted data integrity
                data_integrity_issues = self.parser.validate_bibliography_data_integrity(items_data)
                if data_integrity_issues:
                    for issue in data_integrity_issues:
                        if "missing required field" in issue.lower() or "duplicate" in issue.lower():
                            errors.append(f"Data integrity error: {issue}")
                        else:
                            warnings.append(f"Data integrity warning: {issue}")
                
                # Assign collection references to items
                self.parser.assign_items_to_collections(items_data, collections_data)
                
                if not items_data:
                    warnings.append("No bibliography items found in RDF file")
                if not collections_data:
                    warnings.append("No collections found in RDF file")
                    
            except RDFParsingError as e:
                errors.append(f"Data extraction failed: {str(e)}")
                raise BuildPipelineError(f"Data extraction failed: {str(e)}")
            
            # Step 3: Transform data
            update_progress(40, "Transforming and normalizing data")
            try:
                items = []
                transformation_errors = []
                
                for item_data in items_data:
                    try:
                        item = self.transformer.transform_bibliography_item(item_data)
                        items.append(item)
                    except DataTransformationError as e:
                        item_id = item_data.get('id', 'unknown')
                        error_msg = f"Failed to transform item {item_id}: {str(e)}"
                        
                        # Distinguish between critical errors and warnings
                        if "missing required" in str(e).lower() or "validation" in str(e).lower():
                            transformation_errors.append(error_msg)
                        else:
                            warnings.append(error_msg)
                
                collections = []
                for col_data in collections_data:
                    try:
                        collection = self.transformer.transform_collection(col_data)
                        collections.append(collection)
                    except DataTransformationError as e:
                        warnings.append(f"Failed to transform collection {col_data.get('id', 'unknown')}: {str(e)}")
                
                # If we have critical transformation errors, fail the build
                if transformation_errors:
                    for error in transformation_errors:
                        errors.append(error)
                    raise BuildPipelineError(f"Critical data transformation errors: {len(transformation_errors)} items failed")
                
                # Validate transformed data consistency
                validation_issues = self.transformer.validate_transformed_data(items, collections)
                if validation_issues:
                    for issue in validation_issues:
                        if "duplicate" in issue.lower() and "id" in issue.lower():
                            errors.append(f"Data consistency error: {issue}")
                        else:
                            warnings.append(f"Data consistency warning: {issue}")
                
                if not items:
                    raise BuildPipelineError("No valid bibliography items after transformation")
                        
            except (DataTransformationError, BuildPipelineError):
                raise
            except Exception as e:
                errors.append(f"Data transformation failed: {str(e)}")
                raise BuildPipelineError(f"Data transformation failed: {str(e)}")
            
            # Step 4: Build collection hierarchy
            update_progress(55, "Building collection hierarchy")
            try:
                root_collections = self.hierarchy_builder.build_hierarchy(collections)
                self.hierarchy_builder.assign_items_to_collections(items, root_collections)
                
                # Validate hierarchy
                hierarchy_errors = self.hierarchy_builder.validate_hierarchy()
                if hierarchy_errors:
                    warnings.extend([f"Hierarchy validation: {error}" for error in hierarchy_errors])
                    
            except CollectionHierarchyError as e:
                errors.append(f"Collection hierarchy building failed: {str(e)}")
                raise BuildPipelineError(f"Collection hierarchy building failed: {str(e)}")
            
            # Step 5: Generate JSON files
            update_progress(70, "Generating JSON data files")
            try:
                if self.config.combined_json:
                    json_file = self.json_generator.generate_combined_data(items, root_collections)
                    files_generated.append(json_file)
                else:
                    bib_file = self.json_generator.generate_bibliography_json(items)
                    col_file = self.json_generator.generate_collections_json(root_collections)
                    search_file = self.json_generator.generate_search_index(items)
                    files_generated.extend([bib_file, col_file, search_file])
                    
            except JSONGenerationError as e:
                errors.append(f"JSON generation failed: {str(e)}")
                raise BuildPipelineError(f"JSON generation failed: {str(e)}")
            
            # Step 6: Generate static site files (if not data-only)
            if not self.config.data_only:
                update_progress(85, "Generating static website files")
                try:
                    # Create site configuration
                    site_config = SiteConfig(
                        title="Literature Collection Webviewer",
                        collection_title="Literature Collection",
                        description="Interactive browser for academic literature collections exported from Zotero"
                    )
                    
                    # Generate static site
                    site_files = self.site_generator.generate_site(site_config)
                    files_generated.extend(site_files)
                    
                    self.logger.info(f"Generated {len(site_files)} static site files")
                    
                except SiteGenerationError as e:
                    errors.append(f"Static site generation failed: {str(e)}")
                    raise BuildPipelineError(f"Static site generation failed: {str(e)}")
                except Exception as e:
                    warnings.append(f"Static site generation failed: {str(e)}")
            
            # Step 7: Validate output
            if self.config.validate_output:
                update_progress(95, "Validating generated files")
                try:
                    self._validate_output(files_generated)
                except BuildValidationError as e:
                    errors.append(f"Output validation failed: {str(e)}")
                    # Don't fail the build for validation errors, just warn
                    warnings.append(str(e))
            
            # Step 8: Production optimization (if enabled)
            if self.config.production:
                update_progress(95, "Optimizing for production")
                try:
                    from .production_optimizer import ProductionOptimizer, DeploymentHelper
                    
                    optimizer = ProductionOptimizer(self.config.output_dir)
                    optimization_report = optimizer.optimize_all()
                    
                    # Create deployment configuration
                    deployment_helper = DeploymentHelper(self.config.output_dir)
                    deployment_helper.create_github_pages_config()
                    deployment_info = deployment_helper.create_deployment_info()
                    
                    # Validate deployment
                    deployment_errors = deployment_helper.validate_deployment()
                    if deployment_errors:
                        warnings.extend([f"Deployment validation: {error}" for error in deployment_errors])
                    
                    # Add optimization info to warnings for reporting
                    total_savings = optimization_report.get('total_savings', 0)
                    total_ratio = optimization_report.get('total_compression_ratio', 0)
                    warnings.append(f"Production optimization: {total_savings} bytes saved ({total_ratio:.1f}% reduction)")
                    
                except Exception as e:
                    warnings.append(f"Production optimization failed: {str(e)}")
            
            update_progress(100, "Build completed successfully")
            
            # Update build state
            self._update_build_hash()
            
            # Create build result
            duration = time.time() - start_time
            result = BuildResult(
                success=True,
                duration=duration,
                items_count=len(items),
                collections_count=len(collections),
                files_generated=files_generated,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now()
            )
            
            self._build_history.append(result)
            self.logger.info(f"Build completed successfully in {duration:.2f} seconds")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            errors.append(str(e))
            
            result = BuildResult(
                success=False,
                duration=duration,
                items_count=0,
                collections_count=0,
                files_generated=files_generated,
                errors=errors,
                warnings=warnings,
                timestamp=datetime.now()
            )
            
            self._build_history.append(result)
            self.logger.error(f"Build failed after {duration:.2f} seconds: {str(e)}")
            
            raise BuildPipelineError(f"Build failed: {str(e)}")
    
    def start_watch_mode(self, progress_callback: Optional[Callable[[int, str], None]] = None) -> None:
        """
        Start file watching mode for automatic rebuilds.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Raises:
            BuildPipelineError: If watch mode cannot be started
        """
        if not WATCHDOG_AVAILABLE:
            raise BuildPipelineError(
                "File watching requires the 'watchdog' package. "
                "Install it with: pip install watchdog"
            )
        
        if self._observer is not None:
            self.logger.warning("Watch mode is already active")
            return
        
        try:
            input_path = Path(self.config.input_file)
            watch_dir = input_path.parent
            
            self.logger.info(f"Starting watch mode for {input_path}")
            self.logger.info(f"Watching directory: {watch_dir}")
            
            # Create file watcher
            def rebuild_callback():
                try:
                    self.build(progress_callback)
                except BuildPipelineError as e:
                    self.logger.error(f"Rebuild failed: {str(e)}")
            
            self._file_watcher = RDFFileWatcher(str(input_path), rebuild_callback)
            
            # Set up observer
            self._observer = Observer()
            self._observer.schedule(self._file_watcher, str(watch_dir), recursive=False)
            self._observer.start()
            
            self.logger.info("Watch mode started. Press Ctrl+C to stop.")
            
            # Perform initial build
            self.build(progress_callback)
            
        except Exception as e:
            self.stop_watch_mode()
            raise BuildPipelineError(f"Failed to start watch mode: {str(e)}")
    
    def stop_watch_mode(self) -> None:
        """Stop file watching mode."""
        if self._observer is not None:
            self.logger.info("Stopping watch mode")
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._file_watcher = None
    
    def _validate_inputs(self) -> None:
        """Validate input configuration and files."""
        input_path = Path(self.config.input_file)
        
        if not input_path.exists():
            raise BuildPipelineError(f"Input file does not exist: {self.config.input_file}")
        
        if not input_path.is_file():
            raise BuildPipelineError(f"Input path is not a file: {self.config.input_file}")
        
        # Create output directory if it doesn't exist
        output_path = Path(self.config.output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise BuildPipelineError(f"Failed to create output directory: {str(e)}")
    
    def _should_skip_build(self) -> bool:
        """Check if build can be skipped based on file changes."""
        if not self.config.incremental:
            return False
        
        current_hash = self._calculate_input_hash()
        
        if self._last_build_hash is None:
            return False
        
        return current_hash == self._last_build_hash
    
    def _calculate_input_hash(self) -> str:
        """Calculate hash of input file for change detection."""
        try:
            with open(self.config.input_file, 'rb') as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate input hash: {str(e)}")
            return ""
    
    def _update_build_hash(self) -> None:
        """Update the stored hash of the input file."""
        self._last_build_hash = self._calculate_input_hash()
    
    def _validate_output(self, files_generated: List[str]) -> None:
        """
        Validate generated output files.
        
        Args:
            files_generated: List of file paths that were generated
            
        Raises:
            BuildValidationError: If validation fails
        """
        validation_errors = []
        
        # Validate JSON files
        validation_results = self.json_generator.validate_json_files()
        for file_path, is_valid in validation_results.items():
            if not is_valid:
                validation_errors.append(f"Invalid JSON file: {file_path}")
        
        # Check that all expected files were generated
        for file_path in files_generated:
            if not Path(file_path).exists():
                validation_errors.append(f"Expected file not found: {file_path}")
        
        # Validate file sizes (warn about empty files)
        file_sizes = self.json_generator.get_file_sizes()
        for file_path, size in file_sizes.items():
            if size == 0:
                validation_errors.append(f"Empty file generated: {file_path}")
        
        if validation_errors:
            raise BuildValidationError("; ".join(validation_errors))
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about build history and performance.
        
        Returns:
            Dictionary with build statistics
        """
        if not self._build_history:
            return {"total_builds": 0}
        
        successful_builds = [b for b in self._build_history if b.success]
        failed_builds = [b for b in self._build_history if not b.success]
        
        stats = {
            "total_builds": len(self._build_history),
            "successful_builds": len(successful_builds),
            "failed_builds": len(failed_builds),
            "success_rate": len(successful_builds) / len(self._build_history) * 100,
        }
        
        if successful_builds:
            durations = [b.duration for b in successful_builds]
            stats.update({
                "average_build_time": sum(durations) / len(durations),
                "fastest_build": min(durations),
                "slowest_build": max(durations),
                "last_successful_build": successful_builds[-1].timestamp.isoformat(),
            })
        
        if failed_builds:
            stats["last_failed_build"] = failed_builds[-1].timestamp.isoformat()
        
        return stats
    
    def cleanup(self) -> None:
        """Clean up resources and stop any running processes."""
        self.stop_watch_mode()