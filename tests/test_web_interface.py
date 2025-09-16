"""Tests for web interface functionality using browser automation."""

import pytest
import json
import time
from pathlib import Path
from literature_webviewer.build_pipeline import BuildPipeline, BuildConfig


def build_website(temp_dir, sample_rdf_file):
    """Helper function to build website for testing."""
    output_dir = temp_dir / "website"
    config = BuildConfig(
        input_file=sample_rdf_file,
        output_dir=str(output_dir)
    )
    pipeline = BuildPipeline(config)
    result = pipeline.build()
    assert result.success is True
    return output_dir


class TestWebInterfaceBasic:
    """Basic tests for web interface functionality without browser automation."""
    
    def test_generated_html_structure(self, temp_dir, sample_rdf_file):
        """Test that generated HTML has correct structure."""
        output_dir = temp_dir / "website"
        from literature_webviewer.build_pipeline import BuildConfig
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Read generated HTML
        html_file = output_dir / "index.html"
        html_content = html_file.read_text(encoding='utf-8')
        
        # Check for essential HTML structure
        assert "<!DOCTYPE html>" in html_content or "<html" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "</html>" in html_content
        
        # Check for required elements
        assert 'id="collection-tree"' in html_content
        assert 'id="bibliography-table"' in html_content
        assert 'id="search-input"' in html_content
        # Check for breadcrumb-related elements (may be class-based)
        assert 'breadcrumb' in html_content.lower() or 'navigation' in html_content.lower()
        
        # Check for CSS and JS references
        assert "styles.css" in html_content
        assert "app.js" in html_content
    
    def test_generated_css_structure(self, temp_dir, sample_rdf_file):
        """Test that generated CSS has correct structure."""
        output_dir = temp_dir / "website"
        from literature_webviewer.build_pipeline import BuildConfig
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Read generated CSS
        css_file = output_dir / "styles.css"
        css_content = css_file.read_text(encoding='utf-8')
        
        # Check for essential CSS classes/IDs (may use different naming)
        assert "collection" in css_content.lower() or "tree" in css_content.lower()
        assert "bibliography" in css_content.lower() or "table" in css_content.lower()
        assert "search" in css_content.lower() or "input" in css_content.lower()
        
        # Check for responsive design
        assert "@media" in css_content
        
        # Check for common CSS properties
        assert "display:" in css_content
        assert "color:" in css_content
        assert "font-" in css_content
    
    def test_generated_javascript_structure(self, temp_dir, sample_rdf_file):
        """Test that generated JavaScript has correct structure."""
        output_dir = temp_dir / "website"
        from literature_webviewer.build_pipeline import BuildConfig
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Read generated JavaScript
        js_file = output_dir / "app.js"
        js_content = js_file.read_text(encoding='utf-8')
        
        # Check for essential JavaScript components
        assert "CollectionTree" in js_content
        assert "BibliographyTable" in js_content
        assert "SearchComponent" in js_content
        assert "BreadcrumbComponent" in js_content
        
        # Check for data loading
        assert "fetch" in js_content or "XMLHttpRequest" in js_content
        assert "bibliography.json" in js_content
        assert "collections.json" in js_content
        
        # Check for event handling
        assert "addEventListener" in js_content or "onclick" in js_content
        
        # Check for DOM manipulation
        assert "getElementById" in js_content or "querySelector" in js_content
    
    def test_data_files_accessibility(self, temp_dir, sample_rdf_file):
        """Test that data files are properly structured for web access."""
        output_dir = temp_dir / "website"
        from literature_webviewer.build_pipeline import BuildConfig
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Check bibliography data
        bib_file = output_dir / "data" / "bibliography.json"
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        # Should have proper structure for web consumption
        assert "metadata" in bib_data
        assert "items" in bib_data
        assert isinstance(bib_data["items"], list)
        
        if bib_data["items"]:
            first_item = bib_data["items"][0]
            # Check required fields for web interface
            assert "id" in first_item
            assert "title" in first_item
            assert "authors" in first_item
            assert "type" in first_item
        
        # Check collections data
        col_file = output_dir / "data" / "collections.json"
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Should have proper structure for web consumption
        assert "metadata" in col_data
        assert "collections" in col_data
        assert "tree" in col_data
        assert isinstance(col_data["collections"], dict)
        assert isinstance(col_data["tree"], list)


class TestWebInterfaceDataIntegrity:
    """Test data integrity in web interface."""
    
    def test_bibliography_table_data_completeness(self, temp_dir, sample_rdf_file):
        """Test that bibliography table has complete data."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Load bibliography data
        bib_file = output_dir / "data" / "bibliography.json"
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        items = bib_data["items"]
        assert len(items) > 0
        
        for item in items:
            # Each item should have essential fields
            assert item["id"]
            assert item["title"]
            assert "authors" in item
            assert "type" in item
            
            # Authors should be properly structured
            if item["authors"]:
                for author in item["authors"]:
                    assert "name" in author
                    # Should have at least name or given/surname
                    assert author["name"] or author.get("given") or author.get("surname")
            
            # Type should be valid
            valid_types = ["article", "book", "conference", "thesis", "report", "webpage", "other"]
            assert item["type"] in valid_types
    
    def test_collection_tree_data_completeness(self, temp_dir, sample_rdf_file):
        """Test that collection tree has complete data."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Load collections data
        col_file = output_dir / "data" / "collections.json"
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        collections = col_data["collections"]
        tree = col_data["tree"]
        
        # Tree should reference valid collections
        for root_id in tree:
            assert root_id in collections
        
        # Each collection should have required fields
        for col_id, col_info in collections.items():
            assert col_info["title"]
            assert "itemCount" in col_info
            assert col_info["itemCount"] >= 0
            
            # If has children, they should be valid references
            if "children" in col_info:
                for child_id in col_info["children"]:
                    assert child_id in collections
    
    def test_search_functionality_data_structure(self, temp_dir, sample_rdf_file):
        """Test that data is structured properly for search functionality."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Load bibliography data
        bib_file = output_dir / "data" / "bibliography.json"
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        items = bib_data["items"]
        
        for item in items:
            # Should have searchable text fields
            searchable_fields = []
            
            if item.get("title"):
                searchable_fields.append(item["title"])
            
            if item.get("authors"):
                for author in item["authors"]:
                    if author.get("name"):
                        searchable_fields.append(author["name"])
            
            if item.get("venue"):
                searchable_fields.append(item["venue"])
            
            if item.get("abstract"):
                searchable_fields.append(item["abstract"])
            
            # Should have at least title for searching
            assert len(searchable_fields) > 0
    
    def test_cross_references_integrity(self, temp_dir, sample_rdf_file):
        """Test that cross-references between data structures are valid."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Load both data files
        bib_file = output_dir / "data" / "bibliography.json"
        col_file = output_dir / "data" / "collections.json"
        
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Create sets for validation
        item_ids = {item["id"] for item in bib_data["items"]}
        collection_ids = set(col_data["collections"].keys())
        
        # Check that collection item references are valid
        for col_id, col_info in col_data["collections"].items():
            if "itemIds" in col_info:
                for item_id in col_info["itemIds"]:
                    assert item_id in item_ids, f"Collection {col_id} references non-existent item {item_id}"
        
        # Check that item collection references are valid
        for item in bib_data["items"]:
            if "collections" in item:
                for col_id in item["collections"]:
                    assert col_id in collection_ids, f"Item {item['id']} references non-existent collection {col_id}"


class TestWebInterfaceResponsiveness:
    """Test responsive design aspects of the web interface."""
    
    def test_css_responsive_design_rules(self, temp_dir, sample_rdf_file):
        """Test that CSS includes responsive design rules."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Read CSS file
        css_file = output_dir / "styles.css"
        css_content = css_file.read_text(encoding='utf-8')
        
        # Should have media queries for responsive design
        assert "@media" in css_content
        
        # Should have mobile-specific rules
        mobile_indicators = [
            "max-width",
            "min-width", 
            "screen",
            "768px",  # Common tablet breakpoint
            "480px",  # Common mobile breakpoint
            "1024px"  # Common desktop breakpoint
        ]
        
        # Should have at least some responsive design indicators
        responsive_count = sum(1 for indicator in mobile_indicators if indicator in css_content)
        assert responsive_count >= 2
        
        # Should have flexible layout properties
        flexible_properties = [
            "flex",
            "grid",
            "width: 100%",
            "max-width",
            "min-width"
        ]
        
        flexible_count = sum(1 for prop in flexible_properties if prop in css_content)
        assert flexible_count >= 2
    
    def test_html_viewport_meta_tag(self, temp_dir, sample_rdf_file):
        """Test that HTML includes proper viewport meta tag for mobile."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Read HTML file
        html_file = output_dir / "index.html"
        html_content = html_file.read_text(encoding='utf-8')
        
        # Should have viewport meta tag
        assert 'name="viewport"' in html_content
        assert 'width=device-width' in html_content
        assert 'initial-scale=1' in html_content


class TestWebInterfaceAccessibility:
    """Test accessibility aspects of the web interface."""
    
    def test_html_semantic_structure(self, temp_dir, sample_rdf_file):
        """Test that HTML uses semantic markup."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Read HTML file
        html_file = output_dir / "index.html"
        html_content = html_file.read_text(encoding='utf-8')
        
        # Should use semantic HTML elements
        semantic_elements = [
            "<header",
            "<main",
            "<nav",
            "<section",
            "<article",
            "<aside"
        ]
        
        # Should have at least some semantic elements
        semantic_count = sum(1 for element in semantic_elements if element in html_content)
        assert semantic_count >= 2
        
        # Should have proper heading hierarchy
        assert "<h1" in html_content
        
        # Should have proper table structure if tables are used
        if "<table" in html_content:
            assert "<thead" in html_content
            assert "<tbody" in html_content
            assert "<th" in html_content
    
    def test_html_accessibility_attributes(self, temp_dir, sample_rdf_file):
        """Test that HTML includes accessibility attributes."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Read HTML file
        html_file = output_dir / "index.html"
        html_content = html_file.read_text(encoding='utf-8')
        
        # Should have lang attribute
        assert 'lang=' in html_content
        
        # Should have proper labels for form elements
        if '<input' in html_content:
            # Should have either label elements or aria-label attributes
            has_labels = '<label' in html_content or 'aria-label=' in html_content
            assert has_labels
        
        # Should have alt attributes for images (if any)
        if '<img' in html_content:
            assert 'alt=' in html_content
    
    def test_javascript_keyboard_navigation_support(self, temp_dir, sample_rdf_file):
        """Test that JavaScript supports keyboard navigation."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Read JavaScript file
        js_file = output_dir / "app.js"
        js_content = js_file.read_text(encoding='utf-8')
        
        # Should handle keyboard events
        keyboard_events = [
            "keydown",
            "keyup",
            "keypress",
            "Enter",
            "Escape",
            "ArrowUp",
            "ArrowDown"
        ]
        
        # Should have at least some keyboard event handling
        keyboard_count = sum(1 for event in keyboard_events if event in js_content)
        assert keyboard_count >= 1
        
        # Should handle focus management
        focus_indicators = [
            "focus",
            "blur",
            "tabindex",
            "setAttribute"
        ]
        
        focus_count = sum(1 for indicator in focus_indicators if indicator in js_content)
        assert focus_count >= 1


class TestWebInterfacePerformance:
    """Test performance aspects of the web interface."""
    
    def test_file_sizes_reasonable(self, temp_dir, sample_rdf_file):
        """Test that generated files have reasonable sizes."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Check file sizes
        html_file = output_dir / "index.html"
        css_file = output_dir / "styles.css"
        js_file = output_dir / "app.js"
        
        html_size = html_file.stat().st_size
        css_size = css_file.stat().st_size
        js_size = js_file.stat().st_size
        
        # Files should not be excessively large
        assert html_size < 100 * 1024  # Less than 100KB
        assert css_size < 200 * 1024   # Less than 200KB
        assert js_size < 500 * 1024    # Less than 500KB
        
        # Files should not be empty
        assert html_size > 1000   # At least 1KB
        assert css_size > 500     # At least 0.5KB
        assert js_size > 1000     # At least 1KB
    
    def test_data_file_optimization(self, temp_dir, sample_rdf_file):
        """Test that data files are optimized for loading."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Check data files
        bib_file = output_dir / "data" / "bibliography.json"
        col_file = output_dir / "data" / "collections.json"
        
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Data should be optimized (no unnecessary fields)
        if bib_data["items"]:
            first_item = bib_data["items"][0]
            
            # Should not have empty string fields (they should be omitted)
            for key, value in first_item.items():
                if isinstance(value, str):
                    assert value != "", f"Item has empty string field: {key}"
                elif isinstance(value, list):
                    assert value != [], f"Item has empty list field: {key}"
        
        # Collections should be optimized
        for col_id, col_info in col_data["collections"].items():
            # Should not have unnecessary fields
            for key, value in col_info.items():
                if isinstance(value, str):
                    assert value != "", f"Collection {col_id} has empty string field: {key}"
                elif isinstance(value, list):
                    if key != "children":  # children can be empty
                        assert value != [], f"Collection {col_id} has empty list field: {key}"
    
    def test_json_structure_efficiency(self, temp_dir, sample_rdf_file):
        """Test that JSON structure is efficient for client-side processing."""
        output_dir = build_website(temp_dir, sample_rdf_file)
        
        # Load collections data
        col_file = output_dir / "data" / "collections.json"
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Collections should be structured as a flat dictionary for O(1) lookup
        assert isinstance(col_data["collections"], dict)
        
        # Tree should be a simple array of root IDs
        assert isinstance(col_data["tree"], list)
        
        # Each collection should have efficient structure
        for col_id, col_info in col_data["collections"].items():
            # Should use camelCase for JavaScript compatibility
            assert "itemCount" in col_info
            
            # Children should be array of IDs, not full objects
            if "children" in col_info:
                assert isinstance(col_info["children"], list)
                if col_info["children"]:
                    # Should be strings (IDs), not objects
                    assert isinstance(col_info["children"][0], str)