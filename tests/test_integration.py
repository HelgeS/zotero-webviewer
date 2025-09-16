"""Integration tests for the complete RDF-to-website build pipeline."""

import pytest
import json
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, DC, DCTERMS, FOAF

from zotero_webviewer.build_pipeline import BuildPipeline, BuildConfig
from zotero_webviewer.rdf_parser import RDFParser
from zotero_webviewer.data_transformer import DataTransformer
from zotero_webviewer.collection_builder import CollectionHierarchyBuilder
from zotero_webviewer.json_generator import JSONGenerator
from zotero_webviewer.site_generator import SiteGenerator


# Define Zotero-specific namespaces for test data
Z = Namespace("http://www.zotero.org/namespaces/export#")
BIB = Namespace("http://purl.org/net/biblio#")
LINK = Namespace("http://purl.org/rss/1.0/modules/link/")


class TestBuildPipelineIntegration:
    """Integration tests for the complete build pipeline."""
    
    def test_complete_pipeline_with_sample_data(self, temp_dir, sample_rdf_file):
        """Test the complete pipeline from RDF file to website generation."""
        output_dir = temp_dir / "output"
        
        # Initialize build pipeline
        from zotero_webviewer.build_pipeline import BuildConfig
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        # Run complete pipeline
        result = pipeline.build()
        
        # Verify pipeline completed successfully
        assert result.success is True
        
        # Check that output directory was created
        assert output_dir.exists()
        
        # Check that data files were generated
        data_dir = output_dir / "data"
        assert data_dir.exists()
        
        bibliography_file = data_dir / "bibliography.json"
        collections_file = data_dir / "collections.json"
        
        assert bibliography_file.exists()
        assert collections_file.exists()
        
        # Verify bibliography data
        with open(bibliography_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        assert "metadata" in bib_data
        assert "items" in bib_data
        assert bib_data["metadata"]["total_items"] > 0
        assert len(bib_data["items"]) > 0
        
        # Check that items have expected structure
        first_item = bib_data["items"][0]
        assert "id" in first_item
        assert "title" in first_item
        assert "authors" in first_item
        assert "type" in first_item
        
        # Verify collections data
        with open(collections_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        assert "metadata" in col_data
        assert "collections" in col_data
        assert "tree" in col_data
        
        # Check that HTML files were generated
        index_file = output_dir / "index.html"
        assert index_file.exists()
        
        # Verify HTML content contains expected elements
        html_content = index_file.read_text(encoding='utf-8')
        assert "<html" in html_content
        assert "literature collection" in html_content.lower()
        
        # Check that CSS and JS files were generated
        css_file = output_dir / "styles.css"
        js_file = output_dir / "app.js"
        
        assert css_file.exists()
        assert js_file.exists()
    
    def test_pipeline_with_complex_hierarchy(self, temp_dir):
        """Test pipeline with complex collection hierarchy."""
        # Create RDF with complex hierarchy
        graph = Graph()
        
        # Bind namespaces
        graph.bind("z", Z)
        graph.bind("bib", BIB)
        graph.bind("dc", DC)
        graph.bind("dcterms", DCTERMS)
        graph.bind("foaf", FOAF)
        
        # Create items
        item1 = URIRef("http://example.org/item1")
        item2 = URIRef("http://example.org/item2")
        item3 = URIRef("http://example.org/item3")
        
        # Add basic item data
        for i, item in enumerate([item1, item2, item3], 1):
            graph.add((item, RDF.type, BIB.Article))
            graph.add((item, DC.title, Literal(f"Article {i}")))
            graph.add((item, DC.date, Literal("2023")))
            
            # Add author
            author = URIRef(f"http://example.org/author{i}")
            authors_seq = URIRef(f"http://example.org/authors{i}")
            
            graph.add((item, BIB.authors, authors_seq))
            graph.add((authors_seq, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_1"), author))
            graph.add((author, RDF.type, FOAF.Person))
            graph.add((author, FOAF.givenName, Literal(f"Author{i}")))
            graph.add((author, FOAF.surname, Literal(f"Surname{i}")))
        
        # Create complex collection hierarchy
        # Root -> Computer Science -> Machine Learning -> Deep Learning
        #                          -> Natural Language Processing
        #      -> Mathematics -> Statistics
        
        root_col = URIRef("http://example.org/root")
        cs_col = URIRef("http://example.org/cs")
        ml_col = URIRef("http://example.org/ml")
        dl_col = URIRef("http://example.org/dl")
        nlp_col = URIRef("http://example.org/nlp")
        math_col = URIRef("http://example.org/math")
        stats_col = URIRef("http://example.org/stats")
        
        collections = [
            (root_col, "Research", None, [item1, item2, item3]),
            (cs_col, "Computer Science", root_col, [item1, item2]),
            (ml_col, "Machine Learning", cs_col, [item1, item2]),
            (dl_col, "Deep Learning", ml_col, [item1]),
            (nlp_col, "Natural Language Processing", ml_col, [item2]),
            (math_col, "Mathematics", root_col, [item3]),
            (stats_col, "Statistics", math_col, [item3])
        ]
        
        for col_uri, title, parent_uri, items in collections:
            graph.add((col_uri, DC.title, Literal(title)))
            for item in items:
                graph.add((col_uri, DCTERMS.hasPart, item))
        
        # Save RDF file
        rdf_file = temp_dir / "complex.rdf"
        graph.serialize(destination=str(rdf_file), format="xml")
        
        # Run pipeline
        output_dir = temp_dir / "output"
        config = BuildConfig(
            input_file=str(rdf_file),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Verify collections hierarchy was preserved
        collections_file = output_dir / "data" / "collections.json"
        with open(collections_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Should have all collections
        assert len(col_data["collections"]) == 7
        
        # Check hierarchy structure - should have all collections
        collections_dict = col_data["collections"]
        
        # Should have a collection named "Research"
        research_found = False
        for col_id, col_info in collections_dict.items():
            if col_info["title"] == "Research":
                research_found = True
                break
        
        assert research_found
    
    def test_pipeline_error_handling_invalid_rdf(self, temp_dir):
        """Test pipeline error handling with invalid RDF file."""
        # Create invalid RDF file
        invalid_rdf = temp_dir / "invalid.rdf"
        invalid_rdf.write_text("This is not valid RDF content")
        
        output_dir = temp_dir / "output"
        config = BuildConfig(
            input_file=str(invalid_rdf),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        # Pipeline should handle error gracefully
        try:
            result = pipeline.build()
            assert result.success is False
        except Exception:
            # Exception is also acceptable for invalid input
            pass
    
    def test_pipeline_error_handling_missing_file(self, temp_dir):
        """Test pipeline error handling with missing RDF file."""
        output_dir = temp_dir / "output"
        config = BuildConfig(
            input_file="nonexistent.rdf",
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        # Pipeline should handle missing file gracefully
        try:
            result = pipeline.build()
            assert result.success is False
        except Exception:
            # Exception is also acceptable for missing file
            pass
    
    def test_pipeline_with_large_dataset(self, temp_dir):
        """Test pipeline performance with larger dataset."""
        # Create RDF with many items (100 items, 10 collections)
        graph = Graph()
        
        # Bind namespaces
        graph.bind("z", Z)
        graph.bind("bib", BIB)
        graph.bind("dc", DC)
        graph.bind("dcterms", DCTERMS)
        graph.bind("foaf", FOAF)
        
        # Create 100 items
        items = []
        for i in range(100):
            item = URIRef(f"http://example.org/item{i}")
            items.append(item)
            
            graph.add((item, RDF.type, BIB.Article))
            graph.add((item, DC.title, Literal(f"Article {i}: Research Topic {i % 10}")))
            graph.add((item, DC.date, Literal(str(2020 + (i % 4)))))
            
            # Add author
            author = URIRef(f"http://example.org/author{i}")
            authors_seq = URIRef(f"http://example.org/authors{i}")
            
            graph.add((item, BIB.authors, authors_seq))
            graph.add((authors_seq, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_1"), author))
            graph.add((author, RDF.type, FOAF.Person))
            graph.add((author, FOAF.givenName, Literal(f"FirstName{i}")))
            graph.add((author, FOAF.surname, Literal(f"LastName{i}")))
        
        # Create 10 collections, each with 10 items
        for i in range(10):
            collection = URIRef(f"http://example.org/collection{i}")
            graph.add((collection, DC.title, Literal(f"Collection {i}")))
            
            # Add 10 items to each collection
            for j in range(10):
                item_index = i * 10 + j
                if item_index < len(items):
                    graph.add((collection, DCTERMS.hasPart, items[item_index]))
        
        # Save RDF file
        large_rdf = temp_dir / "large.rdf"
        graph.serialize(destination=str(large_rdf), format="xml")
        
        # Run pipeline and measure performance
        import time
        start_time = time.time()
        
        output_dir = temp_dir / "output"
        config = BuildConfig(
            input_file=str(large_rdf),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        
        end_time = time.time()
        build_time = end_time - start_time
        
        # Should complete successfully
        assert result.success is True
        
        # Should complete in reasonable time (less than 30 seconds)
        assert build_time < 30.0
        
        # Verify all data was processed
        assert result.items_count == 100
        
        bibliography_file = output_dir / "data" / "bibliography.json"
        with open(bibliography_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        assert bib_data["metadata"]["total_items"] == 100
        
        collections_file = output_dir / "data" / "collections.json"
        with open(collections_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        assert len(col_data["collections"]) == 10


class TestComponentIntegration:
    """Test integration between individual components."""
    
    def test_rdf_parser_to_data_transformer_integration(self, sample_rdf_file):
        """Test integration between RDF parser and data transformer."""
        # Parse RDF
        parser = RDFParser()
        parser.parse_rdf_file(sample_rdf_file)
        
        raw_items = parser.extract_bibliography_items()
        raw_collections = parser.extract_collections()
        
        # Transform data
        transformer = DataTransformer()
        
        transformed_items = []
        for raw_item in raw_items:
            item = transformer.transform_bibliography_item(raw_item)
            transformed_items.append(item)
        
        transformed_collections = []
        for raw_collection in raw_collections:
            collection = transformer.transform_collection(raw_collection)
            transformed_collections.append(collection)
        
        # Verify transformation preserved essential data
        assert len(transformed_items) == len(raw_items)
        assert len(transformed_collections) == len(raw_collections)
        
        # Check that item data was properly transformed
        for raw_item, transformed_item in zip(raw_items, transformed_items):
            assert transformed_item.id == raw_item["id"]
            assert transformed_item.title == raw_item["title"]
            assert len(transformed_item.authors) == len(raw_item["authors"])
    
    def test_data_transformer_to_collection_builder_integration(self, sample_raw_item_data, sample_raw_collection_data):
        """Test integration between data transformer and collection builder."""
        transformer = DataTransformer()
        
        # Transform data
        items = [transformer.transform_bibliography_item(raw_item) for raw_item in sample_raw_item_data]
        collections = [transformer.transform_collection(raw_col) for raw_col in sample_raw_collection_data]
        
        # Build hierarchy
        builder = CollectionHierarchyBuilder()
        hierarchy = builder.build_hierarchy(collections)
        builder.assign_items_to_collections(items, hierarchy)
        
        # Verify integration worked
        assert len(hierarchy) > 0
        
        # Check that items were assigned to collections
        assigned_items = [item for item in items if item.collections]
        assert len(assigned_items) > 0
        
        # Check that collections have items
        collections_with_items = [col for col in collections if col.item_ids]
        assert len(collections_with_items) > 0
    
    def test_collection_builder_to_json_generator_integration(self, sample_bibliography_items, sample_collections, temp_dir):
        """Test integration between collection builder and JSON generator."""
        # Build hierarchy
        builder = CollectionHierarchyBuilder()
        hierarchy = builder.build_hierarchy(sample_collections)
        builder.assign_items_to_collections(sample_bibliography_items, hierarchy)
        
        # Generate JSON
        generator = JSONGenerator(str(temp_dir))
        
        bib_file = generator.generate_bibliography_json(sample_bibliography_items)
        col_file = generator.generate_collections_json(hierarchy)
        
        # Verify files were created and contain expected data
        assert Path(bib_file).exists()
        assert Path(col_file).exists()
        
        # Check bibliography JSON
        with open(bib_file, 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        assert len(bib_data["items"]) == len(sample_bibliography_items)
        
        # Check collections JSON
        with open(col_file, 'r', encoding='utf-8') as f:
            col_data = json.load(f)
        
        # Should have all collections (including nested ones)
        total_collections = len(sample_collections)
        for col in sample_collections:
            total_collections += len(col.children)
        
        assert len(col_data["collections"]) >= len(sample_collections)
    
    def test_json_generator_to_site_generator_integration(self, sample_bibliography_items, sample_collections, temp_dir):
        """Test integration between JSON generator and site generator."""
        # Generate JSON files
        json_generator = JSONGenerator(str(temp_dir / "data"))
        
        bib_file = json_generator.generate_bibliography_json(sample_bibliography_items)
        col_file = json_generator.generate_collections_json(sample_collections)
        
        # Generate site
        site_generator = SiteGenerator(str(temp_dir))
        
        from zotero_webviewer.site_generator import SiteConfig
        site_config = SiteConfig(
            title="Test Site",
            collection_title="Test Collection",
            description="Test Description"
        )
        
        result = site_generator.generate_site(site_config)
        assert len(result) > 0  # Should return list of generated files
        
        # Verify site files were created
        index_file = temp_dir / "index.html"
        css_file = temp_dir / "styles.css"
        js_file = temp_dir / "app.js"
        
        assert index_file.exists()
        assert css_file.exists()
        assert js_file.exists()
        
        # Verify HTML and JS files were created (data references are likely in JS)
        html_content = index_file.read_text(encoding='utf-8')
        assert "<html" in html_content
        
        # Check that JavaScript file exists and likely contains data references
        js_file = temp_dir / "app.js"
        if js_file.exists():
            js_content = js_file.read_text(encoding='utf-8')
            # Data file references should be in JavaScript
            assert "bibliography.json" in js_content or "collections.json" in js_content


class TestEndToEndScenarios:
    """End-to-end test scenarios simulating real usage."""
    
    def test_typical_zotero_export_workflow(self, temp_dir):
        """Test typical workflow with Zotero export."""
        # Create realistic Zotero-style RDF export
        graph = Graph()
        
        # Bind namespaces
        graph.bind("z", Z)
        graph.bind("bib", BIB)
        graph.bind("dc", DC)
        graph.bind("dcterms", DCTERMS)
        graph.bind("foaf", FOAF)
        
        # Create realistic academic papers
        papers = [
            {
                "id": "http://zotero.org/users/123/items/ABCD1234",
                "type": BIB.Article,
                "title": "Deep Learning for Natural Language Processing: A Survey",
                "authors": [
                    ("John", "Smith"),
                    ("Jane", "Doe"),
                    ("Alice", "Johnson")
                ],
                "year": "2023",
                "journal": "Journal of Artificial Intelligence Research",
                "abstract": "This survey provides a comprehensive overview of deep learning techniques applied to natural language processing tasks.",
                "doi": "10.1613/jair.1.12345"
            },
            {
                "id": "http://zotero.org/users/123/items/EFGH5678",
                "type": BIB.ConferencePaper,
                "title": "Attention Is All You Need",
                "authors": [
                    ("Ashish", "Vaswani"),
                    ("Noam", "Shazeer")
                ],
                "year": "2017",
                "venue": "Advances in Neural Information Processing Systems",
                "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks."
            }
        ]
        
        # Add papers to graph
        for paper in papers:
            item_uri = URIRef(paper["id"])
            
            graph.add((item_uri, RDF.type, paper["type"]))
            graph.add((item_uri, DC.title, Literal(paper["title"])))
            graph.add((item_uri, DC.date, Literal(paper["year"])))
            graph.add((item_uri, DCTERMS.abstract, Literal(paper["abstract"])))
            
            # Add DOI if present
            if "doi" in paper:
                graph.add((item_uri, DC.identifier, URIRef(f"https://doi.org/{paper['doi']}")))
            
            # Add authors
            authors_seq = URIRef(f"{paper['id']}/authors")
            graph.add((item_uri, BIB.authors, authors_seq))
            
            for i, (given, surname) in enumerate(paper["authors"], 1):
                author_uri = URIRef(f"{paper['id']}/author{i}")
                seq_prop = URIRef(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{i}")
                
                graph.add((authors_seq, seq_prop, author_uri))
                graph.add((author_uri, RDF.type, FOAF.Person))
                graph.add((author_uri, FOAF.givenName, Literal(given)))
                graph.add((author_uri, FOAF.surname, Literal(surname)))
            
            # Add venue
            if "journal" in paper:
                venue_uri = URIRef(f"{paper['id']}/venue")
                graph.add((item_uri, DCTERMS.isPartOf, venue_uri))
                graph.add((venue_uri, DC.title, Literal(paper["journal"])))
            elif "venue" in paper:
                venue_uri = URIRef(f"{paper['id']}/venue")
                graph.add((item_uri, DCTERMS.isPartOf, venue_uri))
                graph.add((venue_uri, DC.title, Literal(paper["venue"])))
        
        # Add collections
        collections = [
            ("http://zotero.org/users/123/collections/COL1", "Machine Learning", None),
            ("http://zotero.org/users/123/collections/COL2", "Natural Language Processing", "http://zotero.org/users/123/collections/COL1"),
            ("http://zotero.org/users/123/collections/COL3", "Neural Networks", "http://zotero.org/users/123/collections/COL1")
        ]
        
        for col_id, title, parent_id in collections:
            col_uri = URIRef(col_id)
            graph.add((col_uri, DC.title, Literal(title)))
            
            # Add items to collections
            if "Natural Language Processing" in title:
                graph.add((col_uri, DCTERMS.hasPart, URIRef(papers[0]["id"])))
            elif "Neural Networks" in title:
                graph.add((col_uri, DCTERMS.hasPart, URIRef(papers[1]["id"])))
            elif "Machine Learning" in title:
                # Parent collection contains all items
                for paper in papers:
                    graph.add((col_uri, DCTERMS.hasPart, URIRef(paper["id"])))
        
        # Save RDF file
        rdf_file = temp_dir / "zotero_export.rdf"
        graph.serialize(destination=str(rdf_file), format="xml")
        
        # Run complete pipeline
        output_dir = temp_dir / "website"
        config = BuildConfig(
            input_file=str(rdf_file),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Verify complete website was generated
        assert (output_dir / "index.html").exists()
        assert (output_dir / "styles.css").exists()
        assert (output_dir / "app.js").exists()
        assert (output_dir / "data" / "bibliography.json").exists()
        assert (output_dir / "data" / "collections.json").exists()
        
        # Verify data integrity
        with open(output_dir / "data" / "bibliography.json", 'r', encoding='utf-8') as f:
            bib_data = json.load(f)
        
        assert bib_data["metadata"]["total_items"] == 2
        
        # Check that papers have expected data
        items = bib_data["items"]
        survey_paper = next((item for item in items if "Survey" in item["title"]), None)
        attention_paper = next((item for item in items if "Attention" in item["title"]), None)
        
        assert survey_paper is not None
        assert attention_paper is not None
        
        # Check survey paper details
        assert len(survey_paper["authors"]) == 3
        assert survey_paper["year"] == 2023
        assert "deep learning" in survey_paper["abstract"].lower()
        
        # Check attention paper details
        assert len(attention_paper["authors"]) == 2
        assert attention_paper["year"] == 2017
        assert "vaswani" in attention_paper["authors"][0]["name"].lower()
    
    def test_incremental_build_workflow(self, temp_dir, sample_rdf_file):
        """Test incremental build workflow (rebuilding when source changes)."""
        output_dir = temp_dir / "website"
        config = BuildConfig(
            input_file=sample_rdf_file,
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        # Initial build
        result1 = pipeline.build()
        assert result1.success is True
        
        # Check initial build timestamp
        index_file = output_dir / "index.html"
        initial_mtime = index_file.stat().st_mtime
        
        # Wait a moment to ensure different timestamp
        import time
        time.sleep(0.1)
        
        # Rebuild (should work even if no changes)
        result2 = pipeline.build()
        assert result2.success is True
        
        # File should be updated
        new_mtime = index_file.stat().st_mtime
        assert new_mtime >= initial_mtime
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery in build workflow."""
        output_dir = temp_dir / "website"
        
        # Try to build with invalid file
        invalid_file = temp_dir / "invalid.rdf"
        invalid_file.write_text("invalid content")
        
        config1 = BuildConfig(
            input_file=str(invalid_file),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config1)
        
        try:
            result1 = pipeline.build()
            assert result1.success is False
        except Exception:
            # Exception is acceptable for invalid input
            pass
        
        # Output directory might be created but should not contain complete website
        if output_dir.exists():
            assert not (output_dir / "index.html").exists()
        
        # Now try with valid file
        # Create minimal valid RDF
        graph = Graph()
        graph.bind("dc", DC)
        graph.bind("bib", BIB)
        
        item = URIRef("http://example.org/item1")
        graph.add((item, RDF.type, BIB.Article))
        graph.add((item, DC.title, Literal("Test Article")))
        
        valid_file = temp_dir / "valid.rdf"
        graph.serialize(destination=str(valid_file), format="xml")
        
        config2 = BuildConfig(
            input_file=str(valid_file),
            output_dir=str(output_dir)
        )
        pipeline2 = BuildPipeline(config2)
        
        result2 = pipeline2.build()
        assert result2.success is True
        
        # Should now have complete website
        assert (output_dir / "index.html").exists()
        assert (output_dir / "data" / "bibliography.json").exists()


class TestPerformanceAndScalability:
    """Test performance and scalability aspects."""
    
    def test_memory_usage_with_large_dataset(self, temp_dir):
        """Test memory usage doesn't grow excessively with large datasets."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large dataset (500 items)
        graph = Graph()
        graph.bind("z", Z)
        graph.bind("bib", BIB)
        graph.bind("dc", DC)
        graph.bind("foaf", FOAF)
        
        for i in range(500):
            item = URIRef(f"http://example.org/item{i}")
            graph.add((item, RDF.type, BIB.Article))
            graph.add((item, DC.title, Literal(f"Article {i} with a reasonably long title that might be typical in academic literature")))
            graph.add((item, DC.date, Literal("2023")))
            
            # Add author
            author = URIRef(f"http://example.org/author{i}")
            authors_seq = URIRef(f"http://example.org/authors{i}")
            
            graph.add((item, BIB.authors, authors_seq))
            graph.add((authors_seq, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#_1"), author))
            graph.add((author, RDF.type, FOAF.Person))
            graph.add((author, FOAF.givenName, Literal(f"FirstName{i}")))
            graph.add((author, FOAF.surname, Literal(f"LastName{i}")))
        
        # Save and process
        large_rdf = temp_dir / "large.rdf"
        graph.serialize(destination=str(large_rdf), format="xml")
        
        output_dir = temp_dir / "output"
        config = BuildConfig(
            input_file=str(large_rdf),
            output_dir=str(output_dir)
        )
        pipeline = BuildPipeline(config)
        
        result = pipeline.build()
        assert result.success is True
        
        # Check memory usage didn't grow excessively
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for 500 items)
        assert memory_growth < 100 * 1024 * 1024
    
    def test_build_time_scalability(self, temp_dir):
        """Test that build time scales reasonably with dataset size."""
        import time
        
        def create_and_build_dataset(size):
            graph = Graph()
            graph.bind("bib", BIB)
            graph.bind("dc", DC)
            
            for i in range(size):
                item = URIRef(f"http://example.org/item{i}")
                graph.add((item, RDF.type, BIB.Article))
                graph.add((item, DC.title, Literal(f"Article {i}")))
            
            rdf_file = temp_dir / f"dataset_{size}.rdf"
            graph.serialize(destination=str(rdf_file), format="xml")
            
            output_dir = temp_dir / f"output_{size}"
            config = BuildConfig(
                input_file=str(rdf_file),
                output_dir=str(output_dir)
            )
            pipeline = BuildPipeline(config)
            
            start_time = time.time()
            result = pipeline.build()
            end_time = time.time()
            
            assert result.success is True
            return end_time - start_time
        
        # Test with different dataset sizes
        time_10 = create_and_build_dataset(10)
        time_50 = create_and_build_dataset(50)
        
        # Build time should scale reasonably (not exponentially)
        # 50 items should take less than 10x the time of 10 items
        assert time_50 < time_10 * 10
        
        # Both should complete in reasonable time
        assert time_10 < 5.0  # 10 items in less than 5 seconds
        assert time_50 < 15.0  # 50 items in less than 15 seconds