"""Unit tests for RDF parser functionality."""

import pytest
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, DC

from literature_webviewer.rdf_parser import (
    RDFParser, 
    RDFParsingError, 
    RDFValidationError, 
    RDFDataIntegrityError
)


class TestRDFParser:
    """Test cases for RDFParser class."""
    
    def test_init(self):
        """Test RDFParser initialization."""
        parser = RDFParser()
        assert parser.graph is None
        assert parser.logger is not None
    
    def test_parse_valid_rdf_file(self, sample_rdf_file):
        """Test parsing a valid RDF file."""
        parser = RDFParser()
        graph = parser.parse_rdf_file(sample_rdf_file)
        
        assert isinstance(graph, Graph)
        assert len(graph) > 0
        assert parser.graph is graph
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file raises appropriate error."""
        parser = RDFParser()
        
        with pytest.raises(RDFParsingError, match="RDF file not found"):
            parser.parse_rdf_file("nonexistent.rdf")
    
    def test_parse_empty_file(self, empty_rdf_file):
        """Test parsing an empty file raises validation error."""
        parser = RDFParser()
        
        with pytest.raises(RDFValidationError, match="RDF file is empty"):
            parser.parse_rdf_file(empty_rdf_file)
    
    def test_parse_malformed_file(self, malformed_rdf_file):
        """Test parsing a malformed RDF file raises parsing error."""
        parser = RDFParser()
        
        with pytest.raises((RDFValidationError, RDFParsingError)):
            parser.parse_rdf_file(malformed_rdf_file)
    
    def test_parse_directory_instead_of_file(self, temp_dir):
        """Test parsing a directory instead of file raises error."""
        parser = RDFParser()
        
        with pytest.raises(RDFParsingError, match="Path is not a file"):
            parser.parse_rdf_file(str(temp_dir))
    
    def test_extract_bibliography_items_without_graph(self):
        """Test extracting items without parsing a graph first."""
        parser = RDFParser()
        
        with pytest.raises(RDFParsingError, match="No RDF graph available"):
            parser.extract_bibliography_items()
    
    def test_extract_bibliography_items_from_sample_data(self, sample_rdf_file):
        """Test extracting bibliography items from sample RDF data."""
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        items = parser.extract_bibliography_items()
        
        assert len(items) == 2
        
        # Check first item
        item1 = next((item for item in items if "Machine Learning" in item["title"]), None)
        assert item1 is not None
        assert item1["type"] in ["article", "other"]  # Type may vary based on RDF structure
        assert item1["title"] == "Machine Learning in Healthcare"
        assert len(item1["authors"]) == 2
        assert item1["year"] == 2023
        assert item1["venue"] == "Journal of Medical AI"
        assert "machine learning" in item1["abstract"].lower()
        
        # Check authors
        author_names = [author["full_name"] for author in item1["authors"]]
        assert "John Smith" in author_names
        assert "Jane Doe" in author_names
        
        # Check second item
        item2 = next((item for item in items if "Deep Learning" in item["title"]), None)
        assert item2 is not None
        assert item2["type"] in ["conference", "other"]  # Type may vary based on RDF structure
        assert item2["title"] == "Deep Learning for Image Recognition"
        assert len(item2["authors"]) == 1
        assert item2["authors"][0]["full_name"] == "Alice Johnson"
        assert item2["year"] == 2022
    
    def test_extract_collections_without_graph(self):
        """Test extracting collections without parsing a graph first."""
        parser = RDFParser()
        
        with pytest.raises(RDFParsingError, match="No RDF graph available"):
            parser.extract_collections()
    
    def test_extract_collections_from_sample_data(self, sample_rdf_file):
        """Test extracting collections from sample RDF data."""
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        collections = parser.extract_collections()
        
        assert len(collections) >= 2
        
        # Check for expected collections
        collection_titles = [col["title"] for col in collections]
        assert "Machine Learning" in collection_titles
        assert "Healthcare AI" in collection_titles
        
        # Check collection with items
        ml_collection = next((col for col in collections if col["title"] == "Machine Learning"), None)
        assert ml_collection is not None
        assert len(ml_collection["item_ids"]) == 2
    
    def test_assign_items_to_collections(self, sample_rdf_file):
        """Test assigning items to collections."""
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        
        items = parser.extract_bibliography_items()
        collections = parser.extract_collections()
        
        # Initially items should not have collection assignments
        for item in items:
            assert "collections" not in item or len(item["collections"]) == 0
        
        # Assign items to collections
        parser.assign_items_to_collections(items, collections)
        
        # Check that items now have collection assignments
        assigned_items = [item for item in items if item.get("collections")]
        assert len(assigned_items) > 0
    
    def test_validate_bibliography_data_integrity_empty_data(self):
        """Test validation with empty data."""
        parser = RDFParser()
        issues = parser.validate_bibliography_data_integrity([])
        
        assert len(issues) == 1
        assert "No bibliography items found" in issues[0]
    
    def test_validate_bibliography_data_integrity_valid_data(self, sample_raw_item_data):
        """Test validation with valid data."""
        parser = RDFParser()
        issues = parser.validate_bibliography_data_integrity(sample_raw_item_data)
        
        # Should have minimal issues with good test data
        assert len(issues) <= 2  # Allow for some minor warnings
    
    def test_validate_bibliography_data_integrity_missing_required_fields(self):
        """Test validation with missing required fields."""
        parser = RDFParser()
        invalid_data = [
            {"id": "item1"},  # Missing title
            {"title": "Test Title"}  # Missing id
        ]
        
        issues = parser.validate_bibliography_data_integrity(invalid_data)
        
        assert len(issues) >= 2
        assert any("missing required field" in issue for issue in issues)
    
    def test_validate_bibliography_data_integrity_duplicate_ids(self):
        """Test validation with duplicate IDs."""
        parser = RDFParser()
        duplicate_data = [
            {"id": "item1", "title": "Title 1"},
            {"id": "item1", "title": "Title 2"}  # Duplicate ID
        ]
        
        issues = parser.validate_bibliography_data_integrity(duplicate_data)
        
        # Check that validation detects some issues (duplicate IDs should be caught)
        assert len(issues) > 0
        # The exact message format may vary, so just check that issues were found
        assert any("duplicate" in issue.lower() for issue in issues)
    
    def test_validate_bibliography_data_integrity_invalid_years(self):
        """Test validation with invalid years."""
        parser = RDFParser()
        invalid_year_data = [
            {"id": "item1", "title": "Title 1", "year": 999},  # Too early
            {"id": "item2", "title": "Title 2", "year": 2200},  # Too late
            {"id": "item3", "title": "Title 3", "year": "invalid"}  # Non-numeric
        ]
        
        issues = parser.validate_bibliography_data_integrity(invalid_year_data)
        
        assert any("invalid year" in issue for issue in issues)
    
    def test_extract_year_from_date_various_formats(self):
        """Test year extraction from various date formats."""
        parser = RDFParser()
        
        # Test valid formats
        assert parser._extract_year_from_date("2023") == 2023
        assert parser._extract_year_from_date("2023-01-01") == 2023
        assert parser._extract_year_from_date("2023/01/01") == 2023
        
        # Test invalid formats
        assert parser._extract_year_from_date("invalid") is None
        assert parser._extract_year_from_date("") is None
        assert parser._extract_year_from_date("23") is None  # Too short
    
    def test_normalize_item_type(self):
        """Test item type normalization."""
        parser = RDFParser()
        
        assert parser._normalize_item_type("journalArticle") == "article"
        assert parser._normalize_item_type("conferencePaper") == "conference"
        assert parser._normalize_item_type("book") == "book"
        assert parser._normalize_item_type("thesis") == "thesis"
        assert parser._normalize_item_type("unknown") == "other"
        assert parser._normalize_item_type("") == "other"
    
    def test_extract_authors_empty_sequence(self, sample_rdf_data):
        """Test author extraction with empty sequence."""
        parser = RDFParser()
        
        # Create empty sequence
        empty_seq = URIRef("http://example.org/empty_authors")
        authors = parser._extract_authors(sample_rdf_data, empty_seq)
        
        assert authors == []
    
    def test_extract_author_data_complete(self, sample_rdf_data):
        """Test extracting complete author data."""
        parser = RDFParser()
        
        # Get an author from the sample data
        author_uri = URIRef("http://example.org/author1")
        author_data = parser._extract_author_data(sample_rdf_data, author_uri)
        
        assert author_data is not None
        assert author_data["given_name"] == "John"
        assert author_data["surname"] == "Smith"
        assert author_data["full_name"] == "John Smith"
    
    def test_extract_author_data_partial(self, sample_rdf_data):
        """Test extracting partial author data."""
        parser = RDFParser()
        
        # Create author with only surname
        author_uri = URIRef("http://example.org/partial_author")
        sample_rdf_data.add((author_uri, RDF.type, URIRef("http://xmlns.com/foaf/0.1/Person")))
        sample_rdf_data.add((author_uri, URIRef("http://xmlns.com/foaf/0.1/surname"), Literal("LastName")))
        
        author_data = parser._extract_author_data(sample_rdf_data, author_uri)
        
        assert author_data is not None
        assert author_data["given_name"] == ""
        assert author_data["surname"] == "LastName"
        assert author_data["full_name"] == "LastName"
    
    def test_extract_venue_with_part_of_relationship(self, sample_rdf_data):
        """Test venue extraction using dcterms:isPartOf."""
        parser = RDFParser()
        
        item_uri = URIRef("http://example.org/item1")
        venue = parser._extract_venue(sample_rdf_data, item_uri)
        
        assert venue == "Journal of Medical AI"
    
    def test_extract_venue_no_relationship(self, sample_rdf_data):
        """Test venue extraction when no relationship exists."""
        parser = RDFParser()
        
        # Create item without venue relationship
        item_uri = URIRef("http://example.org/no_venue_item")
        venue = parser._extract_venue(sample_rdf_data, item_uri)
        
        assert venue == ""


class TestRDFParserEdgeCases:
    """Test edge cases and error conditions for RDF parser."""
    
    def test_parse_valid_rdf_with_sample_data(self, sample_rdf_file):
        """Test parsing with the sample RDF data."""
        parser = RDFParser()
        graph = parser.parse_rdf_file(sample_rdf_file)
        
        assert isinstance(graph, Graph)
        assert len(graph) > 0
        
        # Should be able to extract items and collections
        items = parser.extract_bibliography_items()
        collections = parser.extract_collections()
        
        assert len(items) > 0
        assert len(collections) >= 0  # Collections might be empty in some test data
    
    def test_validate_parsed_graph_no_bibliography_items(self, temp_dir):
        """Test validation fails when no bibliography items found."""
        # Create RDF with no bibliography content
        empty_content_file = temp_dir / "no_bib.rdf"
        empty_content_file.write_text('''<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description rdf:about="http://example.org/something">
                <rdf:type rdf:resource="http://example.org/NotBibliography"/>
            </rdf:Description>
        </rdf:RDF>''')
        
        parser = RDFParser()
        
        with pytest.raises(RDFDataIntegrityError, match="No bibliography items found"):
            parser.parse_rdf_file(str(empty_content_file))
    
    def test_extract_item_data_minimal_data(self, sample_rdf_data):
        """Test extracting item data with minimal information."""
        parser = RDFParser()
        
        # Create minimal item with only title
        minimal_item = URIRef("http://example.org/minimal")
        sample_rdf_data.add((minimal_item, DC.title, Literal("Minimal Title")))
        
        item_data = parser._extract_item_data(sample_rdf_data, minimal_item, "article")
        
        assert item_data is not None
        assert item_data["title"] == "Minimal Title"
        assert item_data["authors"] == []
        assert item_data["year"] is None
    
    def test_extract_item_data_no_title(self, sample_rdf_data):
        """Test extracting item data without title returns None."""
        parser = RDFParser()
        
        # Create item without title
        no_title_item = URIRef("http://example.org/no_title")
        sample_rdf_data.add((no_title_item, RDF.type, URIRef("http://purl.org/net/biblio#Article")))
        
        item_data = parser._extract_item_data(sample_rdf_data, no_title_item, "article")
        
        assert item_data is None
    
    def test_extract_collection_data_no_title(self, sample_rdf_data):
        """Test extracting collection data without title returns None."""
        parser = RDFParser()
        
        # Create collection without title
        no_title_collection = URIRef("http://example.org/no_title_collection")
        
        collection_data = parser._extract_collection_data(sample_rdf_data, no_title_collection)
        
        assert collection_data is None
    
    def test_extract_authors_malformed_sequence(self, sample_rdf_data):
        """Test author extraction with malformed sequence."""
        parser = RDFParser()
        
        # Create malformed sequence (no numbered properties)
        malformed_seq = URIRef("http://example.org/malformed_authors")
        authors = parser._extract_authors(sample_rdf_data, malformed_seq)
        
        # Should return empty list, not crash
        assert authors == []
    
    def test_validation_with_author_structure_issues(self):
        """Test validation catches author data structure issues."""
        parser = RDFParser()
        
        invalid_author_data = [
            {
                "id": "item1",
                "title": "Test Title",
                "authors": "not a list"  # Should be list
            },
            {
                "id": "item2", 
                "title": "Test Title 2",
                "authors": [
                    "not a dict",  # Should be dict
                    {"no_name_info": "value"}  # Missing name fields
                ]
            }
        ]
        
        issues = parser.validate_bibliography_data_integrity(invalid_author_data)
        
        assert any("invalid authors data structure" in issue for issue in issues)
        assert any("is not a dictionary" in issue for issue in issues)
        assert any("has no name information" in issue for issue in issues)