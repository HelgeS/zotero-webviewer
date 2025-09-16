"""Data transformation utilities for converting RDF to structured data."""

import re
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set
from enum import Enum


class ItemType(Enum):
    """Enumeration of bibliography item types."""
    ARTICLE = "article"
    BOOK = "book"
    CONFERENCE = "conference"
    THESIS = "thesis"
    REPORT = "report"
    WEBPAGE = "webpage"
    OTHER = "other"


@dataclass
class Author:
    """Data model for an author."""
    given_name: str = ""
    surname: str = ""
    full_name: str = ""
    
    def __post_init__(self):
        """Generate full name if not provided."""
        if not self.full_name and (self.given_name or self.surname):
            self.full_name = f"{self.given_name} {self.surname}".strip()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Attachment:
    """Data model for an attachment."""
    id: str
    title: str = ""
    type: str = ""
    url: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BibliographyItem:
    """Data model for a bibliography item."""
    id: str
    type: ItemType = ItemType.OTHER
    title: str = ""
    authors: List[Author] = field(default_factory=list)
    year: Optional[int] = None
    venue: str = ""
    abstract: str = ""
    doi: str = ""
    url: str = ""
    keywords: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)
    attachments: List[Attachment] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = asdict(self)
        data["type"] = self.type.value
        data["authors"] = [author.to_dict() for author in self.authors]
        data["attachments"] = [attachment.to_dict() for attachment in self.attachments]
        return data
    
    def get_author_names(self) -> List[str]:
        """Get list of author full names."""
        return [author.full_name for author in self.authors if author.full_name]
    
    def get_primary_author(self) -> Optional[str]:
        """Get the first author's name."""
        if self.authors:
            return self.authors[0].full_name
        return None


@dataclass
class Collection:
    """Data model for a collection."""
    id: str
    title: str = ""
    parent_id: Optional[str] = None
    children: List['Collection'] = field(default_factory=list)
    item_ids: List[str] = field(default_factory=list)
    item_count: int = 0
    
    def __post_init__(self):
        """Calculate item count including children."""
        self.item_count = len(self.item_ids)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = asdict(self)
        data["children"] = [child.to_dict() for child in self.children]
        return data
    
    def add_child(self, child: 'Collection'):
        """Add a child collection."""
        child.parent_id = self.id
        self.children.append(child)
    
    def get_all_item_ids(self) -> Set[str]:
        """Get all item IDs including from child collections."""
        all_ids = set(self.item_ids)
        for child in self.children:
            all_ids.update(child.get_all_item_ids())
        return all_ids
    
    def update_item_count(self):
        """Update item count including children recursively."""
        self.item_count = len(self.get_all_item_ids())
        for child in self.children:
            child.update_item_count()


class DataTransformationError(Exception):
    """Exception raised when data transformation fails."""
    pass


class DataValidationError(DataTransformationError):
    """Exception raised when data validation fails."""
    pass


class DataIntegrityError(DataTransformationError):
    """Exception raised when data integrity checks fail."""
    pass


class DataTransformer:
    """Transforms raw RDF data into structured models."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def transform_bibliography_item(self, item_data: Dict[str, Any]) -> BibliographyItem:
        """
        Transform raw item data into a BibliographyItem model.
        
        Args:
            item_data: Raw item data dictionary from RDF parser
            
        Returns:
            BibliographyItem instance
            
        Raises:
            DataTransformationError: If transformation fails
            DataValidationError: If required data is missing or invalid
        """
        try:
            # Validate required fields
            if not item_data.get("id"):
                raise DataValidationError("Bibliography item missing required 'id' field")
            
            item_id = item_data["id"]
            
            # Validate and clean title (required field)
            title = self._clean_text(item_data.get("title", ""))
            if not title:
                # Try to generate a title from available data
                title = self._generate_fallback_title(item_data)
                if not title:
                    raise DataValidationError(f"Bibliography item {item_id} has no title and cannot generate fallback")
                self.logger.warning(f"Generated fallback title for item {item_id}: {title}")
            
            # Normalize item type with validation
            item_type = self._normalize_item_type(item_data.get("type", "other"))
            
            # Transform authors with validation
            authors = []
            author_errors = []
            for i, author_data in enumerate(item_data.get("authors", [])):
                try:
                    author = self._transform_author(author_data)
                    if author:
                        authors.append(author)
                    else:
                        author_errors.append(f"Author {i} could not be processed")
                except Exception as e:
                    author_errors.append(f"Author {i} transformation failed: {str(e)}")
            
            if author_errors:
                self.logger.warning(f"Item {item_id} author issues: {'; '.join(author_errors)}")
            
            # Transform attachments with error handling
            attachments = []
            attachment_errors = []
            for i, attachment_data in enumerate(item_data.get("attachments", [])):
                try:
                    attachment = self._transform_attachment(attachment_data)
                    if attachment:
                        attachments.append(attachment)
                except Exception as e:
                    attachment_errors.append(f"Attachment {i} transformation failed: {str(e)}")
            
            if attachment_errors:
                self.logger.warning(f"Item {item_id} attachment issues: {'; '.join(attachment_errors)}")
            
            # Clean and normalize text fields
            venue = self._clean_text(item_data.get("venue", ""))
            abstract = self._clean_text(item_data.get("abstract", ""))
            
            # Validate and normalize year
            year = self._validate_year(item_data.get("year"), item_id)
            
            # Extract keywords from abstract and title if not provided
            keywords = item_data.get("keywords", [])
            if not keywords:
                keywords = self._extract_keywords(title, abstract)
            
            # Validate URLs
            doi = self._validate_and_clean_url(item_data.get("doi", ""), "DOI", item_id)
            url = self._validate_and_clean_url(item_data.get("url", ""), "URL", item_id)
            
            return BibliographyItem(
                id=item_id,
                type=item_type,
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                abstract=abstract,
                doi=doi,
                url=url,
                keywords=keywords,
                collections=item_data.get("collections", []),
                attachments=attachments
            )
            
        except (DataTransformationError, DataValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            item_id = item_data.get("id", "unknown")
            raise DataTransformationError(f"Failed to transform bibliography item {item_id}: {str(e)}")
    
    def transform_collection(self, collection_data: Dict[str, Any]) -> Collection:
        """
        Transform raw collection data into a Collection model.
        
        Args:
            collection_data: Raw collection data dictionary from RDF parser
            
        Returns:
            Collection instance
            
        Raises:
            DataTransformationError: If transformation fails
        """
        try:
            title = self._clean_text(collection_data.get("title", ""))
            
            return Collection(
                id=collection_data["id"],
                title=title,
                parent_id=collection_data.get("parent_id"),
                item_ids=collection_data.get("item_ids", [])
            )
            
        except Exception as e:
            raise DataTransformationError(f"Failed to transform collection: {str(e)}")
    
    def normalize_authors(self, authors_data: List[Dict[str, str]]) -> List[Author]:
        """
        Normalize and clean author data.
        
        Args:
            authors_data: List of raw author dictionaries
            
        Returns:
            List of Author instances
        """
        normalized_authors = []
        
        for author_data in authors_data:
            author = self._transform_author(author_data)
            if author:
                normalized_authors.append(author)
        
        return normalized_authors
    
    def _transform_author(self, author_data: Dict[str, str]) -> Optional[Author]:
        """Transform raw author data into Author model."""
        try:
            given_name = self._clean_name(author_data.get("given_name", ""))
            surname = self._clean_name(author_data.get("surname", ""))
            full_name = author_data.get("full_name", "")
            
            # If no full name provided, construct it
            if not full_name:
                full_name = f"{given_name} {surname}".strip()
            else:
                full_name = self._clean_name(full_name)
            
            # Parse full name if individual parts are missing
            if full_name and (not given_name or not surname):
                parsed_given, parsed_surname = self._parse_author_name(full_name)
                if not given_name:
                    given_name = parsed_given
                if not surname:
                    surname = parsed_surname
            
            # Only create author if we have at least some name information
            if given_name or surname or full_name:
                return Author(
                    given_name=given_name,
                    surname=surname,
                    full_name=full_name
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to transform author data: {str(e)}")
            return None
    
    def _transform_attachment(self, attachment_data: Dict[str, str]) -> Optional[Attachment]:
        """Transform raw attachment data into Attachment model."""
        try:
            return Attachment(
                id=attachment_data["id"],
                title=self._clean_text(attachment_data.get("title", "")),
                type=attachment_data.get("type", ""),
                url=self._clean_url(attachment_data.get("url", ""))
            )
        except Exception as e:
            self.logger.warning(f"Failed to transform attachment data: {str(e)}")
            return None
    
    def _normalize_item_type(self, item_type: str) -> ItemType:
        """Normalize item type string to ItemType enum."""
        type_mapping = {
            "article": ItemType.ARTICLE,
            "journalarticle": ItemType.ARTICLE,
            "book": ItemType.BOOK,
            "booksection": ItemType.BOOK,
            "conference": ItemType.CONFERENCE,
            "conferencepaper": ItemType.CONFERENCE,
            "thesis": ItemType.THESIS,
            "report": ItemType.REPORT,
            "webpage": ItemType.WEBPAGE,
            "other": ItemType.OTHER
        }
        
        normalized = item_type.lower().replace("_", "").replace("-", "")
        return type_mapping.get(normalized, ItemType.OTHER)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text.strip()
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize name strings."""
        if not name:
            return ""
        
        # Basic cleaning
        name = self._clean_text(name)
        
        # Remove common prefixes/suffixes
        prefixes = ['Dr.', 'Prof.', 'Mr.', 'Ms.', 'Mrs.']
        suffixes = ['Jr.', 'Sr.', 'PhD', 'Ph.D.', 'M.D.', 'MD']
        
        for prefix in prefixes:
            if name.startswith(prefix + ' '):
                name = name[len(prefix):].strip()
        
        for suffix in suffixes:
            if name.endswith(' ' + suffix):
                name = name[:-len(suffix)].strip()
        
        return name
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL strings."""
        if not url:
            return ""
        
        url = url.strip()
        
        # Basic URL validation
        if url and not (url.startswith('http://') or url.startswith('https://')):
            # If it looks like a DOI, add the DOI URL prefix
            if url.startswith('10.') and '/' in url:
                url = f"https://doi.org/{url}"
            elif not url.startswith('www.'):
                # Don't modify other formats
                pass
        
        return url
    
    def _parse_author_name(self, full_name: str) -> tuple[str, str]:
        """
        Parse a full name into given name and surname.
        
        Args:
            full_name: Full author name
            
        Returns:
            Tuple of (given_name, surname)
        """
        if not full_name:
            return "", ""
        
        # Handle common name formats
        parts = full_name.strip().split()
        
        if len(parts) == 1:
            # Only one name part - assume it's the surname
            return "", parts[0]
        elif len(parts) == 2:
            # Two parts - assume given name, surname
            return parts[0], parts[1]
        else:
            # Multiple parts - assume first part is given name, rest is surname
            return parts[0], " ".join(parts[1:])
    
    def _extract_keywords(self, title: str, abstract: str) -> List[str]:
        """
        Extract potential keywords from title and abstract.
        
        Args:
            title: Item title
            abstract: Item abstract
            
        Returns:
            List of extracted keywords
        """
        keywords = []
        
        # This is a simple implementation - could be enhanced with NLP
        text = f"{title} {abstract}".lower()
        
        # Common academic keywords to look for
        common_keywords = [
            'machine learning', 'artificial intelligence', 'deep learning',
            'neural network', 'algorithm', 'optimization', 'classification',
            'regression', 'clustering', 'natural language processing',
            'computer vision', 'data mining', 'big data', 'statistics'
        ]
        
        for keyword in common_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _generate_fallback_title(self, item_data: Dict[str, Any]) -> str:
        """
        Generate a fallback title when the original title is missing or empty.
        
        Args:
            item_data: Raw item data dictionary
            
        Returns:
            Generated fallback title or empty string if cannot generate
        """
        # Try to construct title from available data
        authors = item_data.get("authors", [])
        year = item_data.get("year")
        venue = item_data.get("venue", "")
        item_type = item_data.get("type", "item")
        
        title_parts = []
        
        # Add first author if available
        if authors and len(authors) > 0:
            first_author = authors[0]
            author_name = first_author.get("surname") or first_author.get("full_name", "")
            if author_name:
                if len(authors) > 1:
                    title_parts.append(f"{author_name} et al.")
                else:
                    title_parts.append(author_name)
        
        # Add year if available
        if year:
            title_parts.append(f"({year})")
        
        # Add venue or type
        if venue:
            title_parts.append(f"in {venue}")
        else:
            title_parts.append(f"[{item_type}]")
        
        if title_parts:
            return " ".join(title_parts)
        
        # Last resort: use item ID
        return f"Untitled item {item_data.get('id', 'unknown')}"
    
    def _validate_year(self, year: Any, item_id: str) -> Optional[int]:
        """
        Validate and normalize publication year.
        
        Args:
            year: Year value from item data
            item_id: Item ID for error reporting
            
        Returns:
            Validated year as integer or None if invalid
        """
        if year is None:
            return None
        
        try:
            # Convert to integer if it's a string
            if isinstance(year, str):
                year = int(year.strip())
            
            if not isinstance(year, int):
                self.logger.warning(f"Item {item_id} has non-numeric year: {year}")
                return None
            
            # Validate reasonable year range
            current_year = 2025  # Could be made dynamic
            if year < 1000:
                self.logger.warning(f"Item {item_id} has year too early: {year}")
                return None
            elif year > current_year + 5:  # Allow some future dates
                self.logger.warning(f"Item {item_id} has year too far in future: {year}")
                return None
            
            return year
            
        except (ValueError, TypeError):
            self.logger.warning(f"Item {item_id} has invalid year format: {year}")
            return None
    
    def _validate_and_clean_url(self, url: str, url_type: str, item_id: str) -> str:
        """
        Validate and clean URL strings with enhanced error handling.
        
        Args:
            url: URL string to validate
            url_type: Type of URL (for error reporting)
            item_id: Item ID for error reporting
            
        Returns:
            Cleaned and validated URL or empty string if invalid
        """
        if not url:
            return ""
        
        url = url.strip()
        
        try:
            # Basic URL validation
            if url and not (url.startswith('http://') or url.startswith('https://')):
                # If it looks like a DOI, add the DOI URL prefix
                if url.startswith('10.') and '/' in url:
                    url = f"https://doi.org/{url}"
                elif url_type == "DOI" and not url.startswith('doi:'):
                    # Handle bare DOI
                    if '/' in url and '.' in url:
                        url = f"https://doi.org/{url}"
                    else:
                        self.logger.warning(f"Item {item_id} has invalid {url_type} format: {url}")
                        return ""
                elif not url.startswith('www.') and not url.startswith('ftp://'):
                    # Don't modify other formats, but warn about potentially invalid URLs
                    if '.' not in url:
                        self.logger.warning(f"Item {item_id} has potentially invalid {url_type}: {url}")
                        return ""
            
            # Check for common URL issues
            if len(url) > 2000:  # Very long URLs might be malformed
                self.logger.warning(f"Item {item_id} has very long {url_type} (truncated): {url[:100]}...")
                return url[:2000]
            
            # Check for suspicious characters
            if any(char in url for char in [' ', '\n', '\r', '\t']):
                self.logger.warning(f"Item {item_id} has {url_type} with whitespace characters")
                url = re.sub(r'\s+', '', url)  # Remove whitespace
            
            return url
            
        except Exception as e:
            self.logger.warning(f"Item {item_id} {url_type} validation failed: {str(e)}")
            return ""
    
    def validate_transformed_data(self, items: List[BibliographyItem], collections: List[Collection]) -> List[str]:
        """
        Validate transformed data for consistency and integrity.
        
        Args:
            items: List of transformed bibliography items
            collections: List of transformed collections
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        if not items:
            issues.append("No bibliography items after transformation")
            return issues
        
        # Validate items
        item_ids = set()
        duplicate_titles = {}
        
        for item in items:
            # Check for duplicate IDs
            if item.id in item_ids:
                issues.append(f"Duplicate item ID: {item.id}")
            item_ids.add(item.id)
            
            # Check for potential duplicate titles
            title_key = item.title.lower().strip()
            if title_key in duplicate_titles:
                duplicate_titles[title_key].append(item.id)
            else:
                duplicate_titles[title_key] = [item.id]
            
            # Validate item data
            if not item.title:
                issues.append(f"Item {item.id} has empty title")
            
            if not item.authors:
                # This is a warning, not an error
                pass
            
            if item.year and (item.year < 1000 or item.year > 2030):
                issues.append(f"Item {item.id} has suspicious year: {item.year}")
        
        # Report potential duplicates
        for title, ids in duplicate_titles.items():
            if len(ids) > 1:
                issues.append(f"Potential duplicate titles: {title} (items: {', '.join(ids)})")
        
        # Validate collections
        if collections:
            collection_ids = set()
            for collection in collections:
                if collection.id in collection_ids:
                    issues.append(f"Duplicate collection ID: {collection.id}")
                collection_ids.add(collection.id)
                
                if not collection.title:
                    issues.append(f"Collection {collection.id} has empty title")
        
        # Cross-validate collection references
        for item in items:
            for collection_id in item.collections:
                if collection_id not in collection_ids:
                    issues.append(f"Item {item.id} references non-existent collection: {collection_id}")
        
        return issues