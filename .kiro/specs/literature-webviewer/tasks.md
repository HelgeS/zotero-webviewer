# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create Python project structure with uv dependency management
  - Configure pyproject.toml with required dependencies (rdflib, jinja2, click)
  - Create basic directory structure for source code, templates, and output
  - _Requirements: 7.1, 7.2_

- [x] 2. Implement RDF parsing functionality
  - [x] 2.1 Create RDF parser module
    - Write RDFParser class to load and parse Zotero RDF files using rdflib
    - Implement methods to extract bibliography items and collections from RDF graph
    - Add error handling for malformed RDF files and missing data
    - _Requirements: 5.1, 5.3_

  - [x] 2.2 Create data models and transformation utilities
    - Define Python dataclasses for BibliographyItem, Author, Collection, and Attachment
    - Implement DataTransformer class to convert raw RDF data to structured models
    - Add author name parsing and normalization functionality
    - _Requirements: 5.1, 5.2_

- [x] 3. Build collection hierarchy processing
  - [x] 3.1 Implement collection hierarchy builder
    - Write CollectionHierarchyBuilder class to construct nested collection trees
    - Implement logic to assign bibliography items to their respective collections
    - Add support for items belonging to multiple collections
    - _Requirements: 2.2, 5.3_

  - [x] 3.2 Create JSON data generation
    - Implement JSONGenerator class to serialize processed data to JSON files
    - Generate separate JSON files for bibliography items and collection hierarchy
    - Optimize JSON structure for efficient client-side loading and filtering
    - _Requirements: 5.2, 6.3_

- [x] 4. Develop static site generation
  - [x] 4.1 Create HTML template system
    - Design responsive HTML template using Jinja2 with semantic markup
    - Implement template for main layout with collection tree, breadcrumbs, and bibliography table
    - Add mobile-responsive CSS Grid and Flexbox layouts
    - _Requirements: 1.1, 2.1, 3.1, 6.1_

  - [x] 4.2 Implement CSS styling system
    - Create comprehensive CSS styles for collection tree navigation
    - Style bibliography table with sortable columns and hover effects
    - Implement responsive design patterns for mobile and desktop views
    - _Requirements: 1.1, 2.1, 4.2_

- [x] 5. Build client-side JavaScript functionality
  - [x] 5.1 Create data loading and initialization
    - Write JavaScript module to fetch and load JSON data files
    - Implement application state initialization and error handling
    - Add loading indicators and progressive enhancement
    - _Requirements: 6.2, 6.3_

  - [x] 5.2 Implement collection tree navigation
    - Create CollectionTree component for hierarchical navigation display
    - Add click handlers for collection selection and tree expansion/collapse
    - Implement visual feedback for selected collections and navigation states
    - _Requirements: 2.2, 2.3_

  - [x] 5.3 Build bibliography table functionality
    - Create BibliographyTable component with sortable columns
    - Implement table filtering based on selected collections
    - Add pagination or virtual scrolling for large datasets
    - _Requirements: 1.1, 1.3, 4.2_

- [x] 6. Implement search and filtering features
  - [x] 6.1 Create search functionality
    - Build SearchComponent with real-time text filtering
    - Implement full-text search across title, authors, abstract, and keywords
    - Add search result highlighting and debounced input handling
    - _Requirements: 4.1, 4.3, 4.4_

  - [x] 6.2 Develop filter coordination system
    - Create FilterController to manage combined collection and search filters
    - Implement logic to apply multiple filters simultaneously
    - Add URL parameter management for shareable filtered views
    - _Requirements: 4.3_

- [ ] 7. Build breadcrumb navigation system
  - Create BreadcrumbComponent to display current collection hierarchy path
  - Implement click handlers for breadcrumb navigation to parent collections
  - Add visual indicators for current location and navigation history
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 8. Create command-line interface
  - [x] 8.1 Implement CLI application
    - Write Click-based CLI for processing RDF files and generating websites
    - Add command-line options for input/output paths and build configurations
    - Implement progress indicators and verbose logging options
    - _Requirements: 7.4_

  - [x] 8.2 Add build pipeline integration
    - Create main build function that orchestrates the entire RDF-to-website pipeline
    - Add file watching and incremental rebuild capabilities
    - Implement validation and error reporting for the complete build process
    - _Requirements: 7.4, 5.4_

- [ ] 9. Implement detailed item view functionality
  - Create modal or expandable view for detailed bibliography information
  - Display complete metadata including abstracts, DOIs, and attachment links
  - Add copy-to-clipboard functionality for citations and metadata
  - _Requirements: 1.4_

- [ ] 10. Add comprehensive error handling and validation
  - [ ] 10.1 Implement build-time error handling
    - Add comprehensive error handling for RDF parsing failures
    - Create validation for required bibliography fields and data integrity
    - Implement graceful handling of missing or malformed data
    - _Requirements: 5.1, 7.3_

  - [ ] 10.2 Add runtime error handling
    - Implement client-side error handling for data loading failures
    - Add user feedback for network errors and loading states
    - Create fallback mechanisms for browser compatibility issues
    - _Requirements: 6.2, 6.3_

- [ ] 11. Create comprehensive test suite
  - [ ] 11.1 Write unit tests for core functionality
    - Create tests for RDF parsing with various Zotero export formats
    - Test data transformation and collection hierarchy building
    - Add tests for JSON generation and template rendering
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 11.2 Implement integration and end-to-end tests
    - Create tests for complete RDF-to-website build pipeline
    - Test web interface functionality with sample data
    - Add performance tests for large dataset handling
    - _Requirements: 1.3, 6.3_

- [ ] 12. Optimize performance and finalize deployment
  - [ ] 12.1 Implement performance optimizations
    - Add lazy loading for large bibliography collections
    - Optimize search indexing and filtering performance
    - Implement efficient virtual scrolling for large tables
    - _Requirements: 1.3, 4.1, 6.3_

  - [ ] 12.2 Prepare for static deployment
    - Generate production-ready static assets with minification
    - Create deployment documentation and GitHub Pages configuration
    - Create GitHub action to automatically build the static page on push
    - Add build artifacts and deployment scripts
    - Add uv command to build the page: `uv run build`
    - _Requirements: 6.1, 6.2, 6.4_