"""Unit tests for JSON generation functionality."""

import json
from pathlib import Path
from zotero_webviewer.json_generator import (
    JSONGenerator
)
from zotero_webviewer.data_transformer import BibliographyItem, Collection, Author


class TestJSONGenerator:
    """Test cases for JSONGenerator class."""
    
    def test_init_default(self, temp_dir):
        """Test JSONGenerator initialization with default output directory."""
        generator = JSONGenerator(str(temp_dir / "data"))
        
        assert generator.logger is not None
        assert generator.output_dir.name == "data"
        assert generator.output_dir.exists()
    
    def test_init_custom_output_dir(self, temp_dir):
        """Test JSONGenerator initialization with custom output directory."""
        custom_dir = temp_dir / "custom_output"
        generator = JSONGenerator(str(custom_dir))
        
        assert generator.output_dir == custom_dir
        assert generator.output_dir.exists()
    
    def test_generate_bibliography_json(self, temp_dir, sample_bibliography_items):
        """Test generating bibliography JSON file."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_bibliography_json(sample_bibliography_items)
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Check file content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "items" in data
        assert data["metadata"]["total_items"] == len(sample_bibliography_items)
        assert len(data["items"]) == len(sample_bibliography_items)
        
        # Check first item structure
        first_item = data["items"][0]
        assert "id" in first_item
        assert "title" in first_item
        assert "authors" in first_item
        assert "type" in first_item
    
    def test_generate_bibliography_json_custom_filename(self, temp_dir, sample_bibliography_items):
        """Test generating bibliography JSON with custom filename."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_bibliography_json(
            sample_bibliography_items, 
            filename="custom_bibliography.json"
        )
        
        assert Path(output_path).name == "custom_bibliography.json"
        assert Path(output_path).exists()
    
    def test_generate_collections_json(self, temp_dir, sample_collections):
        """Test generating collections JSON file."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_collections_json(sample_collections)
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Check file content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "collections" in data
        assert "tree" in data
        
        # Check metadata
        assert data["metadata"]["total_collections"] >= len(sample_collections)
        # Note: The JSON generator counts all collections, including nested ones
        assert data["metadata"]["root_collections"] >= 1
        
        # Check tree structure (should contain root collection IDs)
        assert isinstance(data["tree"], list)
        
        # Check collections dictionary
        assert isinstance(data["collections"], dict)
        for collection in sample_collections:
            if collection.id in data["collections"]:
                col_data = data["collections"][collection.id]
                assert col_data["title"] == collection.title
                assert col_data["itemCount"] == collection.item_count
    
    def test_generate_search_index(self, temp_dir, sample_bibliography_items):
        """Test generating search index JSON file."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_search_index(sample_bibliography_items)
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Check file content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "index" in data
        assert data["metadata"]["total_items"] == len(sample_bibliography_items)
        
        # Check index structure
        first_index_entry = data["index"][0]
        assert "id" in first_index_entry
        assert "title" in first_index_entry
        assert "authors" in first_index_entry
        assert "searchable" in first_index_entry
        assert "keywords" in first_index_entry
    
    def test_generate_combined_data(self, temp_dir, sample_bibliography_items, sample_collections):
        """Test generating combined data JSON file."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_combined_data(
            sample_bibliography_items, 
            sample_collections
        )
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Check file content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "bibliography" in data
        assert "collections" in data
        
        # Check bibliography section
        assert "items" in data["bibliography"]
        assert len(data["bibliography"]["items"]) == len(sample_bibliography_items)
        
        # Check collections section
        assert "hierarchy" in data["collections"]
        assert "index" in data["collections"]
    
    def test_optimize_bibliography_item(self, temp_dir):
        """Test bibliography item optimization."""
        generator = JSONGenerator(str(temp_dir))
        
        item_dict = {
            "id": "item1",
            "title": "Test Title",
            "authors": [
                {"given_name": "John", "surname": "Smith", "full_name": "John Smith"},
                {"given_name": "", "surname": "", "full_name": ""}  # Empty author
            ],
            "year": 2023,
            "venue": "Test Venue",
            "abstract": "",  # Empty field
            "doi": "",  # Empty field
            "keywords": [],  # Empty list
            "attachments": [
                {"title": "PDF", "url": "https://example.org/paper.pdf"},
                {"title": "", "url": ""}  # Empty attachment
            ]
        }
        
        optimized = generator._optimize_bibliography_item(item_dict)
        
        # Should remove empty fields
        assert "abstract" not in optimized
        assert "doi" not in optimized
        assert "keywords" not in optimized
        
        # Should filter out empty authors and attachments
        assert len(optimized["authors"]) == 1
        assert len(optimized["attachments"]) == 1
        
        # Should simplify author structure
        assert optimized["authors"][0]["name"] == "John Smith"
    
    def test_optimize_collection(self, temp_dir):
        """Test collection optimization."""
        generator = JSONGenerator(str(temp_dir))
        
        collection_dict = {
            "id": "col1",
            "title": "Test Collection",
            "parent_id": None,  # Should be excluded when None
            "item_ids": ["item1", "item2"],
            "item_count": 2,
            "children": [
                {
                    "id": "child1",
                    "title": "Child Collection",
                    "parent_id": "col1",
                    "item_ids": [],  # Should be excluded when empty
                    "item_count": 0,
                    "children": []
                }
            ]
        }
        
        optimized = generator._optimize_collection(collection_dict)
        
        # Should rename fields for client-side use
        assert optimized["itemCount"] == 2
        assert "parentId" not in optimized  # None value excluded
        assert "itemIds" in optimized
        
        # Should recursively optimize children
        assert len(optimized["children"]) == 1
        child = optimized["children"][0]
        assert child["itemCount"] == 0
        assert "itemIds" not in child  # Empty list excluded
    
    def test_optimize_collection_for_js(self, temp_dir):
        """Test collection optimization for JavaScript consumption."""
        generator = JSONGenerator(str(temp_dir))
        
        collection_dict = {
            "id": "parent",
            "title": "Parent Collection",
            "parent_id": "grandparent",
            "item_ids": ["item1"],
            "item_count": 1,
            "children": [
                {"id": "child1", "title": "Child 1"},
                {"id": "child2", "title": "Child 2"}
            ]
        }
        
        optimized = generator._optimize_collection_for_js(collection_dict)
        
        # Should include parent ID when present
        assert optimized["parentId"] == "grandparent"
        
        # Should convert children to array of IDs
        assert optimized["children"] == ["child1", "child2"]
        
        # Should include item IDs
        assert optimized["itemIds"] == ["item1"]
    
    def test_create_searchable_text(self, temp_dir):
        """Test creating searchable text from bibliography item."""
        generator = JSONGenerator(str(temp_dir))
        
        item = BibliographyItem(
            id="item1",
            title="Machine Learning in Healthcare",
            authors=[
                Author(given_name="John", surname="Smith", full_name="John Smith"),
                Author(given_name="Jane", surname="Doe", full_name="Jane Doe")
            ],
            venue="Journal of AI",
            abstract="This paper explores the use of artificial intelligence in medical diagnosis and treatment.",
            keywords=["machine learning", "healthcare", "AI"]
        )
        
        searchable = generator._create_searchable_text(item)
        
        # Should include title, authors, venue, abstract excerpt, and keywords
        assert "machine learning in healthcare" in searchable
        assert "john smith" in searchable
        assert "jane doe" in searchable
        assert "journal of ai" in searchable
        assert "artificial intelligence" in searchable
        assert "machine learning" in searchable
        assert "healthcare" in searchable
    
    def test_create_collection_index(self, temp_dir, sample_collections):
        """Test creating collection index."""
        generator = JSONGenerator(str(temp_dir))
        
        index = generator._create_collection_index(sample_collections)
        
        assert isinstance(index, dict)
        
        # Check that all collections are indexed
        for collection in sample_collections:
            assert collection.id in index
            
            col_info = index[collection.id]
            assert col_info["title"] == collection.title
            assert col_info["itemCount"] == collection.item_count
            assert "path" in col_info
            assert "hasChildren" in col_info
    
    def test_get_output_files(self, temp_dir):
        """Test getting list of output files."""
        generator = JSONGenerator(str(temp_dir))
        
        # Initially no files
        files = generator.get_output_files()
        assert files == []
        
        # Create some JSON files
        (generator.output_dir / "test1.json").write_text('{"test": 1}')
        (generator.output_dir / "test2.json").write_text('{"test": 2}')
        (generator.output_dir / "not_json.txt").write_text("not json")
        
        files = generator.get_output_files()
        
        # Should only include JSON files, sorted
        assert len(files) == 2
        assert all(f.endswith('.json') for f in files)
        assert files == sorted(files)
    
    def test_validate_json_files(self, temp_dir):
        """Test validating generated JSON files."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create valid and invalid JSON files
        (generator.output_dir / "valid.json").write_text('{"valid": true}')
        (generator.output_dir / "invalid.json").write_text('{"invalid": json}')  # Missing quotes
        
        validation_results = generator.validate_json_files()
        
        assert len(validation_results) == 2
        assert validation_results[str(generator.output_dir / "valid.json")] is True
        assert validation_results[str(generator.output_dir / "invalid.json")] is False
    
    def test_get_file_sizes(self, temp_dir):
        """Test getting file sizes for generated JSON files."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create files with different sizes
        small_file = generator.output_dir / "small.json"
        large_file = generator.output_dir / "large.json"
        
        small_file.write_text('{}')
        large_file.write_text('{"data": "' + 'x' * 1000 + '"}')
        
        file_sizes = generator.get_file_sizes()
        
        assert len(file_sizes) == 2
        assert file_sizes[str(small_file)] == 2  # "{}"
        assert file_sizes[str(large_file)] > 1000
    
    def test_flatten_collections_list(self, temp_dir):
        """Test flattening hierarchical collections list."""
        generator = JSONGenerator(str(temp_dir))
        
        parent = Collection(id="parent", title="Parent")
        child1 = Collection(id="child1", title="Child 1")
        child2 = Collection(id="child2", title="Child 2")
        grandchild = Collection(id="grandchild", title="Grandchild")
        
        parent.add_child(child1)
        parent.add_child(child2)
        child1.add_child(grandchild)
        
        flattened = generator._flatten_collections_list([parent])
        
        assert len(flattened) == 4
        ids = [col.id for col in flattened]
        assert "parent" in ids
        assert "child1" in ids
        assert "child2" in ids
        assert "grandchild" in ids


class TestJSONGeneratorErrorHandling:
    """Test error handling in JSON generator."""
    
    def test_generate_bibliography_json_with_real_data(self, temp_dir, sample_rdf_file):
        """Test bibliography JSON generation with real RDF data."""
        from zotero_webviewer.rdf_parser import RDFParser
        from zotero_webviewer.data_transformer import DataTransformer
        
        # Parse real RDF data
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        items_data = parser.extract_bibliography_items()
        
        # Transform the data
        transformer = DataTransformer()
        items = [transformer.transform_bibliography_item(item_data) for item_data in items_data]
        
        # Generate JSON
        generator = JSONGenerator(str(temp_dir))
        output_path = generator.generate_bibliography_json(items)
        
        # Verify the output
        assert Path(output_path).exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "items" in data
        assert len(data["items"]) == len(items)
    
    def test_generate_collections_json_with_real_data(self, temp_dir, sample_rdf_file):
        """Test collections JSON generation with real RDF data."""
        from zotero_webviewer.rdf_parser import RDFParser
        from zotero_webviewer.data_transformer import DataTransformer
        from zotero_webviewer.collection_builder import CollectionHierarchyBuilder
        
        # Parse real RDF data
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        collections_data = parser.extract_collections()
        
        # Transform the data
        transformer = DataTransformer()
        collections = [transformer.transform_collection(col_data) for col_data in collections_data]
        
        # Build hierarchy
        builder = CollectionHierarchyBuilder()
        hierarchy = builder.build_hierarchy(collections)
        
        # Generate JSON
        generator = JSONGenerator(str(temp_dir))
        output_path = generator.generate_collections_json(hierarchy)
        
        # Verify the output
        assert Path(output_path).exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "collections" in data
        assert "tree" in data
    
    def test_generate_search_index_with_real_data(self, temp_dir, sample_rdf_file):
        """Test search index generation with real RDF data."""
        from zotero_webviewer.rdf_parser import RDFParser
        from zotero_webviewer.data_transformer import DataTransformer
        
        # Parse real RDF data
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        items_data = parser.extract_bibliography_items()
        
        # Transform the data
        transformer = DataTransformer()
        items = [transformer.transform_bibliography_item(item_data) for item_data in items_data]
        
        # Generate search index
        generator = JSONGenerator(str(temp_dir))
        output_path = generator.generate_search_index(items)
        
        # Verify the output
        assert Path(output_path).exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "index" in data
        assert len(data["index"]) == len(items)
    
    def test_generate_combined_data_with_real_data(self, temp_dir, sample_rdf_file):
        """Test combined data generation with real RDF data."""
        from zotero_webviewer.rdf_parser import RDFParser
        from zotero_webviewer.data_transformer import DataTransformer
        from zotero_webviewer.collection_builder import CollectionHierarchyBuilder
        
        # Parse real RDF data
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        items_data = parser.extract_bibliography_items()
        collections_data = parser.extract_collections()
        
        # Transform the data
        transformer = DataTransformer()
        items = [transformer.transform_bibliography_item(item_data) for item_data in items_data]
        collections = [transformer.transform_collection(col_data) for col_data in collections_data]
        
        # Build hierarchy
        builder = CollectionHierarchyBuilder()
        hierarchy = builder.build_hierarchy(collections)
        
        # Generate combined data
        generator = JSONGenerator(str(temp_dir))
        output_path = generator.generate_combined_data(items, hierarchy)
        
        # Verify the output
        assert Path(output_path).exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "bibliography" in data
        assert "collections" in data
    
    def test_validate_json_files_basic(self, temp_dir):
        """Test basic JSON file validation."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create valid and invalid JSON files
        valid_file = generator.output_dir / "valid.json"
        invalid_file = generator.output_dir / "invalid.json"
        
        valid_file.write_text('{"test": true}')
        invalid_file.write_text('{"invalid": json}')  # Missing quotes
        
        validation_results = generator.validate_json_files()
        
        # Should validate correctly
        assert str(valid_file) in validation_results
        assert str(invalid_file) in validation_results
        assert validation_results[str(valid_file)] is True
        assert validation_results[str(invalid_file)] is False
    
    def test_get_file_sizes_basic(self, temp_dir):
        """Test basic file size functionality."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create a JSON file
        test_file = generator.output_dir / "test.json"
        test_file.write_text('{"test": true}')
        
        file_sizes = generator.get_file_sizes()
        
        # Should include the test file
        assert str(test_file) in file_sizes
        assert file_sizes[str(test_file)] > 0
    
    def test_empty_items_list(self, temp_dir):
        """Test generating JSON with empty items list."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_bibliography_json([])
        
        # Should create valid JSON with empty items
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["metadata"]["total_items"] == 0
        assert data["items"] == []
    
    def test_empty_collections_list(self, temp_dir):
        """Test generating JSON with empty collections list."""
        generator = JSONGenerator(str(temp_dir))
        
        output_path = generator.generate_collections_json([])
        
        # Should create valid JSON with empty collections
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["metadata"]["total_collections"] == 0
        assert data["collections"] == {}
        assert data["tree"] == []
    
    def test_item_with_missing_fields(self, temp_dir):
        """Test generating JSON with items that have missing optional fields."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create item with minimal data
        minimal_item = BibliographyItem(id="minimal", title="Minimal Item")
        
        output_path = generator.generate_bibliography_json([minimal_item])
        
        # Should handle gracefully
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        item_data = data["items"][0]
        assert item_data["id"] == "minimal"
        assert item_data["title"] == "Minimal Item"
        # Optional fields should be excluded or have default values
    
    def test_collection_with_missing_fields(self, temp_dir):
        """Test generating JSON with collections that have missing optional fields."""
        generator = JSONGenerator(str(temp_dir))
        
        # Create collection with minimal data
        minimal_collection = Collection(id="minimal", title="Minimal Collection")
        
        output_path = generator.generate_collections_json([minimal_collection])
        
        # Should handle gracefully
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "minimal" in data["collections"]
        col_data = data["collections"]["minimal"]
        assert col_data["title"] == "Minimal Collection"
        assert col_data["itemCount"] == 0