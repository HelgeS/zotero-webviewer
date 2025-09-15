"""Collection hierarchy building functionality."""

import logging
from typing import Dict, List, Optional, Set
from .data_transformer import Collection, BibliographyItem


class CollectionHierarchyError(Exception):
    """Exception raised when collection hierarchy building fails."""
    pass


class CollectionHierarchyBuilder:
    """Builds hierarchical collection structures from flat collection data."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._collections_by_id: Dict[str, Collection] = {}
        self._root_collections: List[Collection] = []
    
    def build_hierarchy(self, collections: List[Collection]) -> List[Collection]:
        """
        Build a hierarchical collection tree from a flat list of collections.
        
        Args:
            collections: List of Collection objects with potential parent-child relationships
            
        Returns:
            List of root-level Collection objects with nested children
            
        Raises:
            CollectionHierarchyError: If hierarchy building fails
        """
        try:
            self.logger.info(f"Building hierarchy from {len(collections)} collections")
            
            # Reset internal state
            self._collections_by_id.clear()
            self._root_collections.clear()
            
            # Index all collections by ID for quick lookup
            for collection in collections:
                self._collections_by_id[collection.id] = collection
                # Clear any existing children to rebuild the hierarchy
                collection.children.clear()
            
            # Build parent-child relationships
            for collection in collections:
                if collection.parent_id:
                    # This collection has a parent
                    parent = self._collections_by_id.get(collection.parent_id)
                    if parent:
                        parent.add_child(collection)
                        self.logger.debug(f"Added collection '{collection.title}' as child of '{parent.title}'")
                    else:
                        # Parent not found - treat as root collection but log warning
                        self.logger.warning(f"Parent collection '{collection.parent_id}' not found for '{collection.title}'. Treating as root collection.")
                        self._root_collections.append(collection)
                        collection.parent_id = None  # Clear invalid parent reference
                else:
                    # This is a root collection
                    self._root_collections.append(collection)
            
            # Update item counts for all collections (including children)
            for root_collection in self._root_collections:
                root_collection.update_item_count()
            
            # Sort collections by title for consistent ordering
            self._root_collections.sort(key=lambda c: c.title.lower())
            for collection in self._collections_by_id.values():
                collection.children.sort(key=lambda c: c.title.lower())
            
            self.logger.info(f"Built hierarchy with {len(self._root_collections)} root collections")
            return self._root_collections
            
        except Exception as e:
            raise CollectionHierarchyError(f"Failed to build collection hierarchy: {str(e)}")
    
    def assign_items_to_collections(
        self, 
        items: List[BibliographyItem], 
        collections: List[Collection]
    ) -> None:
        """
        Assign bibliography items to their respective collections.
        Supports items belonging to multiple collections.
        
        Args:
            items: List of BibliographyItem objects
            collections: List of Collection objects (can be hierarchical)
            
        Raises:
            CollectionHierarchyError: If assignment fails
        """
        try:
            self.logger.info(f"Assigning {len(items)} items to collections")
            
            # Create a flat mapping of all collections (including nested ones)
            all_collections = self._flatten_collections(collections)
            collections_by_id = {col.id: col for col in all_collections}
            
            # Clear existing item assignments
            for collection in all_collections:
                collection.item_ids.clear()
            
            # Track assignment statistics
            assigned_count = 0
            unassigned_items = []
            
            # Assign each item to its collections
            for item in items:
                item_assigned = False
                
                for collection_id in item.collections:
                    collection = collections_by_id.get(collection_id)
                    if collection:
                        if item.id not in collection.item_ids:
                            collection.item_ids.append(item.id)
                            item_assigned = True
                            self.logger.debug(f"Assigned item '{item.title}' to collection '{collection.title}'")
                    else:
                        self.logger.warning(f"Collection '{collection_id}' not found for item '{item.title}'")
                
                if item_assigned:
                    assigned_count += 1
                else:
                    unassigned_items.append(item)
            
            # Update item counts after assignment
            for collection in all_collections:
                collection.update_item_count()
            
            self.logger.info(f"Successfully assigned {assigned_count} items to collections")
            if unassigned_items:
                self.logger.warning(f"{len(unassigned_items)} items were not assigned to any collection")
                
        except Exception as e:
            raise CollectionHierarchyError(f"Failed to assign items to collections: {str(e)}")
    
    def get_collection_by_id(self, collection_id: str) -> Optional[Collection]:
        """
        Get a collection by its ID.
        
        Args:
            collection_id: The collection ID to search for
            
        Returns:
            Collection object if found, None otherwise
        """
        return self._collections_by_id.get(collection_id)
    
    def get_all_item_ids_in_collection(self, collection_id: str) -> Set[str]:
        """
        Get all item IDs in a collection, including items in child collections.
        
        Args:
            collection_id: The collection ID
            
        Returns:
            Set of item IDs in the collection and its children
        """
        collection = self.get_collection_by_id(collection_id)
        if collection:
            return collection.get_all_item_ids()
        return set()
    
    def get_collection_path(self, collection_id: str) -> List[Collection]:
        """
        Get the full path from root to the specified collection.
        
        Args:
            collection_id: The collection ID
            
        Returns:
            List of Collection objects from root to target collection
        """
        collection = self.get_collection_by_id(collection_id)
        if not collection:
            return []
        
        path = []
        current = collection
        
        # Build path from target to root
        while current:
            path.insert(0, current)  # Insert at beginning to build root-to-target path
            if current.parent_id:
                current = self.get_collection_by_id(current.parent_id)
            else:
                current = None
        
        return path
    
    def find_collections_containing_item(self, item_id: str) -> List[Collection]:
        """
        Find all collections that contain a specific item.
        
        Args:
            item_id: The item ID to search for
            
        Returns:
            List of Collection objects containing the item
        """
        containing_collections = []
        
        for collection in self._collections_by_id.values():
            if item_id in collection.item_ids:
                containing_collections.append(collection)
        
        return containing_collections
    
    def validate_hierarchy(self) -> List[str]:
        """
        Validate the collection hierarchy for common issues.
        
        Returns:
            List of validation error messages (empty if no issues)
        """
        errors = []
        
        try:
            # Check for circular references
            for collection in self._collections_by_id.values():
                if self._has_circular_reference(collection):
                    errors.append(f"Circular reference detected in collection '{collection.title}' ({collection.id})")
            
            # Check for orphaned collections (parent_id points to non-existent collection)
            for collection in self._collections_by_id.values():
                if collection.parent_id and collection.parent_id not in self._collections_by_id:
                    errors.append(f"Collection '{collection.title}' references non-existent parent '{collection.parent_id}'")
            
            # Check for duplicate collection titles at the same level
            title_counts_by_parent = {}
            for collection in self._collections_by_id.values():
                parent_key = collection.parent_id or "ROOT"
                if parent_key not in title_counts_by_parent:
                    title_counts_by_parent[parent_key] = {}
                
                title = collection.title.lower()
                if title in title_counts_by_parent[parent_key]:
                    title_counts_by_parent[parent_key][title] += 1
                else:
                    title_counts_by_parent[parent_key][title] = 1
            
            for parent_key, title_counts in title_counts_by_parent.items():
                for title, count in title_counts.items():
                    if count > 1:
                        parent_desc = "root level" if parent_key == "ROOT" else f"parent {parent_key}"
                        errors.append(f"Duplicate collection title '{title}' found at {parent_desc}")
        
        except Exception as e:
            errors.append(f"Error during hierarchy validation: {str(e)}")
        
        return errors
    
    def _flatten_collections(self, collections: List[Collection]) -> List[Collection]:
        """
        Flatten a hierarchical collection structure into a flat list.
        
        Args:
            collections: List of root collections (may contain nested children)
            
        Returns:
            Flat list of all collections
        """
        flattened = []
        
        def _add_collection_and_children(collection: Collection):
            flattened.append(collection)
            for child in collection.children:
                _add_collection_and_children(child)
        
        for collection in collections:
            _add_collection_and_children(collection)
        
        return flattened
    
    def _has_circular_reference(self, collection: Collection, visited: Optional[Set[str]] = None) -> bool:
        """
        Check if a collection has a circular reference in its parent chain.
        
        Args:
            collection: Collection to check
            visited: Set of already visited collection IDs
            
        Returns:
            True if circular reference detected, False otherwise
        """
        if visited is None:
            visited = set()
        
        if collection.id in visited:
            return True
        
        visited.add(collection.id)
        
        if collection.parent_id:
            parent = self.get_collection_by_id(collection.parent_id)
            if parent:
                return self._has_circular_reference(parent, visited.copy())
        
        return False
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the collection hierarchy.
        
        Returns:
            Dictionary with hierarchy statistics
        """
        stats = {
            "total_collections": len(self._collections_by_id),
            "root_collections": len(self._root_collections),
            "max_depth": 0,
            "total_items": 0,
            "collections_with_items": 0
        }
        
        # Calculate maximum depth and item statistics
        for root_collection in self._root_collections:
            depth = self._calculate_max_depth(root_collection)
            stats["max_depth"] = max(stats["max_depth"], depth)
        
        for collection in self._collections_by_id.values():
            if collection.item_ids:
                stats["collections_with_items"] += 1
                stats["total_items"] += len(collection.item_ids)
        
        return stats
    
    def _calculate_max_depth(self, collection: Collection, current_depth: int = 1) -> int:
        """Calculate the maximum depth of a collection tree."""
        if not collection.children:
            return current_depth
        
        max_child_depth = current_depth
        for child in collection.children:
            child_depth = self._calculate_max_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth