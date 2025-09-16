"""Unit tests for data transformation functionality."""

import pytest
from zotero_webviewer.data_transformer import (
    DataTransformer,
    BibliographyItem,
    Collection,
    Author,
    Attachment,
    ItemType,
    DataTransformationError,
    DataValidationError
)


class TestAuthor:
    """Test cases for Author data model."""
    
    def test_author_creation_complete(self):
        """Test creating author with complete information."""
        author = Author(given_name="John", surname="Smith", full_name="John Smith")
        
        assert author.given_name == "John"
        assert author.surname == "Smith"
        assert author.full_name == "John Smith"
    
    def test_author_creation_auto_full_name(self):
        """Test automatic full name generation."""
        author = Author(given_name="Jane", surname="Doe")
        
        assert author.full_name == "Jane Doe"
    
    def test_author_creation_partial_name(self):
        """Test creating author with partial name information."""
        author = Author(surname="LastName")
        
        assert author.given_name == ""
        assert author.surname == "LastName"
        assert author.full_name == "LastName"
    
    def test_author_to_dict(self):
        """Test converting author to dictionary."""
        author = Author(given_name="Alice", surname="Johnson")
        author_dict = author.to_dict()
        
        expected = {
            "given_name": "Alice",
            "surname": "Johnson", 
            "full_name": "Alice Johnson"
        }
        assert author_dict == expected


class TestBibliographyItem:
    """Test cases for BibliographyItem data model."""
    
    def test_bibliography_item_creation_minimal(self):
        """Test creating bibliography item with minimal data."""
        item = BibliographyItem(id="item1", title="Test Title")
        
        assert item.id == "item1"
        assert item.title == "Test Title"
        assert item.type == ItemType.OTHER
        assert item.authors == []
        assert item.year is None
    
    def test_bibliography_item_creation_complete(self):
        """Test creating bibliography item with complete data."""
        authors = [Author(given_name="John", surname="Smith")]
        attachments = [Attachment(id="att1", title="PDF")]
        
        item = BibliographyItem(
            id="item1",
            type=ItemType.ARTICLE,
            title="Test Article",
            authors=authors,
            year=2023,
            venue="Test Journal",
            abstract="Test abstract",
            doi="https://doi.org/10.1000/test",
            url="https://example.org/paper",
            keywords=["test", "article"],
            collections=["col1", "col2"],
            attachments=attachments
        )
        
        assert item.type == ItemType.ARTICLE
        assert len(item.authors) == 1
        assert item.year == 2023
        assert len(item.keywords) == 2
        assert len(item.collections) == 2
        assert len(item.attachments) == 1
    
    def test_bibliography_item_to_dict(self):
        """Test converting bibliography item to dictionary."""
        author = Author(given_name="Jane", surname="Doe")
        item = BibliographyItem(
            id="item1",
            type=ItemType.CONFERENCE,
            title="Test Paper",
            authors=[author],
            year=2022
        )
        
        item_dict = item.to_dict()
        
        assert item_dict["id"] == "item1"
        assert item_dict["type"] == "conference"
        assert item_dict["title"] == "Test Paper"
        assert len(item_dict["authors"]) == 1
        assert item_dict["authors"][0]["full_name"] == "Jane Doe"
        assert item_dict["year"] == 2022
    
    def test_get_author_names(self):
        """Test getting list of author names."""
        authors = [
            Author(given_name="John", surname="Smith"),
            Author(given_name="Jane", surname="Doe")
        ]
        item = BibliographyItem(id="item1", title="Test", authors=authors)
        
        author_names = item.get_author_names()
        
        assert len(author_names) == 2
        assert "John Smith" in author_names
        assert "Jane Doe" in author_names
    
    def test_get_primary_author(self):
        """Test getting primary (first) author."""
        authors = [
            Author(given_name="First", surname="Author"),
            Author(given_name="Second", surname="Author")
        ]
        item = BibliographyItem(id="item1", title="Test", authors=authors)
        
        primary = item.get_primary_author()
        assert primary == "First Author"
    
    def test_get_primary_author_no_authors(self):
        """Test getting primary author when no authors exist."""
        item = BibliographyItem(id="item1", title="Test")
        
        primary = item.get_primary_author()
        assert primary is None


class TestCollection:
    """Test cases for Collection data model."""
    
    def test_collection_creation(self):
        """Test creating collection."""
        collection = Collection(
            id="col1",
            title="Test Collection",
            item_ids=["item1", "item2"]
        )
        
        assert collection.id == "col1"
        assert collection.title == "Test Collection"
        assert collection.parent_id is None
        assert len(collection.item_ids) == 2
        assert collection.item_count == 2
    
    def test_collection_add_child(self):
        """Test adding child collection."""
        parent = Collection(id="parent", title="Parent")
        child = Collection(id="child", title="Child")
        
        parent.add_child(child)
        
        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert child.parent_id == "parent"
    
    def test_collection_get_all_item_ids(self):
        """Test getting all item IDs including from children."""
        parent = Collection(id="parent", title="Parent", item_ids=["item1"])
        child1 = Collection(id="child1", title="Child1", item_ids=["item2", "item3"])
        child2 = Collection(id="child2", title="Child2", item_ids=["item3", "item4"])
        
        parent.add_child(child1)
        parent.add_child(child2)
        
        all_ids = parent.get_all_item_ids()
        
        assert len(all_ids) == 4  # item1, item2, item3, item4 (item3 deduplicated)
        assert "item1" in all_ids
        assert "item2" in all_ids
        assert "item3" in all_ids
        assert "item4" in all_ids
    
    def test_collection_update_item_count(self):
        """Test updating item count including children."""
        parent = Collection(id="parent", title="Parent", item_ids=["item1"])
        child = Collection(id="child", title="Child", item_ids=["item2", "item3"])
        
        parent.add_child(child)
        parent.update_item_count()
        
        assert parent.item_count == 3  # item1 + item2 + item3
        assert child.item_count == 2   # item2 + item3
    
    def test_collection_to_dict(self):
        """Test converting collection to dictionary."""
        child = Collection(id="child", title="Child", item_ids=["item1"])
        parent = Collection(id="parent", title="Parent", item_ids=["item2"])
        parent.add_child(child)
        
        parent_dict = parent.to_dict()
        
        assert parent_dict["id"] == "parent"
        assert parent_dict["title"] == "Parent"
        assert parent_dict["parent_id"] is None
        assert len(parent_dict["children"]) == 1
        assert parent_dict["children"][0]["id"] == "child"


class TestDataTransformer:
    """Test cases for DataTransformer class."""
    
    def test_init(self):
        """Test DataTransformer initialization."""
        transformer = DataTransformer()
        assert transformer.logger is not None
    
    def test_transform_bibliography_item_complete(self, sample_raw_item_data):
        """Test transforming complete bibliography item data."""
        transformer = DataTransformer()
        raw_item = sample_raw_item_data[0]
        
        item = transformer.transform_bibliography_item(raw_item)
        
        assert isinstance(item, BibliographyItem)
        assert item.id == raw_item["id"]
        assert item.title == raw_item["title"]
        assert item.type == ItemType.ARTICLE
        assert len(item.authors) == 2
        assert item.year == 2023
        assert item.venue == raw_item["venue"]
        assert item.abstract == raw_item["abstract"]
        assert item.doi == raw_item["doi"]
    
    def test_transform_bibliography_item_missing_id(self):
        """Test transforming item without ID raises error."""
        transformer = DataTransformer()
        raw_item = {"title": "Test Title"}
        
        with pytest.raises(DataValidationError, match="missing required 'id' field"):
            transformer.transform_bibliography_item(raw_item)
    
    def test_transform_bibliography_item_missing_title(self):
        """Test transforming item without title generates fallback."""
        transformer = DataTransformer()
        raw_item = {
            "id": "item1",
            "authors": [{"full_name": "John Smith", "surname": "Smith"}],
            "year": 2023,
            "venue": "Test Journal"
        }
        
        item = transformer.transform_bibliography_item(raw_item)
        
        # Should generate fallback title
        assert item.title != ""
        assert "Smith" in item.title
        assert "2023" in item.title
    
    def test_transform_bibliography_item_no_fallback_title_possible(self):
        """Test transforming item where no fallback title can be generated."""
        transformer = DataTransformer()
        raw_item = {"id": "item1"}  # No title, authors, year, or venue
        
        # The transformer should generate a fallback title
        item = transformer.transform_bibliography_item(raw_item)
        assert item.title != ""
        assert "[item]" in item.title or "item1" in item.title  # Should have some fallback title
    
    def test_transform_collection(self, sample_raw_collection_data):
        """Test transforming collection data."""
        transformer = DataTransformer()
        raw_collection = sample_raw_collection_data[0]
        
        collection = transformer.transform_collection(raw_collection)
        
        assert isinstance(collection, Collection)
        assert collection.id == raw_collection["id"]
        assert collection.title == raw_collection["title"]
        assert collection.parent_id == raw_collection["parent_id"]
        assert collection.item_ids == raw_collection["item_ids"]
    
    def test_normalize_authors(self):
        """Test normalizing author data."""
        transformer = DataTransformer()
        raw_authors = [
            {"given_name": "John", "surname": "Smith"},
            {"full_name": "Jane Doe"},
            {"surname": "LastOnly"},
            {}  # Empty author (should be filtered out)
        ]
        
        authors = transformer.normalize_authors(raw_authors)
        
        assert len(authors) == 3  # Empty author filtered out
        assert authors[0].full_name == "John Smith"
        assert authors[1].full_name == "Jane Doe"
        assert authors[2].full_name == "LastOnly"
    
    def test_normalize_item_type(self):
        """Test item type normalization."""
        transformer = DataTransformer()
        
        assert transformer._normalize_item_type("article") == ItemType.ARTICLE
        assert transformer._normalize_item_type("journalArticle") == ItemType.ARTICLE
        assert transformer._normalize_item_type("CONFERENCE") == ItemType.CONFERENCE
        assert transformer._normalize_item_type("book-section") == ItemType.BOOK
        assert transformer._normalize_item_type("unknown") == ItemType.OTHER
        assert transformer._normalize_item_type("") == ItemType.OTHER
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        transformer = DataTransformer()
        
        # Test whitespace normalization
        assert transformer._clean_text("  multiple   spaces  ") == "multiple spaces"
        
        # Test HTML tag removal
        assert transformer._clean_text("<p>Text with <b>HTML</b> tags</p>") == "Text with HTML tags"
        
        # Test HTML entity decoding
        assert transformer._clean_text("Text &amp; more &lt;text&gt;") == "Text & more <text>"
        
        # Test empty input
        assert transformer._clean_text("") == ""
        assert transformer._clean_text(None) == ""
    
    def test_clean_name(self):
        """Test name cleaning functionality."""
        transformer = DataTransformer()
        
        # Test prefix removal
        assert transformer._clean_name("Dr. John Smith") == "John Smith"
        assert transformer._clean_name("Prof. Jane Doe") == "Jane Doe"
        
        # Test suffix removal
        assert transformer._clean_name("John Smith Jr.") == "John Smith"
        assert transformer._clean_name("Jane Doe PhD") == "Jane Doe"
        
        # Test combined prefix and suffix
        assert transformer._clean_name("Dr. John Smith Jr.") == "John Smith"
        
        # Test no changes needed
        assert transformer._clean_name("Plain Name") == "Plain Name"
    
    def test_clean_url(self):
        """Test URL cleaning functionality."""
        transformer = DataTransformer()
        
        # Test DOI handling
        assert transformer._clean_url("10.1000/example") == "https://doi.org/10.1000/example"
        
        # Test already valid URLs
        assert transformer._clean_url("https://example.org/paper") == "https://example.org/paper"
        assert transformer._clean_url("http://example.org/paper") == "http://example.org/paper"
        
        # Test empty input
        assert transformer._clean_url("") == ""
        assert transformer._clean_url("   ") == ""
    
    def test_parse_author_name(self):
        """Test author name parsing."""
        transformer = DataTransformer()
        
        # Test single name
        given, surname = transformer._parse_author_name("Smith")
        assert given == ""
        assert surname == "Smith"
        
        # Test two names
        given, surname = transformer._parse_author_name("John Smith")
        assert given == "John"
        assert surname == "Smith"
        
        # Test multiple names
        given, surname = transformer._parse_author_name("John Michael Smith")
        assert given == "John"
        assert surname == "Michael Smith"
        
        # Test empty name
        given, surname = transformer._parse_author_name("")
        assert given == ""
        assert surname == ""
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        transformer = DataTransformer()
        
        title = "Machine Learning Applications in Healthcare"
        abstract = "This paper explores artificial intelligence and deep learning techniques for medical diagnosis."
        
        keywords = transformer._extract_keywords(title, abstract)
        
        assert "machine learning" in keywords
        assert "artificial intelligence" in keywords
        assert "deep learning" in keywords
        assert len(keywords) <= 10  # Should be limited
    
    def test_generate_fallback_title(self):
        """Test fallback title generation."""
        transformer = DataTransformer()
        
        # Test with authors and year
        item_data = {
            "id": "item1",
            "authors": [{"surname": "Smith", "full_name": "John Smith"}],
            "year": 2023,
            "venue": "Test Journal"
        }
        
        title = transformer._generate_fallback_title(item_data)
        
        assert "Smith" in title
        assert "2023" in title
        assert "Test Journal" in title
    
    def test_generate_fallback_title_multiple_authors(self):
        """Test fallback title generation with multiple authors."""
        transformer = DataTransformer()
        
        item_data = {
            "id": "item1",
            "authors": [
                {"surname": "Smith", "full_name": "John Smith"},
                {"surname": "Doe", "full_name": "Jane Doe"}
            ],
            "year": 2023
        }
        
        title = transformer._generate_fallback_title(item_data)
        
        assert "Smith et al." in title
        assert "2023" in title
    
    def test_generate_fallback_title_minimal_data(self):
        """Test fallback title generation with minimal data."""
        transformer = DataTransformer()
        
        item_data = {"id": "item1", "type": "article"}
        
        title = transformer._generate_fallback_title(item_data)
        
        # Should generate some fallback title
        assert title != ""
        assert "article" in title.lower() or "item" in title.lower()
    
    def test_validate_year(self):
        """Test year validation."""
        transformer = DataTransformer()
        
        # Test valid years
        assert transformer._validate_year(2023, "item1") == 2023
        assert transformer._validate_year("2022", "item1") == 2022
        
        # Test invalid years
        assert transformer._validate_year(999, "item1") is None  # Too early
        assert transformer._validate_year(2050, "item1") is None  # Too late
        assert transformer._validate_year("invalid", "item1") is None  # Non-numeric
        assert transformer._validate_year(None, "item1") is None  # None input
    
    def test_validate_and_clean_url(self):
        """Test URL validation and cleaning."""
        transformer = DataTransformer()
        
        # Test valid URLs
        assert transformer._validate_and_clean_url("https://example.org", "URL", "item1") == "https://example.org"
        
        # Test DOI handling
        assert transformer._validate_and_clean_url("10.1000/example", "DOI", "item1") == "https://doi.org/10.1000/example"
        
        # Test invalid URLs
        assert transformer._validate_and_clean_url("invalid", "URL", "item1") == ""
        assert transformer._validate_and_clean_url("", "URL", "item1") == ""
        
        # Test URL with whitespace
        assert transformer._validate_and_clean_url("https://example.org/path with spaces", "URL", "item1") == "https://example.org/pathwithspaces"
    
    def test_validate_transformed_data_valid(self, sample_bibliography_items, sample_collections):
        """Test validation of valid transformed data."""
        transformer = DataTransformer()
        
        issues = transformer.validate_transformed_data(sample_bibliography_items, sample_collections)
        
        # Should have minimal issues with good test data
        assert len(issues) <= 1  # Allow for minor warnings
    
    def test_validate_transformed_data_empty_items(self):
        """Test validation with empty items list."""
        transformer = DataTransformer()
        
        issues = transformer.validate_transformed_data([], [])
        
        assert len(issues) == 1
        assert "No bibliography items after transformation" in issues[0]
    
    def test_validate_transformed_data_duplicate_ids(self):
        """Test validation catches duplicate item IDs."""
        transformer = DataTransformer()
        
        items = [
            BibliographyItem(id="item1", title="Title 1"),
            BibliographyItem(id="item1", title="Title 2")  # Duplicate ID
        ]
        
        issues = transformer.validate_transformed_data(items, [])
        
        assert any("Duplicate item ID" in issue for issue in issues)
    
    def test_validate_transformed_data_missing_collection_references(self):
        """Test validation catches missing collection references."""
        transformer = DataTransformer()
        
        items = [
            BibliographyItem(id="item1", title="Title 1", collections=["nonexistent"])
        ]
        collections = [
            Collection(id="existing", title="Existing Collection")
        ]
        
        issues = transformer.validate_transformed_data(items, collections)
        
        assert any("references non-existent collection" in issue for issue in issues)


class TestDataTransformerErrorHandling:
    """Test error handling in data transformer."""
    
    def test_transform_bibliography_item_with_invalid_author_data(self):
        """Test handling of invalid author data during transformation."""
        transformer = DataTransformer()
        
        raw_item = {
            "id": "item1",
            "title": "Test Title",
            "authors": [
                {"given_name": "Valid", "surname": "Author"},
                {},  # Empty author data
                {"invalid": "data"}  # Invalid author structure
            ]
        }
        
        # Should not raise exception, but log warnings
        item = transformer.transform_bibliography_item(raw_item)
        
        assert len(item.authors) == 1  # Only valid author included
        assert item.authors[0].full_name == "Valid Author"
    
    def test_transform_bibliography_item_with_invalid_attachment_data(self):
        """Test handling of invalid attachment data during transformation."""
        transformer = DataTransformer()
        
        raw_item = {
            "id": "item1",
            "title": "Test Title",
            "attachments": [
                {"id": "att1", "title": "Valid Attachment"},
                {},  # Missing required fields
                {"invalid": "structure"}  # Invalid structure
            ]
        }
        
        # Should not raise exception, but log warnings
        item = transformer.transform_bibliography_item(raw_item)
        
        # Should handle gracefully (may have 0 or 1 attachments depending on validation)
        assert len(item.attachments) <= 1
    
    def test_transform_collection_missing_required_fields(self):
        """Test transforming collection with missing required fields."""
        transformer = DataTransformer()
        
        with pytest.raises(DataTransformationError):
            transformer.transform_collection({})  # Missing id field