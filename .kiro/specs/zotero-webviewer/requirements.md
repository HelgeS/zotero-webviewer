# Requirements Document

## Introduction

The Literature Collection Webviewer is a static website that provides an interactive interface for browsing and exploring academic literature collections exported from Zotero as RDF files. The system will convert Zotero RDF data into a web-friendly format and present it through a responsive interface featuring hierarchical collection browsing, comprehensive search functionality, and detailed bibliography display. The solution must be deployable as a static site (e.g., GitHub Pages) while maintaining dynamic client-side functionality for sorting, filtering, and navigation.

## Requirements

### Requirement 1

**User Story:** As a researcher, I want to view all my literature in a comprehensive table format, so that I can quickly scan through my entire collection and access bibliographic details.

#### Acceptance Criteria

1. WHEN the webviewer loads THEN the system SHALL display all literature items in a table format with columns for title, authors, publication year, journal/venue, and item type
2. WHEN displaying the bibliography table THEN the system SHALL show complete author lists, publication titles, and venue information for each item
3. WHEN the table contains many items THEN the system SHALL implement pagination or virtual scrolling to maintain performance
4. WHEN a user clicks on a literature item THEN the system SHALL display detailed bibliographic information including abstract, DOI, and other metadata

### Requirement 2

**User Story:** As a researcher, I want to browse my literature by collection hierarchy, so that I can focus on specific research topics or organizational categories.

#### Acceptance Criteria

1. WHEN the webviewer loads THEN the system SHALL display a tree-style navigation menu on the left side showing all collections and subcollections
2. WHEN a user clicks on a collection THEN the system SHALL filter the main table to show only items in that collection and its subcollections
3. WHEN a collection is selected THEN the system SHALL expand the tree to show any subcollections within that collection
4. WHEN no collection is selected THEN the system SHALL display all literature items from all collections

### Requirement 3

**User Story:** As a researcher, I want to see my current navigation path, so that I understand which collection I'm currently viewing and can easily navigate back to parent collections.

#### Acceptance Criteria

1. WHEN a collection is selected THEN the system SHALL display a breadcrumb navigation above the literature table
2. WHEN displaying breadcrumbs THEN the system SHALL show the full hierarchy path from root to current collection
3. WHEN a user clicks on any breadcrumb item THEN the system SHALL navigate to that collection level
4. WHEN viewing all collections THEN the system SHALL display "All Collections" or similar indicator in the breadcrumb area

### Requirement 4

**User Story:** As a researcher, I want to search and sort my literature collection, so that I can quickly find specific papers or organize them by different criteria.

#### Acceptance Criteria

1. WHEN a user enters text in the search field THEN the system SHALL filter results to show only items matching the search term in title, authors, abstract, or keywords
2. WHEN a user clicks on column headers THEN the system SHALL sort the table by that column in ascending or descending order
3. WHEN search is active THEN the system SHALL maintain the current collection filter while applying the search
4. WHEN search results are displayed THEN the system SHALL highlight matching terms in the results

### Requirement 5

**User Story:** As a developer, I want the system to convert Zotero RDF data into a web-friendly format, so that the static website can efficiently load and display the literature data.

#### Acceptance Criteria

1. WHEN processing a Zotero RDF file THEN the system SHALL extract all bibliographic metadata including titles, authors, abstracts, publication details, and collection assignments
2. WHEN converting RDF data THEN the system SHALL generate a JSON file containing structured literature data and collection hierarchy
3. WHEN parsing collections THEN the system SHALL preserve the hierarchical relationship between collections and subcollections
4. WHEN generating output THEN the system SHALL create optimized data structures for client-side filtering and searching

### Requirement 6

**User Story:** As a researcher, I want the webviewer to work as a static website, so that I can easily host it on platforms like GitHub Pages without requiring server infrastructure.

#### Acceptance Criteria

1. WHEN the website is built THEN the system SHALL generate only static HTML, CSS, and JavaScript files
2. WHEN deployed THEN the system SHALL function completely client-side without requiring server-side processing
3. WHEN accessing the site THEN the system SHALL load quickly and work offline after initial load
4. WHEN building the site THEN the system SHALL include all necessary data files (JSON) alongside the static assets

### Requirement 7

**User Story:** As a developer, I want all code generation to be done in Python using modern tooling, so that the build process is maintainable and follows current best practices.

#### Acceptance Criteria

1. WHEN setting up the project THEN the system SHALL use `uv` for Python dependency management
2. WHEN processing RDF files THEN the system SHALL use appropriate Python libraries for RDF parsing and data manipulation
3. WHEN generating the website THEN the system SHALL create all HTML, CSS, and JavaScript files through Python scripts
4. WHEN building the project THEN the system SHALL provide a simple command-line interface for processing RDF files and generating the website