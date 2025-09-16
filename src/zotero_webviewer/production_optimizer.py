"""Production optimization utilities for minification and compression."""

import re
import json
import gzip
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List


logger = logging.getLogger(__name__)


class ProductionOptimizer:
    """Handles production optimizations like minification and compression."""
    
    def __init__(self, output_dir: str):
        """Initialize the production optimizer.
        
        Args:
            output_dir: Directory containing the generated files
        """
        self.output_dir = Path(output_dir)
        self.stats = {
            'original_sizes': {},
            'optimized_sizes': {},
            'compression_ratios': {}
        }
    
    def optimize_all(self) -> Dict[str, any]:
        """Optimize all generated files for production.
        
        Returns:
            Dictionary with optimization statistics
        """
        logger.info("Starting production optimization...")
        
        # Optimize CSS
        css_files = list(self.output_dir.glob("*.css"))
        for css_file in css_files:
            self.optimize_css(css_file)
        
        # Optimize JavaScript
        js_files = list(self.output_dir.glob("*.js"))
        for js_file in js_files:
            self.optimize_javascript(js_file)
        
        # Optimize JSON data files
        json_files = list(self.output_dir.glob("data/*.json"))
        for json_file in json_files:
            self.optimize_json(json_file)
        
        # Optimize HTML
        html_files = list(self.output_dir.glob("*.html"))
        for html_file in html_files:
            self.optimize_html(html_file)
        
        # Generate compressed versions
        self.generate_compressed_files()
        
        # Generate optimization report
        return self.generate_report()
    
    def optimize_css(self, css_file: Path) -> None:
        """Minify CSS file.
        
        Args:
            css_file: Path to CSS file to optimize
        """
        logger.debug(f"Optimizing CSS: {css_file}")
        
        original_size = css_file.stat().st_size
        self.stats['original_sizes'][str(css_file)] = original_size
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minify CSS
        minified = self._minify_css(content)
        
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        optimized_size = css_file.stat().st_size
        self.stats['optimized_sizes'][str(css_file)] = optimized_size
        self.stats['compression_ratios'][str(css_file)] = (
            (original_size - optimized_size) / original_size * 100
        )
        
        logger.debug(f"CSS optimized: {original_size} -> {optimized_size} bytes "
                    f"({self.stats['compression_ratios'][str(css_file)]:.1f}% reduction)")
    
    def optimize_javascript(self, js_file: Path) -> None:
        """Minify JavaScript file.
        
        Args:
            js_file: Path to JavaScript file to optimize
        """
        logger.debug(f"Optimizing JavaScript: {js_file}")
        
        original_size = js_file.stat().st_size
        self.stats['original_sizes'][str(js_file)] = original_size
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minify JavaScript
        minified = self._minify_javascript(content)
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        optimized_size = js_file.stat().st_size
        self.stats['optimized_sizes'][str(js_file)] = optimized_size
        self.stats['compression_ratios'][str(js_file)] = (
            (original_size - optimized_size) / original_size * 100
        )
        
        logger.debug(f"JavaScript optimized: {original_size} -> {optimized_size} bytes "
                    f"({self.stats['compression_ratios'][str(js_file)]:.1f}% reduction)")
    
    def optimize_json(self, json_file: Path) -> None:
        """Optimize JSON file by removing whitespace.
        
        Args:
            json_file: Path to JSON file to optimize
        """
        logger.debug(f"Optimizing JSON: {json_file}")
        
        original_size = json_file.stat().st_size
        self.stats['original_sizes'][str(json_file)] = original_size
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Write compact JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        
        optimized_size = json_file.stat().st_size
        self.stats['optimized_sizes'][str(json_file)] = optimized_size
        self.stats['compression_ratios'][str(json_file)] = (
            (original_size - optimized_size) / original_size * 100
        )
        
        logger.debug(f"JSON optimized: {original_size} -> {optimized_size} bytes "
                    f"({self.stats['compression_ratios'][str(json_file)]:.1f}% reduction)")
    
    def optimize_html(self, html_file: Path) -> None:
        """Minify HTML file.
        
        Args:
            html_file: Path to HTML file to optimize
        """
        logger.debug(f"Optimizing HTML: {html_file}")
        
        original_size = html_file.stat().st_size
        self.stats['original_sizes'][str(html_file)] = original_size
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minify HTML
        minified = self._minify_html(content)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        optimized_size = html_file.stat().st_size
        self.stats['optimized_sizes'][str(html_file)] = optimized_size
        self.stats['compression_ratios'][str(html_file)] = (
            (original_size - optimized_size) / original_size * 100
        )
        
        logger.debug(f"HTML optimized: {original_size} -> {optimized_size} bytes "
                    f"({self.stats['compression_ratios'][str(html_file)]:.1f}% reduction)")
    
    def generate_compressed_files(self) -> None:
        """Generate gzip compressed versions of static files."""
        logger.debug("Generating compressed files...")
        
        # Files to compress
        compress_extensions = ['.html', '.css', '.js', '.json']
        
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in compress_extensions:
                self._create_gzip_file(file_path)
    
    def _create_gzip_file(self, file_path: Path) -> None:
        """Create a gzip compressed version of a file.
        
        Args:
            file_path: Path to file to compress
        """
        gzip_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(gzip_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        original_size = file_path.stat().st_size
        compressed_size = gzip_path.stat().st_size
        compression_ratio = (original_size - compressed_size) / original_size * 100
        
        logger.debug(f"Compressed {file_path.name}: {original_size} -> {compressed_size} bytes "
                    f"({compression_ratio:.1f}% reduction)")
    
    def _minify_css(self, css_content: str) -> str:
        """Minify CSS content.
        
        Args:
            css_content: CSS content to minify
            
        Returns:
            Minified CSS content
        """
        # Remove comments
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        
        # Remove whitespace around specific characters
        css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)
        
        # Remove trailing semicolons before closing braces
        css_content = re.sub(r';\s*}', '}', css_content)
        
        # Remove leading/trailing whitespace
        css_content = css_content.strip()
        
        return css_content
    
    def _minify_javascript(self, js_content: str) -> str:
        """Basic JavaScript minification.
        
        Args:
            js_content: JavaScript content to minify
            
        Returns:
            Minified JavaScript content
        """
        # Remove single-line comments (but preserve URLs)
        js_content = re.sub(r'(?<!:)//.*?(?=\n|$)', '', js_content)
        
        # Remove multi-line comments
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace (but preserve string literals)
        lines = []
        in_string = False
        string_char = None
        
        for line in js_content.split('\n'):
            if not line.strip():
                continue
            
            # Basic whitespace reduction
            line = re.sub(r'\s+', ' ', line.strip())
            
            # Remove whitespace around operators (basic)
            line = re.sub(r'\s*([=+\-*/<>!&|{}();,])\s*', r'\1', line)
            
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _minify_html(self, html_content: str) -> str:
        """Minify HTML content.
        
        Args:
            html_content: HTML content to minify
            
        Returns:
            Minified HTML content
        """
        # Remove HTML comments (but preserve conditional comments)
        html_content = re.sub(r'<!--(?!\[if).*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove unnecessary whitespace between tags
        html_content = re.sub(r'>\s+<', '><', html_content)
        
        # Remove leading/trailing whitespace on lines
        lines = [line.strip() for line in html_content.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def generate_report(self) -> Dict[str, any]:
        """Generate optimization report.
        
        Returns:
            Dictionary with optimization statistics
        """
        total_original = sum(self.stats['original_sizes'].values())
        total_optimized = sum(self.stats['optimized_sizes'].values())
        total_savings = total_original - total_optimized
        total_ratio = (total_savings / total_original * 100) if total_original > 0 else 0
        
        report = {
            'total_original_size': total_original,
            'total_optimized_size': total_optimized,
            'total_savings': total_savings,
            'total_compression_ratio': total_ratio,
            'file_details': {}
        }
        
        for file_path in self.stats['original_sizes']:
            report['file_details'][file_path] = {
                'original_size': self.stats['original_sizes'][file_path],
                'optimized_size': self.stats['optimized_sizes'][file_path],
                'compression_ratio': self.stats['compression_ratios'][file_path]
            }
        
        logger.info(f"Production optimization complete: "
                   f"{total_original} -> {total_optimized} bytes "
                   f"({total_ratio:.1f}% reduction)")
        
        return report


class DeploymentHelper:
    """Helper for deployment-related tasks."""
    
    def __init__(self, output_dir: str):
        """Initialize deployment helper.
        
        Args:
            output_dir: Directory containing the generated files
        """
        self.output_dir = Path(output_dir)
    
    def create_github_pages_config(self) -> None:
        """Create configuration files for GitHub Pages deployment."""
        logger.info("Creating GitHub Pages configuration...")
        
        # Create .nojekyll file to prevent Jekyll processing
        nojekyll_path = self.output_dir / '.nojekyll'
        nojekyll_path.touch()
        
        # Create CNAME file if needed (placeholder)
        # This would be configured based on user input in a real implementation
        
        logger.info("GitHub Pages configuration created")
    
    def create_deployment_info(self) -> Dict[str, any]:
        """Create deployment information file.
        
        Returns:
            Dictionary with deployment information
        """
        deployment_info = {
            'build_timestamp': datetime.now().isoformat(),
            'files': [],
            'total_size': 0
        }
        
        # Collect file information
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                relative_path = file_path.relative_to(self.output_dir)
                file_size = file_path.stat().st_size
                
                deployment_info['files'].append({
                    'path': str(relative_path),
                    'size': file_size,
                    'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                })
                deployment_info['total_size'] += file_size
        
        # Write deployment info
        info_path = self.output_dir / 'deployment-info.json'
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(deployment_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Deployment info created: {len(deployment_info['files'])} files, "
                   f"{deployment_info['total_size'] / 1024:.1f} KB total")
        
        return deployment_info
    
    def validate_deployment(self) -> List[str]:
        """Validate that all required files are present for deployment.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required files
        required_files = ['index.html', 'styles.css', 'app.js']
        for required_file in required_files:
            file_path = self.output_dir / required_file
            if not file_path.exists():
                errors.append(f"Missing required file: {required_file}")
        
        # Check data directory
        data_dir = self.output_dir / 'data'
        if not data_dir.exists():
            errors.append("Missing data directory")
        else:
            # Check for JSON files
            json_files = list(data_dir.glob('*.json'))
            if not json_files:
                errors.append("No JSON data files found in data directory")
        
        # Check file sizes (warn about very large files)
        for file_path in self.output_dir.rglob('*'):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                if file_size > 10 * 1024 * 1024:  # 10MB
                    errors.append(f"Large file detected: {file_path.name} ({file_size / 1024 / 1024:.1f} MB)")
        
        return errors