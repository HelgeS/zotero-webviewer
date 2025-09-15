"""RDF parsing functionality for Zotero exports."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from rdflib import Graph, Namespace, URIRef, Literal
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
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise RDFParsingError(f"RDF file not found: {file_path}")
                
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
            
            # Parse the RDF file
            self.graph.parse(file_path, format="xml")
            
            self.logger.info(f"Successfully parsed RDF file: {file_path}")
            self.logger.info(f"Graph contains {len(self.graph)} triples")
            
            return self.graph
            
        except Exception as e:
            raise RDFParsingError(f"Failed to parse RDF file {file_path}: {str(e)}")
    
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
            
            # Finally, look for any subjects that have bibliographic properties but weren't caught above
            # This catches rdf:Description elements that represent bibliography items
            bibliographic_properties = [DC.title, BIB.authors, DCTERMS.isPartOf]
            
            for prop in bibliographic_properties:
                for subject, _, _ in graph.triples((None, prop, None)):
                    if subject in processed_subjects:
                        continue
                        
                    # Skip attachments and memos
                    if (subject, RDF.type, Z.Attachment) in graph or \
                       (subject, RDF.type, BIB.Memo) in graph:
                        continue
                    
                    # Check if this looks like a bibliography item (has title)
                    if graph.value(subject, DC.title):
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
            # In Zotero RDF, collections are typically represented as subjects
            # that have dcterms:hasPart relationships with items
            collection_subjects = set()
            
            # Find subjects that have hasPart relationships (indicating collections)
            for subject, _, _ in graph.triples((None, DCTERMS.hasPart, None)):
                collection_subjects.add(subject)
            
            # Also look for subjects that are referenced by dcterms:isPartOf
            for _, _, collection_ref in graph.triples((None, DCTERMS.isPartOf, None)):
                if isinstance(collection_ref, URIRef):
                    collection_subjects.add(collection_ref)
            
            for collection_subject in collection_subjects:
                collection_data = self._extract_collection_data(graph, collection_subject)
                if collection_data:
                    collections.append(collection_data)
            
            self.logger.info(f"Extracted {len(collections)} collections")
            return collections
            
        except Exception as e:
            raise RDFParsingError(f"Failed to extract collections: {str(e)}")
    
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
            if not (attachment_node, RDF.type, Z.Attachment) in graph:
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