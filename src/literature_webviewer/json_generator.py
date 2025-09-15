"""JSON data generation for static website deployment."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .data_transformer import BibliographyItem, Collection


class JSONGenerationError(Exception):
    """Exception raised when JSON generation fails."""
    pass


class JSONGenerator:
    """Generates optimized JSON files for client-side loading and filtering."""
    
    def __init__(self, output_dir: str = "output/data"):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_bibliography_json(
        self, 
        items: List[BibliographyItem], 
        filename: str = "bibliography.json"
    ) -> str:
        """
        Generate JSON file containing bibliography items data.
        
        Args:
            items: List of BibliographyItem objects
            filename: Output filename for the JSON file
            
        Returns:
            Path to the generated JSON file
            
        Raises:
            JSONGenerationError: If JSON generation fails
        """
        try:
            self.logger.info(f"Generating bibliography JSON for {len(items)} items")
            
            # Convert items to optimized dictionary format
            items_data = []
            for item in items:
                item_dict = item.to_dict()
                
                # Optimize the data structure for client-side use
                optimized_item = self._optimize_bibliography_item(item_dict)
                items_data.append(optimized_item)
            
            # Sort items by title for consistent ordering
            items_data.sort(key=lambda x: x.get("title", "").lower())
            
            # Create the final JSON structure
            json_data = {
                "metadata": {
                    "total_items": len(items_data),
                    "generated_at": self._get_timestamp(),
                    "version": "1.0"
                },
                "items": items_data
            }
            
            # Write to file
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated bibliography JSON: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise JSONGenerationError(f"Failed to generate bibliography JSON: {str(e)}")
    
    def generate_collections_json(
        self, 
        collections: List[Collection], 
        filename: str = "collections.json"
    ) -> str:
        """
        Generate JSON file containing collection hierarchy data.
        
        Args:
            collections: List of root Collection objects (with nested children)
            filename: Output filename for the JSON file
            
        Returns:
            Path to the generated JSON file
            
        Raises:
            JSONGenerationError: If JSON generation fails
        """
        try:
            self.logger.info(f"Generating collections JSON for {len(collections)} root collections")
            
            # Convert collections to optimized dictionary format
            collections_data = []
            for collection in collections:
                collection_dict = collection.to_dict()
                optimized_collection = self._optimize_collection(collection_dict)
                collections_data.append(optimized_collection)
            
            # Create collection index for quick lookups
            collection_index = self._create_collection_index(collections)
            
            # Create the final JSON structure
            json_data = {
                "metadata": {
                    "total_collections": len(collection_index),
                    "root_collections": len(collections_data),
                    "generated_at": self._get_timestamp(),
                    "version": "1.0"
                },
                "collections": collections_data,
                "index": collection_index
            }
            
            # Write to file
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated collections JSON: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise JSONGenerationError(f"Failed to generate collections JSON: {str(e)}")
    
    def generate_search_index(
        self, 
        items: List[BibliographyItem], 
        filename: str = "search_index.json"
    ) -> str:
        """
        Generate optimized search index for client-side searching.
        
        Args:
            items: List of BibliographyItem objects
            filename: Output filename for the search index
            
        Returns:
            Path to the generated search index file
            
        Raises:
            JSONGenerationError: If search index generation fails
        """
        try:
            self.logger.info(f"Generating search index for {len(items)} items")
            
            search_data = []
            for item in items:
                # Create searchable text combining multiple fields
                searchable_text = self._create_searchable_text(item)
                
                search_entry = {
                    "id": item.id,
                    "title": item.title,
                    "authors": item.get_author_names(),
                    "year": item.year,
                    "venue": item.venue,
                    "type": item.type.value,
                    "searchable": searchable_text,
                    "keywords": item.keywords
                }
                
                search_data.append(search_entry)
            
            # Create the search index structure
            json_data = {
                "metadata": {
                    "total_items": len(search_data),
                    "generated_at": self._get_timestamp(),
                    "version": "1.0"
                },
                "index": search_data
            }
            
            # Write to file
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated search index: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise JSONGenerationError(f"Failed to generate search index: {str(e)}")
    
    def generate_combined_data(
        self, 
        items: List[BibliographyItem], 
        collections: List[Collection],
        filename: str = "data.json"
    ) -> str:
        """
        Generate a single JSON file containing all data for smaller datasets.
        
        Args:
            items: List of BibliographyItem objects
            collections: List of root Collection objects
            filename: Output filename for the combined data file
            
        Returns:
            Path to the generated combined data file
            
        Raises:
            JSONGenerationError: If combined data generation fails
        """
        try:
            self.logger.info(f"Generating combined data file with {len(items)} items and {len(collections)} collections")
            
            # Generate optimized data structures
            items_data = [self._optimize_bibliography_item(item.to_dict()) for item in items]
            collections_data = [self._optimize_collection(col.to_dict()) for col in collections]
            
            # Sort for consistent ordering
            items_data.sort(key=lambda x: x.get("title", "").lower())
            
            # Create collection index
            collection_index = self._create_collection_index(collections)
            
            # Create the combined JSON structure
            json_data = {
                "metadata": {
                    "total_items": len(items_data),
                    "total_collections": len(collection_index),
                    "root_collections": len(collections_data),
                    "generated_at": self._get_timestamp(),
                    "version": "1.0"
                },
                "bibliography": {
                    "items": items_data
                },
                "collections": {
                    "hierarchy": collections_data,
                    "index": collection_index
                }
            }
            
            # Write to file
            output_path = self.output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Generated combined data file: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise JSONGenerationError(f"Failed to generate combined data: {str(e)}")
    
    def _optimize_bibliography_item(self, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize bibliography item dictionary for client-side use.
        
        Args:
            item_dict: Raw item dictionary
            
        Returns:
            Optimized item dictionary
        """
        # Remove empty fields to reduce file size
        optimized = {}
        
        for key, value in item_dict.items():
            if value is not None and value != "" and value != []:
                if key == "authors":
                    # Simplify author structure for client-side use
                    optimized[key] = [
                        {
                            "name": author.get("full_name", ""),
                            "given": author.get("given_name", ""),
                            "surname": author.get("surname", "")
                        }
                        for author in value
                        if author.get("full_name")
                    ]
                elif key == "attachments":
                    # Only include attachments with URLs
                    optimized[key] = [
                        att for att in value 
                        if att.get("url") or att.get("title")
                    ]
                else:
                    optimized[key] = value
        
        return optimized
    
    def _optimize_collection(self, collection_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize collection dictionary for client-side use.
        
        Args:
            collection_dict: Raw collection dictionary
            
        Returns:
            Optimized collection dictionary
        """
        optimized = {
            "id": collection_dict["id"],
            "title": collection_dict["title"],
            "itemCount": collection_dict["item_count"]
        }
        
        # Only include parent_id if it exists
        if collection_dict.get("parent_id"):
            optimized["parentId"] = collection_dict["parent_id"]
        
        # Only include item_ids if there are items
        if collection_dict.get("item_ids"):
            optimized["itemIds"] = collection_dict["item_ids"]
        
        # Recursively optimize children
        if collection_dict.get("children"):
            optimized["children"] = [
                self._optimize_collection(child)
                for child in collection_dict["children"]
            ]
        
        return optimized
    
    def _create_collection_index(self, collections: List[Collection]) -> Dict[str, Any]:
        """
        Create a flat index of all collections for quick lookups.
        
        Args:
            collections: List of root collections
            
        Returns:
            Dictionary mapping collection IDs to collection info
        """
        index = {}
        
        def _index_collection(collection: Collection, path: List[str] = None):
            if path is None:
                path = []
            
            current_path = path + [collection.title]
            
            index[collection.id] = {
                "title": collection.title,
                "path": current_path,
                "itemCount": collection.item_count,
                "hasChildren": len(collection.children) > 0,
                "parentId": collection.parent_id
            }
            
            # Index children recursively
            for child in collection.children:
                _index_collection(child, current_path)
        
        for collection in collections:
            _index_collection(collection)
        
        return index
    
    def _create_searchable_text(self, item: BibliographyItem) -> str:
        """
        Create searchable text by combining multiple fields.
        
        Args:
            item: BibliographyItem object
            
        Returns:
            Combined searchable text string
        """
        searchable_parts = []
        
        # Add title
        if item.title:
            searchable_parts.append(item.title.lower())
        
        # Add author names
        for author in item.authors:
            if author.full_name:
                searchable_parts.append(author.full_name.lower())
        
        # Add venue
        if item.venue:
            searchable_parts.append(item.venue.lower())
        
        # Add abstract (first 200 characters to keep index size reasonable)
        if item.abstract:
            abstract_excerpt = item.abstract[:200].lower()
            searchable_parts.append(abstract_excerpt)
        
        # Add keywords
        searchable_parts.extend([kw.lower() for kw in item.keywords])
        
        return " ".join(searchable_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_output_files(self) -> List[str]:
        """
        Get list of all generated JSON files.
        
        Returns:
            List of file paths for generated JSON files
        """
        json_files = []
        
        if self.output_dir.exists():
            for file_path in self.output_dir.glob("*.json"):
                json_files.append(str(file_path))
        
        return sorted(json_files)
    
    def validate_json_files(self) -> Dict[str, bool]:
        """
        Validate that generated JSON files are valid JSON.
        
        Returns:
            Dictionary mapping file paths to validation results
        """
        validation_results = {}
        
        for file_path in self.get_output_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                validation_results[file_path] = True
                self.logger.debug(f"JSON validation passed: {file_path}")
            except json.JSONDecodeError as e:
                validation_results[file_path] = False
                self.logger.error(f"JSON validation failed for {file_path}: {str(e)}")
            except Exception as e:
                validation_results[file_path] = False
                self.logger.error(f"Error validating {file_path}: {str(e)}")
        
        return validation_results
    
    def get_file_sizes(self) -> Dict[str, int]:
        """
        Get file sizes for all generated JSON files.
        
        Returns:
            Dictionary mapping file paths to file sizes in bytes
        """
        file_sizes = {}
        
        for file_path in self.get_output_files():
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    file_sizes[file_path] = path_obj.stat().st_size
            except Exception as e:
                self.logger.warning(f"Could not get size for {file_path}: {str(e)}")
        
        return file_sizes