"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, DC, DCTERMS, FOAF

from zotero_webviewer.data_transformer import BibliographyItem, Collection, Author, Attachment, ItemType


# Define Zotero-specific namespaces for test data
Z = Namespace("http://www.zotero.org/namespaces/export#")
BIB = Namespace("http://purl.org/net/biblio#")
LINK = Namespace("http://purl.org/rss/1.0/modules/link/")
VCARD = Namespace("http://nwalsh.com/rdf/vCard#")
PRISM = Namespace("http://prismstandard.org/namespaces/1.2/basic/")


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_rdf_data():
    """Create sample RDF data for testing."""
    graph = Graph()
    
    # Bind namespaces
    graph.bind("z", Z)
    graph.bind("bib", BIB)
    graph.bind("dc", DC)
    graph.bind("dcterms", DCTERMS)
    graph.bind("foaf", FOAF)
    
    # Create sample bibliography items
    item1 = URIRef("http://example.org/item1")
    item2 = URIRef("http://example.org/item2")
    
    # Item 1: Journal Article
    graph.add((item1, RDF.type, BIB.Article))
    graph.add((item1, DC.title, Literal("Machine Learning in Healthcare")))
    graph.add((item1, DC.date, Literal("2023")))
    graph.add((item1, DCTERMS.abstract, Literal("This paper explores the applications of machine learning in healthcare.")))
    
    # Authors for item 1
    authors1 = URIRef("http://example.org/authors1")
    author1 = URIRef("http://example.org/author1")
    author2 = URIRef("http://example.org/author2")
    
    graph.add((item1, BIB.authors, authors1))
    graph.add((authors1, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_1"), author1))
    graph.add((authors1, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_2"), author2))
    
    graph.add((author1, RDF.type, FOAF.Person))
    graph.add((author1, FOAF.givenName, Literal("John")))
    graph.add((author1, FOAF.surname, Literal("Smith")))
    
    graph.add((author2, RDF.type, FOAF.Person))
    graph.add((author2, FOAF.givenName, Literal("Jane")))
    graph.add((author2, FOAF.surname, Literal("Doe")))
    
    # Venue for item 1
    venue1 = URIRef("http://example.org/venue1")
    graph.add((item1, DCTERMS.isPartOf, venue1))
    graph.add((venue1, DC.title, Literal("Journal of Medical AI")))
    
    # Item 2: Conference Paper
    graph.add((item2, RDF.type, BIB.ConferencePaper))
    graph.add((item2, DC.title, Literal("Deep Learning for Image Recognition")))
    graph.add((item2, DC.date, Literal("2022")))
    
    # Authors for item 2
    authors2 = URIRef("http://example.org/authors2")
    author3 = URIRef("http://example.org/author3")
    
    graph.add((item2, BIB.authors, authors2))
    graph.add((authors2, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_1"), author3))
    
    graph.add((author3, RDF.type, FOAF.Person))
    graph.add((author3, FOAF.givenName, Literal("Alice")))
    graph.add((author3, FOAF.surname, Literal("Johnson")))
    
    # Collections
    collection1 = URIRef("http://example.org/collection1")
    collection2 = URIRef("http://example.org/collection2")
    
    graph.add((collection1, DC.title, Literal("Machine Learning")))
    graph.add((collection1, DCTERMS.hasPart, item1))
    graph.add((collection1, DCTERMS.hasPart, item2))
    
    graph.add((collection2, DC.title, Literal("Healthcare AI")))
    graph.add((collection2, DCTERMS.hasPart, item1))
    
    return graph


@pytest.fixture
def sample_rdf_file(temp_dir, sample_rdf_data):
    """Create a sample RDF file for testing."""
    rdf_file = temp_dir / "sample.rdf"
    sample_rdf_data.serialize(destination=str(rdf_file), format="xml")
    return str(rdf_file)


@pytest.fixture
def malformed_rdf_file(temp_dir):
    """Create a malformed RDF file for testing error handling."""
    rdf_file = temp_dir / "malformed.rdf"
    rdf_file.write_text("<?xml version='1.0'?><rdf:RDF><invalid>content</rdf:RDF>")
    return str(rdf_file)


@pytest.fixture
def empty_rdf_file(temp_dir):
    """Create an empty RDF file for testing."""
    rdf_file = temp_dir / "empty.rdf"
    rdf_file.write_text("")
    return str(rdf_file)


@pytest.fixture
def sample_bibliography_items():
    """Create sample bibliography items for testing."""
    return [
        BibliographyItem(
            id="item1",
            type=ItemType.ARTICLE,
            title="Machine Learning in Healthcare",
            authors=[
                Author(given_name="John", surname="Smith", full_name="John Smith"),
                Author(given_name="Jane", surname="Doe", full_name="Jane Doe")
            ],
            year=2023,
            venue="Journal of Medical AI",
            abstract="This paper explores the applications of machine learning in healthcare.",
            doi="https://doi.org/10.1000/example1",
            collections=["collection1", "collection2"]
        ),
        BibliographyItem(
            id="item2",
            type=ItemType.CONFERENCE,
            title="Deep Learning for Image Recognition",
            authors=[
                Author(given_name="Alice", surname="Johnson", full_name="Alice Johnson")
            ],
            year=2022,
            venue="Conference on Computer Vision",
            collections=["collection1"]
        ),
        BibliographyItem(
            id="item3",
            type=ItemType.BOOK,
            title="Introduction to Data Science",
            authors=[
                Author(given_name="Bob", surname="Wilson", full_name="Bob Wilson")
            ],
            year=2021,
            venue="Academic Press",
            collections=[]
        )
    ]


@pytest.fixture
def sample_collections():
    """Create sample collections for testing."""
    collection1 = Collection(
        id="collection1",
        title="Machine Learning",
        item_ids=["item1", "item2"]
    )
    
    collection2 = Collection(
        id="collection2",
        title="Healthcare AI",
        parent_id="collection1",
        item_ids=["item1"]
    )
    
    collection3 = Collection(
        id="collection3",
        title="Computer Vision",
        item_ids=["item2"]
    )
    
    # Set up parent-child relationship
    collection1.add_child(collection2)
    
    return [collection1, collection2, collection3]


@pytest.fixture
def sample_raw_item_data():
    """Create sample raw item data as would come from RDF parser."""
    return [
        {
            "id": "http://example.org/item1",
            "type": "article",
            "title": "Machine Learning in Healthcare",
            "authors": [
                {"given_name": "John", "surname": "Smith", "full_name": "John Smith"},
                {"given_name": "Jane", "surname": "Doe", "full_name": "Jane Doe"}
            ],
            "year": 2023,
            "venue": "Journal of Medical AI",
            "abstract": "This paper explores the applications of machine learning in healthcare.",
            "doi": "https://doi.org/10.1000/example1",
            "url": "",
            "keywords": [],
            "collections": ["collection1", "collection2"],
            "attachments": []
        },
        {
            "id": "http://example.org/item2",
            "type": "conference",
            "title": "Deep Learning for Image Recognition",
            "authors": [
                {"given_name": "Alice", "surname": "Johnson", "full_name": "Alice Johnson"}
            ],
            "year": 2022,
            "venue": "Conference on Computer Vision",
            "abstract": "",
            "doi": "",
            "url": "https://example.org/paper2",
            "keywords": ["deep learning", "computer vision"],
            "collections": ["collection1"],
            "attachments": [
                {
                    "id": "attachment1",
                    "title": "Full Text PDF",
                    "type": "application/pdf",
                    "url": "https://example.org/paper2.pdf"
                }
            ]
        }
    ]


@pytest.fixture
def sample_raw_collection_data():
    """Create sample raw collection data as would come from RDF parser."""
    return [
        {
            "id": "collection1",
            "title": "Machine Learning",
            "parent_id": None,
            "item_ids": ["http://example.org/item1", "http://example.org/item2"]
        },
        {
            "id": "collection2",
            "title": "Healthcare AI",
            "parent_id": "collection1",
            "item_ids": ["http://example.org/item1"]
        },
        {
            "id": "collection3",
            "title": "Computer Vision",
            "parent_id": None,
            "item_ids": ["http://example.org/item2"]
        }
    ]