"""RDF parsing functionality for Zotero exports."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, DC, DCTERMS, FOAF


# Define Zotero-specific namespaces
Z = Namespace("http://www.zotero.org/namespaces/export#")
BIB = Namespace("http://purl.org/net/biblio#")
LINK = Namespace("http://purl.org/rss/1.0/modules/link/")
VCARD = Namespace("http://nwalsh.com/rdf/vCard#")
PRISM = Namespace("http://prismstandard.org/namespaces/1.2/basic/")


class RDFParsingError(Exception):
    """Exception raised when RDF parsing fails."""
    pass


class RDFValidationError(RDFParsingError):
    """Exception raised when RDF validation fails."""
    pass


class RDFDataIntegrityError(RDFParsingError):
    """Exception raised when RDF data integrity checks fail."""
    pass


class RDFParser:
    """Parser for Zotero RDF exports."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.graph = None
        
    def parse_rdf_file(self, file_path: str) -> Graph:
        """
        Parse an RDF file and return the RDF graph.
        
        Args:
            file_path: Path to the RDF file
            
        Returns:
            RDF graph object
            
        Raises:
            RDFParsingError: If the file cannot be parsed
            RDFValidationError: If the file format is invalid
        """
        try:
            file_path = Path(file_path)
            
            # Validate file existence and accessibility
            if not file_path.exists():
                raise RDFParsingError(f"RDF file not found: {file_path}")
            
            if not file_path.is_file():
                raise RDFParsingError(f"Path is not a file: {file_path}")
            
            # Check file size (warn about very large files)
            file_size = file_path.stat().st_size
            if file_size == 0:
                raise RDFValidationError(f"RDF file is empty: {file_path}")
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                self.logger.warning(f"Large RDF file detected ({file_size / 1024 / 1024:.1f}MB): {file_path}")
            
            # Check file permissions
            if not file_path.stat().st_mode & 0o444:  # Check read permission
                raise RDFParsingError(f"No read permission for RDF file: {file_path}")
                
            self.graph = Graph()
            
            # Bind namespaces for cleaner queries
            self.graph.bind("z", Z)
            self.graph.bind("bib", BIB)
            self.graph.bind("dc", DC)
            self.graph.bind("dcterms", DCTERMS)
            self.graph.bind("foaf", FOAF)
            self.graph.bind("link", LINK)
            self.graph.bind("vcard", VCARD)
            self.graph.bind("prism", PRISM)
            
            # Parse the RDF file with enhanced error handling
            try:
                self.graph.parse(file_path, format="xml")
            except Exception as parse_error:
                # Try to provide more specific error information
                error_msg = str(parse_error).lower()
                if "xml" in error_msg and ("malformed" in error_msg or "syntax" in error_msg):
                    raise RDFValidationError(f"Malformed XML in RDF file {file_path}: {str(parse_error)}")
                elif "encoding" in error_msg:
                    raise RDFValidationError(f"Encoding error in RDF file {file_path}: {str(parse_error)}")
                elif "namespace" in error_msg:
                    raise RDFValidationError(f"Namespace error in RDF file {file_path}: {str(parse_error)}")
                else:
                    raise RDFParsingError(f"Failed to parse RDF file {file_path}: {str(parse_error)}")
            
            # Validate the parsed graph
            self._validate_parsed_graph(file_path)
            
            self.logger.info(f"Successfully parsed RDF file: {file_path}")
            self.logger.info(f"Graph contains {len(self.graph)} triples")
            
            return self.graph
            
        except (RDFParsingError, RDFValidationError):
            # Re-raise our custom exceptions
            raise
        except PermissionError as e:
            raise RDFParsingError(f"Permission denied accessing RDF file {file_path}: {str(e)}")
        except FileNotFoundError as e:
            raise RDFParsingError(f"RDF file not found {file_path}: {str(e)}")
        except Exception as e:
            raise RDFParsingError(f"Unexpected error parsing RDF file {file_path}: {str(e)}")
    
    def extract_bibliography_items(self, graph: Optional[Graph] = None) -> List[Dict[str, Any]]:
        """
        Extract bibliography items from the RDF graph.
        
        Args:
            graph: RDF graph to extract from (uses instance graph if None)
            
        Returns:
            List of dictionaries containing bibliography item data
            
        Raises:
            RDFParsingError: If extraction fails
        """
        if graph is None:
            graph = self.graph
            
        if graph is None:
            raise RDFParsingError("No RDF graph available. Call parse_rdf_file first.")
            
        items = []
        
        try:
            # Query for different types of bibliography items
            item_types = [
                (BIB.Article, "article"),
                (BIB.Book, "book"),
                (BIB.ConferencePaper, "conference"),
                (BIB.Thesis, "thesis")
            ]
            
            processed_subjects = set()
            
            # First, find items by explicit RDF types
            for rdf_type, item_type in item_types:
                for subject in graph.subjects(RDF.type, rdf_type):
                    if subject in processed_subjects:
                        continue
                        
                    # Skip attachments and memos
                    if (subject, RDF.type, Z.Attachment) in graph or \
                       (subject, RDF.type, BIB.Memo) in graph:
                        continue
                        
                    item_data = self._extract_item_data(graph, subject, item_type)
                    if item_data:
                        items.append(item_data)
                        processed_subjects.add(subject)
            
            # Also check for items with z:itemType but no explicit RDF.type
            for subject, _, item_type_literal in graph.triples((None, Z.itemType, None)):
                if subject in processed_subjects:
                    continue
                    
                # Skip attachments
                if str(item_type_literal) == "attachment":
                    continue
                    
                item_data = self._extract_item_data(graph, subject, str(item_type_literal))
                if item_data:
                    items.append(item_data)
                    processed_subjects.add(subject)
            
            # Finally, look for subjects that have bibliographic properties but weren't caught above
            # This catches rdf:Description elements that represent bibliography items
            # BUT we need to be more selective to avoid collections and venue entities
            for subject, _, _ in graph.triples((None, BIB.authors, None)):
                if subject in processed_subjects:
                    continue
                    
                # Skip attachments, memos, collections, and venue entities
                if (subject, RDF.type, Z.Attachment) in graph or \
                   (subject, RDF.type, BIB.Memo) in graph or \
                   (subject, RDF.type, Z.Collection) in graph or \
                   (subject, RDF.type, BIB.Journal) in graph or \
                   (subject, RDF.type, BIB.Proceedings) in graph:
                    continue
                
                # Only include if it has authors (strong indicator of bibliography item)
                # and has a title
                if graph.value(subject, BIB.authors) and graph.value(subject, DC.title):
                    item_data = self._extract_item_data(graph, subject, "other")
                    if item_data:
                        items.append(item_data)
                        processed_subjects.add(subject)
            
            self.logger.info(f"Extracted {len(items)} bibliography items")
            return items
            
        except Exception as e:
            raise RDFParsingError(f"Failed to extract bibliography items: {str(e)}")
    
    def extract_collections(self, graph: Optional[Graph] = None) -> List[Dict[str, Any]]:
        """
        Extract collection information from the RDF graph.
        
        Args:
            graph: RDF graph to extract from (uses instance graph if None)
            
        Returns:
            List of dictionaries containing collection data
            
        Raises:
            RDFParsingError: If extraction fails
        """
        if graph is None:
            graph = self.graph
            
        if graph is None:
            raise RDFParsingError("No RDF graph available. Call parse_rdf_file first.")
            
        collections = []
        
        try:
            # In Zotero RDF, collections are specifically marked with z:Collection type
            # This distinguishes them from venues (bib:Journal) and other entities
            for subject in graph.subjects(RDF.type, Z.Collection):
                collection_data = self._extract_collection_data(graph, subject)
                if collection_data:
                    collections.append(collection_data)
            
            self.logger.info(f"Extracted {len(collections)} collections")
            return collections
            
        except Exception as e:
            raise RDFParsingError(f"Failed to extract collections: {str(e)}")
    
    def assign_items_to_collections(
        self, 
        items_data: List[Dict[str, Any]], 
        collections_data: List[Dict[str, Any]]
    ) -> None:
        """
        Assign collection references to bibliography items based on collection data.
        
        Args:
            items_data: List of item dictionaries to update
            collections_data: List of collection dictionaries with item_ids
        """
        try:
            # Create a mapping from item ID to item data for quick lookup
            items_by_id = {item["id"]: item for item in items_data}
            
            # For each collection, add the collection ID to its items
            for collection in collections_data:
                collection_id = collection["id"]
                for item_id in collection.get("item_ids", []):
                    if item_id in items_by_id:
                        # Initialize collections list if it doesn't exist
                        if "collections" not in items_by_id[item_id]:
                            items_by_id[item_id]["collections"] = []
                        
                        # Add collection ID if not already present
                        if collection_id not in items_by_id[item_id]["collections"]:
                            items_by_id[item_id]["collections"].append(collection_id)
            
            # Count assignments for logging
            assigned_count = sum(1 for item in items_data if item.get("collections"))
            self.logger.info(f"Assigned collection references to {assigned_count} items")
            
        except Exception as e:
            self.logger.error(f"Failed to assign items to collections: {str(e)}")
    
    def _extract_item_data(self, graph: Graph, subject: URIRef, item_type: str) -> Optional[Dict[str, Any]]:
        """Extract data for a single bibliography item."""
        try:
            item_data = {
                "id": str(subject),
                "type": self._normalize_item_type(item_type),
                "title": "",
                "authors": [],
                "year": None,
                "venue": "",
                "abstract": "",
                "doi": "",
                "url": "",
                "keywords": [],
                "collections": [],
                "attachments": []
            }
            
            # Extract title
            title = graph.value(subject, DC.title)
            if title:
                item_data["title"] = str(title)
            
            # Extract authors
            authors_seq = graph.value(subject, BIB.authors)
            if authors_seq:
                item_data["authors"] = self._extract_authors(graph, authors_seq)
            
            # Extract publication year from date
            date = graph.value(subject, DC.date)
            if date:
                item_data["year"] = self._extract_year_from_date(str(date))
            
            # Extract venue/journal information
            venue = self._extract_venue(graph, subject)
            if venue:
                item_data["venue"] = venue
            
            # Extract abstract
            abstract = graph.value(subject, DCTERMS.abstract)
            if abstract:
                item_data["abstract"] = str(abstract)
            
            # Extract DOI and URL
            for identifier in graph.objects(subject, DC.identifier):
                if isinstance(identifier, URIRef):
                    url_str = str(identifier)
                    if "doi.org" in url_str:
                        item_data["doi"] = url_str
                    else:
                        item_data["url"] = url_str
                elif hasattr(identifier, 'value'):
                    # Handle dcterms:URI objects
                    uri_value = graph.value(identifier, RDF.value)
                    if uri_value:
                        url_str = str(uri_value)
                        if "doi.org" in url_str:
                            item_data["doi"] = url_str
                        else:
                            item_data["url"] = url_str
            
            # Extract attachments
            for attachment in graph.objects(subject, LINK.link):
                attachment_data = self._extract_attachment_data(graph, attachment)
                if attachment_data:
                    item_data["attachments"].append(attachment_data)
            
            # Only return items with at least a title
            if item_data["title"]:
                return item_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract data for item {subject}: {str(e)}")
            return None
    
    def _extract_collection_data(self, graph: Graph, subject: URIRef) -> Optional[Dict[str, Any]]:
        """Extract data for a single collection."""
        try:
            collection_data = {
                "id": str(subject),
                "title": "",
                "parent_id": None,
                "item_ids": []
            }
            
            # Extract title
            title = graph.value(subject, DC.title)
            if title:
                collection_data["title"] = str(title)
            
            # Extract items that belong to this collection
            for item in graph.objects(subject, DCTERMS.hasPart):
                collection_data["item_ids"].append(str(item))
            
            # Only return collections with a title
            if collection_data["title"]:
                return collection_data
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract collection data for {subject}: {str(e)}")
            return None
    
    def _extract_authors(self, graph: Graph, authors_seq: URIRef) -> List[Dict[str, str]]:
        """Extract author information from an RDF sequence."""
        authors = []
        
        try:
            # RDF sequences use rdf:_1, rdf:_2, etc.
            seq_index = 1
            while True:
                # Create the sequence property URI
                seq_prop = URIRef(f"http://www.w3.org/1999/02/22-rdf-syntax-ns#_{seq_index}")
                author_node = graph.value(authors_seq, seq_prop)
                
                if not author_node:
                    break
                
                # Check if this is a foaf:Person and extract data
                if (author_node, RDF.type, FOAF.Person) in graph:
                    author_data = self._extract_author_data(graph, author_node)
                    if author_data:
                        authors.append(author_data)
                
                seq_index += 1
            
            # If no numbered sequence found, try alternative approaches
            if not authors:
                # Look for any objects of the sequence that are persons
                for _, _, obj in graph.triples((authors_seq, None, None)):
                    if isinstance(obj, URIRef) and (obj, RDF.type, FOAF.Person) in graph:
                        author_data = self._extract_author_data(graph, obj)
                        if author_data:
                            authors.append(author_data)
        
        except Exception as e:
            self.logger.warning(f"Failed to extract authors: {str(e)}")
        
        return authors
    
    def _extract_author_data(self, graph: Graph, author_node: URIRef) -> Optional[Dict[str, str]]:
        """Extract data for a single author."""
        try:
            given_name = graph.value(author_node, FOAF.givenName)
            surname = graph.value(author_node, FOAF.surname)
            
            if given_name or surname:
                given_str = str(given_name) if given_name else ""
                surname_str = str(surname) if surname else ""
                
                # Create full name
                full_name = f"{given_str} {surname_str}".strip()
                
                return {
                    "given_name": given_str,
                    "surname": surname_str,
                    "full_name": full_name
                }
        
        except Exception as e:
            self.logger.warning(f"Failed to extract author data: {str(e)}")
        
        return None
    
    def _extract_venue(self, graph: Graph, subject: URIRef) -> str:
        """Extract venue/journal information."""
        venue = ""
        
        try:
            # Check for dcterms:isPartOf relationship
            part_of = graph.value(subject, DCTERMS.isPartOf)
            if part_of:
                # Get the title of the journal/venue
                venue_title = graph.value(part_of, DC.title)
                if venue_title:
                    venue = str(venue_title)
            
            # Also check for publisher information
            if not venue:
                publisher = graph.value(subject, DC.publisher)
                if publisher:
                    publisher_name = graph.value(publisher, FOAF.name)
                    if publisher_name:
                        venue = str(publisher_name)
        
        except Exception as e:
            self.logger.warning(f"Failed to extract venue: {str(e)}")
        
        return venue
    
    def _extract_attachment_data(self, graph: Graph, attachment_node: URIRef) -> Optional[Dict[str, str]]:
        """Extract attachment information."""
        try:
            # Check if this is actually an attachment
            if (attachment_node, RDF.type, Z.Attachment) not in graph:
                return None
            
            attachment_data = {
                "id": str(attachment_node),
                "title": "",
                "type": "",
                "url": ""
            }
            
            # Extract title
            title = graph.value(attachment_node, DC.title)
            if title:
                attachment_data["title"] = str(title)
            
            # Extract MIME type
            mime_type = graph.value(attachment_node, LINK.type)
            if mime_type:
                attachment_data["type"] = str(mime_type)
            
            # Extract URL if available
            for identifier in graph.objects(attachment_node, DC.identifier):
                if hasattr(identifier, 'value'):
                    uri_value = graph.value(identifier, RDF.value)
                    if uri_value:
                        attachment_data["url"] = str(uri_value)
                        break
            
            return attachment_data if attachment_data["title"] else None
        
        except Exception as e:
            self.logger.warning(f"Failed to extract attachment data: {str(e)}")
            return None
    
    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from a date string."""
        try:
            # Handle various date formats
            if len(date_str) >= 4 and date_str[:4].isdigit():
                return int(date_str[:4])
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _normalize_item_type(self, item_type: str) -> str:
        """Normalize item type to standard values."""
        type_mapping = {
            "journalArticle": "article",
            "conferencePaper": "conference",
            "book": "book",
            "bookSection": "book",
            "thesis": "thesis",
            "report": "report",
            "webpage": "webpage"
        }
        
        return type_mapping.get(item_type, "other")
    
    def _validate_parsed_graph(self, file_path: Path) -> None:
        """
        Validate the parsed RDF graph for basic integrity.
        
        Args:
            file_path: Path to the RDF file being validated
            
        Raises:
            RDFValidationError: If validation fails
            RDFDataIntegrityError: If data integrity issues are found
        """
        if not self.graph:
            raise RDFValidationError("No graph data after parsing")
        
        if len(self.graph) == 0:
            raise RDFValidationError(f"RDF file contains no triples: {file_path}")
        
        # Check for minimum expected content
        has_bibliography_items = False
        has_zotero_namespaces = False
        
        # Look for bibliography-related triples
        for s, p, o in self.graph:
            predicate_str = str(p)
            if str(BIB) in predicate_str or str(Z) in predicate_str or str(DC) in predicate_str:
                has_zotero_namespaces = True
            
            # Check for bibliography item indicators
            if (s, RDF.type, BIB.Article) in self.graph or \
               (s, RDF.type, BIB.Book) in self.graph or \
               any(self.graph.triples((None, BIB.authors, None))) or \
               any(self.graph.triples((None, DC.title, None))):
                has_bibliography_items = True
                break
        
        if not has_zotero_namespaces:
            self.logger.warning(f"RDF file may not be a Zotero export (no Zotero namespaces found): {file_path}")
        
        if not has_bibliography_items:
            raise RDFDataIntegrityError(f"No bibliography items found in RDF file: {file_path}")
        
        self.logger.debug(f"RDF validation passed for {file_path}")
    
    def validate_bibliography_data_integrity(self, items_data: List[Dict[str, Any]]) -> List[str]:
        """
        Validate bibliography data for required fields and data integrity.
        
        Args:
            items_data: List of extracted bibliography item dictionaries
            
        Returns:
            List of validation warnings/errors
        """
        validation_issues = []
        
        if not items_data:
            validation_issues.append("No bibliography items found")
            return validation_issues
        
        required_fields = ["id", "title"]
        recommended_fields = ["authors", "year", "type"]
        
        items_without_title = 0
        items_without_authors = 0
        items_without_year = 0
        items_with_invalid_year = 0
        duplicate_ids = set()
        seen_ids = set()
        
        for i, item in enumerate(items_data):
            item_id = item.get("id", f"item_{i}")
            
            # Check for duplicate IDs
            if item_id in seen_ids:
                duplicate_ids.add(item_id)
            seen_ids.add(item_id)
            
            # Check required fields
            for field in required_fields:
                if not item.get(field):
                    if field == "title":
                        items_without_title += 1
                    validation_issues.append(f"Item {item_id} missing required field: {field}")
            
            # Check recommended fields
            if not item.get("authors"):
                items_without_authors += 1
            
            if not item.get("year"):
                items_without_year += 1
            elif item.get("year"):
                year = item["year"]
                if not isinstance(year, int) or year < 1000 or year > 2100:
                    items_with_invalid_year += 1
                    validation_issues.append(f"Item {item_id} has invalid year: {year}")
            
            # Validate author data structure
            authors = item.get("authors", [])
            if authors and not isinstance(authors, list):
                validation_issues.append(f"Item {item_id} has invalid authors data structure")
            else:
                for j, author in enumerate(authors):
                    if not isinstance(author, dict):
                        validation_issues.append(f"Item {item_id} author {j} is not a dictionary")
                    elif not author.get("full_name") and not (author.get("given_name") or author.get("surname")):
                        validation_issues.append(f"Item {item_id} author {j} has no name information")
        
        # Summary statistics
        total_items = len(items_data)
        
        if duplicate_ids:
            validation_issues.append(f"Found {len(duplicate_ids)} duplicate item IDs")
        
        if items_without_title > 0:
            validation_issues.append(f"{items_without_title}/{total_items} items missing titles")
        
        if items_without_authors > total_items * 0.1:  # More than 10% missing authors
            validation_issues.append(f"{items_without_authors}/{total_items} items missing authors (>{items_without_authors/total_items*100:.1f}%)")
        
        if items_without_year > total_items * 0.2:  # More than 20% missing years
            validation_issues.append(f"{items_without_year}/{total_items} items missing publication year (>{items_without_year/total_items*100:.1f}%)")
        
        if items_with_invalid_year > 0:
            validation_issues.append(f"{items_with_invalid_year}/{total_items} items have invalid years")
        
        return validation_issues