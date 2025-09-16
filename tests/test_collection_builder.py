"""Unit tests for collection hierarchy building functionality."""

import pytest
from zotero_webviewer.collection_builder import (
    CollectionHierarchyBuilder,
    CollectionHierarchyError
)
from zotero_webviewer.data_transformer import Collection, BibliographyItem


class TestCollectionHierarchyBuilder:
    """Test cases for CollectionHierarchyBuilder class."""
    
    def test_init(self):
        """Test CollectionHierarchyBuilder initialization."""
        builder = CollectionHierarchyBuilder()
        assert builder.logger is not None
        assert builder._collections_by_id == {}
        assert builder._root_collections == []
    
    def test_build_hierarchy_flat_collections(self):
        """Test building hierarchy from flat collections (no parent-child relationships)."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="col1", title="Collection 1"),
            Collection(id="col2", title="Collection 2"),
            Collection(id="col3", title="Collection 3")
        ]
        
        hierarchy = builder.build_hierarchy(collections)
        
        assert len(hierarchy) == 3
        assert all(col.parent_id is None for col in hierarchy)
        assert all(len(col.children) == 0 for col in hierarchy)
        
        # Should be sorted by title
        titles = [col.title for col in hierarchy]
        assert titles == sorted(titles)
    
    def test_build_hierarchy_with_parent_child_relationships(self):
        """Test building hierarchy with parent-child relationships."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="parent", title="Parent Collection"),
            Collection(id="child1", title="Child 1", parent_id="parent"),
            Collection(id="child2", title="Child 2", parent_id="parent"),
            Collection(id="grandchild", title="Grandchild", parent_id="child1")
        ]
        
        hierarchy = builder.build_hierarchy(collections)
        
        # Should have only one root collection
        assert len(hierarchy) == 1
        
        parent = hierarchy[0]
        assert parent.id == "parent"
        assert len(parent.children) == 2
        
        # Check children
        child_titles = [child.title for child in parent.children]
        assert "Child 1" in child_titles
        assert "Child 2" in child_titles
        
        # Check grandchild
        child1 = next(child for child in parent.children if child.title == "Child 1")
        assert len(child1.children) == 1
        assert child1.children[0].title == "Grandchild"
    
    def test_build_hierarchy_orphaned_collection(self):
        """Test building hierarchy with orphaned collection (parent not found)."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="orphan", title="Orphan", parent_id="nonexistent"),
            Collection(id="normal", title="Normal Collection")
        ]
        
        hierarchy = builder.build_hierarchy(collections)
        
        # Orphaned collection should be treated as root
        assert len(hierarchy) == 2
        
        orphan = next(col for col in hierarchy if col.title == "Orphan")
        assert orphan.parent_id is None  # Should be cleared
    
    def test_assign_items_to_collections(self, sample_bibliography_items):
        """Test assigning bibliography items to collections."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="collection1", title="Collection 1"),
            Collection(id="collection2", title="Collection 2")
        ]
        
        # Build hierarchy first
        hierarchy = builder.build_hierarchy(collections)
        
        # Assign items
        builder.assign_items_to_collections(sample_bibliography_items, hierarchy)
        
        # Check assignments
        col1 = builder.get_collection_by_id("collection1")
        col2 = builder.get_collection_by_id("collection2")
        
        assert col1 is not None
        assert col2 is not None
        
        # Items should be assigned based on their collections list
        assert "item1" in col1.item_ids
        assert "item2" in col1.item_ids
        assert "item1" in col2.item_ids
    
    def test_assign_items_to_collections_with_hierarchy(self):
        """Test assigning items to hierarchical collections."""
        builder = CollectionHierarchyBuilder()
        
        parent = Collection(id="parent", title="Parent")
        child = Collection(id="child", title="Child", parent_id="parent")
        collections = [parent, child]
        
        items = [
            BibliographyItem(id="item1", title="Item 1", collections=["parent"]),
            BibliographyItem(id="item2", title="Item 2", collections=["child"])
        ]
        
        hierarchy = builder.build_hierarchy(collections)
        builder.assign_items_to_collections(items, hierarchy)
        
        parent_col = builder.get_collection_by_id("parent")
        child_col = builder.get_collection_by_id("child")
        
        assert "item1" in parent_col.item_ids
        assert "item2" in child_col.item_ids
        
        # Check item counts (should include children)
        assert parent_col.item_count == 2  # item1 + item2 from child
        assert child_col.item_count == 1   # item2 only
    
    def test_get_collection_by_id(self):
        """Test retrieving collection by ID."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="col1", title="Collection 1"),
            Collection(id="col2", title="Collection 2")
        ]
        
        builder.build_hierarchy(collections)
        
        col1 = builder.get_collection_by_id("col1")
        assert col1 is not None
        assert col1.title == "Collection 1"
        
        nonexistent = builder.get_collection_by_id("nonexistent")
        assert nonexistent is None
    
    def test_get_all_item_ids_in_collection(self):
        """Test getting all item IDs in a collection including children."""
        builder = CollectionHierarchyBuilder()
        
        parent = Collection(id="parent", title="Parent", item_ids=["item1"])
        child = Collection(id="child", title="Child", parent_id="parent", item_ids=["item2", "item3"])
        
        hierarchy = builder.build_hierarchy([parent, child])
        
        # Get all items in parent (should include child items)
        all_items = builder.get_all_item_ids_in_collection("parent")
        
        assert len(all_items) == 3
        assert "item1" in all_items
        assert "item2" in all_items
        assert "item3" in all_items
    
    def test_get_collection_path(self):
        """Test getting full path from root to collection."""
        builder = CollectionHierarchyBuilder()
        
        root = Collection(id="root", title="Root")
        middle = Collection(id="middle", title="Middle", parent_id="root")
        leaf = Collection(id="leaf", title="Leaf", parent_id="middle")
        
        builder.build_hierarchy([root, middle, leaf])
        
        path = builder.get_collection_path("leaf")
        
        assert len(path) == 3
        assert path[0].title == "Root"
        assert path[1].title == "Middle"
        assert path[2].title == "Leaf"
    
    def test_get_collection_path_nonexistent(self):
        """Test getting path for non-existent collection."""
        builder = CollectionHierarchyBuilder()
        
        path = builder.get_collection_path("nonexistent")
        assert path == []
    
    def test_find_collections_containing_item(self):
        """Test finding all collections that contain a specific item."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="col1", title="Collection 1", item_ids=["item1", "item2"]),
            Collection(id="col2", title="Collection 2", item_ids=["item1", "item3"]),
            Collection(id="col3", title="Collection 3", item_ids=["item3"])
        ]
        
        builder.build_hierarchy(collections)
        
        # Find collections containing item1
        containing = builder.find_collections_containing_item("item1")
        
        assert len(containing) == 2
        titles = [col.title for col in containing]
        assert "Collection 1" in titles
        assert "Collection 2" in titles
    
    def test_validate_hierarchy_valid(self):
        """Test validation of valid hierarchy."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="parent", title="Parent"),
            Collection(id="child", title="Child", parent_id="parent")
        ]
        
        builder.build_hierarchy(collections)
        errors = builder.validate_hierarchy()
        
        assert len(errors) == 0
    
    def test_validate_hierarchy_circular_reference(self):
        """Test validation catches circular references."""
        builder = CollectionHierarchyBuilder()
        
        # Create circular reference manually (can't happen through normal build_hierarchy)
        col1 = Collection(id="col1", title="Collection 1", parent_id="col2")
        col2 = Collection(id="col2", title="Collection 2", parent_id="col1")
        
        # Manually set up the internal state to test validation
        builder._collections_by_id = {"col1": col1, "col2": col2}
        
        errors = builder.validate_hierarchy()
        
        assert len(errors) > 0
        assert any("Circular reference" in error for error in errors)
    
    def test_validate_hierarchy_orphaned_collections(self):
        """Test validation catches orphaned collections."""
        builder = CollectionHierarchyBuilder()
        
        # Create collection with non-existent parent
        orphan = Collection(id="orphan", title="Orphan", parent_id="nonexistent")
        
        # Manually set up internal state
        builder._collections_by_id = {"orphan": orphan}
        
        errors = builder.validate_hierarchy()
        
        assert len(errors) > 0
        assert any("references non-existent parent" in error for error in errors)
    
    def test_validate_hierarchy_duplicate_titles(self):
        """Test validation catches duplicate collection titles at same level."""
        builder = CollectionHierarchyBuilder()
        
        collections = [
            Collection(id="col1", title="Duplicate Title"),
            Collection(id="col2", title="Duplicate Title")  # Same title, same level (root)
        ]
        
        builder.build_hierarchy(collections)
        errors = builder.validate_hierarchy()
        
        assert len(errors) > 0
        assert any("Duplicate collection title" in error for error in errors)
    
    def test_get_statistics(self):
        """Test getting hierarchy statistics."""
        builder = CollectionHierarchyBuilder()
        
        parent = Collection(id="parent", title="Parent", item_ids=["item1"])
        child1 = Collection(id="child1", title="Child 1", parent_id="parent", item_ids=["item2"])
        child2 = Collection(id="child2", title="Child 2", parent_id="parent")
        grandchild = Collection(id="grandchild", title="Grandchild", parent_id="child1", item_ids=["item3"])
        
        builder.build_hierarchy([parent, child1, child2, grandchild])
        
        stats = builder.get_statistics()
        
        assert stats["total_collections"] == 4
        assert stats["root_collections"] == 1
        assert stats["max_depth"] == 3  # parent -> child1 -> grandchild
        assert stats["collections_with_items"] == 3  # parent, child1, grandchild
        assert stats["total_items"] == 3  # item1, item2, item3


class TestCollectionHierarchyBuilderEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_build_hierarchy_empty_list(self):
        """Test building hierarchy from empty collection list."""
        builder = CollectionHierarchyBuilder()
        
        hierarchy = builder.build_hierarchy([])
        
        assert hierarchy == []
        assert builder._collections_by_id == {}
        assert builder._root_collections == []
    
    def test_build_hierarchy_exception_handling(self, monkeypatch):
        """Test exception handling during hierarchy building."""
        builder = CollectionHierarchyBuilder()
        
        # Mock a method to raise an exception
        def mock_add_child(self, child):
            raise Exception("Test exception")
        
        monkeypatch.setattr(Collection, "add_child", mock_add_child)
        
        collections = [
            Collection(id="parent", title="Parent"),
            Collection(id="child", title="Child", parent_id="parent")
        ]
        
        with pytest.raises(CollectionHierarchyError, match="Failed to build collection hierarchy"):
            builder.build_hierarchy(collections)
    
    def test_assign_items_exception_handling(self, monkeypatch):
        """Test exception handling during item assignment."""
        builder = CollectionHierarchyBuilder()
        
        collections = [Collection(id="col1", title="Collection 1")]
        items = [BibliographyItem(id="item1", title="Item 1")]
        
        builder.build_hierarchy(collections)
        
        # Mock a method to raise an exception
        def mock_update_item_count(self):
            raise Exception("Test exception")
        
        monkeypatch.setattr(Collection, "update_item_count", mock_update_item_count)
        
        with pytest.raises(CollectionHierarchyError, match="Failed to assign items to collections"):
            builder.assign_items_to_collections(items, collections)
    
    def test_assign_items_to_collections_item_not_found(self):
        """Test assigning items when collection references don't exist."""
        builder = CollectionHierarchyBuilder()
        
        collections = [Collection(id="existing", title="Existing")]
        items = [BibliographyItem(id="item1", title="Item 1", collections=["nonexistent"])]
        
        hierarchy = builder.build_hierarchy(collections)
        
        # Should not raise exception, but log warnings
        builder.assign_items_to_collections(items, hierarchy)
        
        # Item should not be assigned to any collection
        existing_col = builder.get_collection_by_id("existing")
        assert len(existing_col.item_ids) == 0
    
    def test_circular_reference_detection(self):
        """Test circular reference detection in complex scenarios."""
        builder = CollectionHierarchyBuilder()
        
        # Create a more complex circular reference scenario
        col1 = Collection(id="col1", title="Collection 1", parent_id="col3")
        col2 = Collection(id="col2", title="Collection 2", parent_id="col1")
        col3 = Collection(id="col3", title="Collection 3", parent_id="col2")
        
        # Manually set up internal state
        builder._collections_by_id = {"col1": col1, "col2": col2, "col3": col3}
        
        # Test circular reference detection
        assert builder._has_circular_reference(col1)
        assert builder._has_circular_reference(col2)
        assert builder._has_circular_reference(col3)
    
    def test_max_depth_calculation_single_level(self):
        """Test maximum depth calculation for single level."""
        builder = CollectionHierarchyBuilder()
        
        collection = Collection(id="single", title="Single Level")
        
        depth = builder._calculate_max_depth(collection)
        assert depth == 1
    
    def test_max_depth_calculation_multiple_levels(self):
        """Test maximum depth calculation for multiple levels."""
        builder = CollectionHierarchyBuilder()
        
        # Create hierarchy: root -> child1 -> grandchild
        #                       -> child2
        root = Collection(id="root", title="Root")
        child1 = Collection(id="child1", title="Child 1")
        child2 = Collection(id="child2", title="Child 2")
        grandchild = Collection(id="grandchild", title="Grandchild")
        
        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)
        
        depth = builder._calculate_max_depth(root)
        assert depth == 3  # root -> child1 -> grandchild
    
    def test_flatten_collections_list(self):
        """Test flattening hierarchical collections."""
        builder = CollectionHierarchyBuilder()
        
        parent = Collection(id="parent", title="Parent")
        child1 = Collection(id="child1", title="Child 1")
        child2 = Collection(id="child2", title="Child 2")
        grandchild = Collection(id="grandchild", title="Grandchild")
        
        parent.add_child(child1)
        parent.add_child(child2)
        child1.add_child(grandchild)
        
        flattened = builder._flatten_collections([parent])
        
        assert len(flattened) == 4
        ids = [col.id for col in flattened]
        assert "parent" in ids
        assert "child1" in ids
        assert "child2" in ids
        assert "grandchild" in ids
    
    def test_validation_exception_handling(self, monkeypatch):
        """Test exception handling during validation."""
        builder = CollectionHierarchyBuilder()
        
        collections = [Collection(id="col1", title="Collection 1")]
        builder.build_hierarchy(collections)
        
        # Mock a method to raise an exception during validation
        def mock_has_circular_reference(self, collection, visited=None):
            raise Exception("Validation error")
        
        monkeypatch.setattr(builder, "_has_circular_reference", mock_has_circular_reference)
        
        errors = builder.validate_hierarchy()
        
        assert len(errors) > 0
        assert any("Error during hierarchy validation" in error for error in errors)