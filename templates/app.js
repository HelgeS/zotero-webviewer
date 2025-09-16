// JavaScript application for literature webviewer

/**
 * Application state and configuration
 */
const AppState = {
    bibliography: [],
    collections: {},
    collectionTree: [],
    filteredItems: [],
    currentCollection: null,
    searchQuery: '',
    sortColumn: 'title',
    sortDirection: 'asc',
    currentPage: 1,
    itemsPerPage: 50,
    isLoading: false,
    error: null,
    // Performance optimization state
    searchIndex: null,
    virtualScrolling: {
        enabled: false,
        itemHeight: 60,
        containerHeight: 0,
        scrollTop: 0,
        visibleStart: 0,
        visibleEnd: 0,
        bufferSize: 5
    },
    lazyLoading: {
        enabled: true,
        chunkSize: 100,
        loadedChunks: new Set()
    }
};

/**
 * Data loading and initialization module
 */
const DataLoader = {
    /**
     * Initialize the application by loading data and setting up the UI
     */
    async init() {
        try {
            this.showLoading(true);
            await this.loadData();
            this.initializeUI();
            this.hideLoading();
            console.log('Literature Webviewer initialized successfully');
        } catch (error) {
            this.handleError('Failed to initialize application', error);
        }
    },

    /**
     * Load JSON data files for bibliography and collections
     */
    async loadData() {
        try {
            const [bibliographyResponse, collectionsResponse] = await Promise.all([
                fetch('data/bibliography.json'),
                fetch('data/collections.json')
            ]);

            if (!bibliographyResponse.ok) {
                throw new Error(`Failed to load bibliography data: ${bibliographyResponse.status}`);
            }
            if (!collectionsResponse.ok) {
                throw new Error(`Failed to load collections data: ${collectionsResponse.status}`);
            }

            const bibliographyData = await bibliographyResponse.json();
            const collectionsData = await collectionsResponse.json();

            // Store data in application state
            AppState.bibliography = bibliographyData.items || [];
            AppState.collections = collectionsData.collections || {};
            AppState.collectionTree = collectionsData.tree || [];
            AppState.filteredItems = [...AppState.bibliography];

            console.log(`Loaded ${AppState.bibliography.length} bibliography items and ${Object.keys(AppState.collections).length} collections`);
        } catch (error) {
            // Check if this is a CORS error (common when opening file:// directly)
            if (error.message.includes('NetworkError') || error.message.includes('CORS') || 
                window.location.protocol === 'file:') {
                throw new Error(`Data loading failed due to CORS restrictions. 
                
To fix this issue:
1. Serve the website using a local HTTP server:
   - Run: python3 -m http.server 8000
   - Then open: http://localhost:8000
   
2. Or deploy to a web server (GitHub Pages, Netlify, etc.)

Technical details: ${error.message}`);
            }
            throw new Error(`Data loading failed: ${error.message}`);
        }
    },

    /**
     * Initialize UI components and event handlers
     */
    initializeUI() {
        // Initialize performance optimizations first
        if (window.PerformanceOptimizer) {
            window.PerformanceOptimizer.init();
        }
        
        // Initialize breadcrumb component
        if (window.BreadcrumbComponent) {
            window.BreadcrumbComponent.init();
        }
        
        // Initialize bibliography table
        if (window.BibliographyTable) {
            window.BibliographyTable.init();
        }
        
        // Initialize detailed item view
        if (window.DetailedItemView) {
            window.DetailedItemView.init();
        }
        
        // Initialize filter controller
        if (window.FilterController) {
            window.FilterController.init();
        }
        
        // Initialize collection tree
        if (window.CollectionTree) {
            window.CollectionTree.init();
        }
        
        // Update results count
        this.updateResultsCount();
        
        // Initialize search functionality
        this.initializeSearch();
        
        // Initialize error handling
        this.initializeErrorHandling();
        
        // Set up keyboard navigation
        this.initializeKeyboardNavigation();
    },

    /**
     * Initialize search input with debounced handling
     */
    initializeSearch() {
        // Initialize the SearchComponent
        if (window.SearchComponent) {
            window.SearchComponent.init();
        }
    },

    /**
     * Handle search input with debouncing
     */
    handleSearch(query) {
        AppState.searchQuery = query.trim().toLowerCase();
        AppState.currentPage = 1; // Reset to first page
        
        // Show/hide clear button
        const searchClear = document.querySelector('.search-clear');
        if (searchClear) {
            searchClear.style.display = AppState.searchQuery ? 'block' : 'none';
        }
        
        // Filter items and update display
        this.filterItems();
        this.updateResultsCount();
        
        // Trigger table update (will be implemented in subtask 5.3)
        if (window.BibliographyTable && window.BibliographyTable.update) {
            window.BibliographyTable.update();
        }
    },

    /**
     * Clear search input and filters
     */
    clearSearch() {
        const searchInput = document.getElementById('search-input');
        const searchClear = document.querySelector('.search-clear');
        
        if (searchInput) {
            searchInput.value = '';
        }
        if (searchClear) {
            searchClear.style.display = 'none';
        }
        
        AppState.searchQuery = '';
        this.filterItems();
        this.updateResultsCount();
        
        // Trigger table update
        if (window.BibliographyTable && window.BibliographyTable.update) {
            window.BibliographyTable.update();
        }
    },

    /**
     * Filter items based on current search and collection filters
     */
    filterItems() {
        let filtered = [...AppState.bibliography];
        
        // Apply collection filter
        if (AppState.currentCollection) {
            const collectionIds = this.getCollectionAndDescendantIds(AppState.currentCollection);
            filtered = filtered.filter(item => 
                item.collections && item.collections.some(colId => collectionIds.includes(colId))
            );
        }
        
        // Apply search filter
        if (AppState.searchQuery) {
            filtered = filtered.filter(item => this.matchesSearch(item, AppState.searchQuery));
        }
        
        AppState.filteredItems = filtered;
    },

    /**
     * Check if an item matches the search query
     */
    matchesSearch(item, query) {
        if (window.SearchComponent) {
            return window.SearchComponent.performFullTextSearch(item, query);
        }
        
        // Fallback implementation
        const searchFields = [
            item.title || '',
            (item.authors || []).map(author => author.name || author.fullName || '').join(' '),
            item.abstract || '',
            (item.keywords || []).join(' '),
            item.venue || ''
        ];
        
        const searchText = searchFields.join(' ').toLowerCase();
        return searchText.includes(query);
    },

    /**
     * Get collection ID and all descendant collection IDs
     */
    getCollectionAndDescendantIds(collectionId) {
        const ids = [collectionId];
        const collection = AppState.collections[collectionId];
        
        if (collection && collection.children) {
            collection.children.forEach(childId => {
                ids.push(...this.getCollectionAndDescendantIds(childId));
            });
        }
        
        return ids;
    },

    /**
     * Update the results count display
     */
    updateResultsCount() {
        const resultsCount = document.getElementById('results-count');
        if (resultsCount) {
            const total = AppState.filteredItems.length;
            const totalItems = AppState.bibliography.length;
            
            let text = `Showing ${total.toLocaleString()} item${total !== 1 ? 's' : ''}`;
            if (total !== totalItems) {
                text += ` of ${totalItems.toLocaleString()} total`;
            }
            
            if (AppState.searchQuery) {
                text += ` matching "${AppState.searchQuery}"`;
            }
            
            if (AppState.currentCollection) {
                const collection = AppState.collections[AppState.currentCollection];
                if (collection) {
                    text += ` in "${collection.title}"`;
                }
            }
            
            resultsCount.textContent = text;
        }
    },

    /**
     * Initialize error handling UI
     */
    initializeErrorHandling() {
        const errorContainer = document.getElementById('error-container');
        const errorDismiss = document.querySelector('.error-dismiss');
        
        if (errorDismiss) {
            errorDismiss.addEventListener('click', () => {
                this.hideError();
            });
        }
        
        // Close error on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && errorContainer && errorContainer.style.display !== 'none') {
                this.hideError();
            }
        });
    },

    /**
     * Initialize keyboard navigation
     */
    initializeKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + F to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        });
    },

    /**
     * Show loading indicator
     */
    showLoading(fullScreen = false) {
        AppState.isLoading = true;
        
        if (fullScreen) {
            const loadingOverlay = document.getElementById('loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
                loadingOverlay.setAttribute('aria-hidden', 'false');
            }
        }
    },

    /**
     * Hide loading indicator
     */
    hideLoading() {
        AppState.isLoading = false;
        
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
            loadingOverlay.setAttribute('aria-hidden', 'true');
        }
        
        // Hide loading indicators in content areas
        const loadingIndicators = document.querySelectorAll('.loading-indicator, .loading-row');
        loadingIndicators.forEach(indicator => {
            indicator.style.display = 'none';
        });
    },

    /**
     * Handle and display errors
     */
    handleError(message, error = null) {
        console.error(message, error);
        AppState.error = { message, error };
        this.hideLoading();
        this.showError(message);
    },

    /**
     * Show error message to user
     */
    showError(message) {
        const errorContainer = document.getElementById('error-container');
        const errorMessage = document.querySelector('.error-message');
        
        if (errorContainer && errorMessage) {
            // Check if message contains CORS instructions and format accordingly
            if (message.includes('CORS restrictions') || message.includes('python3 -m http.server')) {
                errorMessage.innerHTML = message.replace(/\n/g, '<br>');
            } else {
                errorMessage.textContent = message;
            }
            errorContainer.style.display = 'block';
        }
    },

    /**
     * Hide error message
     */
    hideError() {
        const errorContainer = document.getElementById('error-container');
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
        AppState.error = null;
    }
};

/**
 * Search Component for real-time text filtering and highlighting
 */
const SearchComponent = {
    searchInput: null,
    searchClear: null,
    searchTimeout: null,
    
    /**
     * Initialize the search component
     */
    init() {
        this.searchInput = document.getElementById('search-input');
        this.searchClear = document.querySelector('.search-clear');
        
        if (this.searchInput) {
            this.initializeEventHandlers();
            this.initializeKeyboardShortcuts();
        }
    },

    /**
     * Initialize event handlers for search functionality
     */
    initializeEventHandlers() {
        // Debounced search input handling
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.handleSearch(e.target.value);
            }, 300); // Debounce search by 300ms
        });

        // Clear search on Escape key
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            }
        });

        // Clear button functionality
        if (this.searchClear) {
            this.searchClear.addEventListener('click', () => {
                this.clearSearch();
            });
        }

        // Focus search input when clicking on search container
        const searchContainer = this.searchInput.closest('.search-container');
        if (searchContainer) {
            searchContainer.addEventListener('click', (e) => {
                if (e.target === searchContainer) {
                    this.searchInput.focus();
                }
            });
        }
    },

    /**
     * Initialize keyboard shortcuts for search
     */
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + F to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                this.focusSearch();
            }
            
            // Ctrl/Cmd + K as alternative search shortcut
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.focusSearch();
            }
        });
    },

    /**
     * Focus and select the search input
     */
    focusSearch() {
        if (this.searchInput) {
            this.searchInput.focus();
            this.searchInput.select();
        }
    },

    /**
     * Handle search input with debouncing and filtering
     */
    handleSearch(query) {
        const trimmedQuery = query.trim().toLowerCase();
        
        // Use FilterController if available for coordinated filtering
        if (window.FilterController) {
            window.FilterController.onSearchChanged(trimmedQuery);
        } else {
            // Fallback to direct state management
            AppState.searchQuery = trimmedQuery;
            AppState.currentPage = 1;
            
            DataLoader.filterItems();
            DataLoader.updateResultsCount();
            
            if (window.BibliographyTable && window.BibliographyTable.update) {
                window.BibliographyTable.update();
            }
        }
        
        // Update UI state
        this.updateClearButton();
        this.updateSearchInputState();
        
        // Announce search results to screen readers
        this.announceSearchResults();
    },

    /**
     * Clear search input and reset filters
     */
    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        
        // Use FilterController if available
        if (window.FilterController) {
            window.FilterController.onSearchChanged('');
        } else {
            // Fallback to direct state management
            AppState.searchQuery = '';
            DataLoader.filterItems();
            DataLoader.updateResultsCount();
            
            if (window.BibliographyTable && window.BibliographyTable.update) {
                window.BibliographyTable.update();
            }
        }
        
        this.updateClearButton();
        this.updateSearchInputState();

        // Focus back to search input
        this.searchInput.focus();
    },

    /**
     * Update the visibility of the clear button
     */
    updateClearButton() {
        if (this.searchClear) {
            this.searchClear.style.display = AppState.searchQuery ? 'block' : 'none';
        }
    },

    /**
     * Update search input visual state
     */
    updateSearchInputState() {
        if (this.searchInput) {
            if (AppState.searchQuery) {
                this.searchInput.classList.add('has-query');
            } else {
                this.searchInput.classList.remove('has-query');
            }
        }
    },

    /**
     * Perform full-text search across multiple fields
     */
    performFullTextSearch(item, query) {
        if (!query) return true;

        // Use optimized search if available
        if (window.PerformanceOptimizer && AppState.searchIndex) {
            const itemIndex = AppState.bibliography.indexOf(item);
            const matchingIndices = window.PerformanceOptimizer.performIndexedSearch(query);
            return matchingIndices.has(itemIndex);
        }

        // Fallback to original search
        const searchFields = this.getSearchableFields(item);
        const searchText = searchFields.join(' ').toLowerCase();
        
        // Support for multiple search terms (AND logic)
        const searchTerms = query.split(/\s+/).filter(term => term.length > 0);
        
        return searchTerms.every(term => searchText.includes(term));
    },

    /**
     * Get searchable text fields from an item
     */
    getSearchableFields(item) {
        return [
            item.title || '',
            (item.authors || []).map(author => author.name || author.fullName || '').join(' '),
            item.abstract || '',
            (item.keywords || []).join(' '),
            item.venue || '',
            item.type || ''
        ];
    },

    /**
     * Highlight search terms in text
     */
    highlightSearchTerms(text, query) {
        if (!query || !text) return text;

        const searchTerms = query.split(/\s+/).filter(term => term.length > 0);
        let highlightedText = text;

        searchTerms.forEach(term => {
            const regex = new RegExp(`(${this.escapeRegExp(term)})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark class="search-highlight">$1</mark>');
        });

        return highlightedText;
    },

    /**
     * Escape special regex characters
     */
    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    /**
     * Get search match context (snippet with highlighted terms)
     */
    getSearchContext(text, query, maxLength = 150) {
        if (!query || !text) return text;

        const searchTerms = query.split(/\s+/).filter(term => term.length > 0);
        const lowerText = text.toLowerCase();
        
        // Find the first occurrence of any search term
        let firstMatchIndex = -1;
        let matchedTerm = '';
        
        for (const term of searchTerms) {
            const index = lowerText.indexOf(term.toLowerCase());
            if (index !== -1 && (firstMatchIndex === -1 || index < firstMatchIndex)) {
                firstMatchIndex = index;
                matchedTerm = term;
            }
        }

        if (firstMatchIndex === -1) return text;

        // Calculate context window
        const contextStart = Math.max(0, firstMatchIndex - Math.floor(maxLength / 2));
        const contextEnd = Math.min(text.length, contextStart + maxLength);
        
        let context = text.substring(contextStart, contextEnd);
        
        // Add ellipsis if truncated
        if (contextStart > 0) context = '...' + context;
        if (contextEnd < text.length) context = context + '...';

        return this.highlightSearchTerms(context, query);
    },

    /**
     * Announce search results to screen readers
     */
    announceSearchResults() {
        const resultsCount = AppState.filteredItems.length;
        const totalCount = AppState.bibliography.length;
        
        let message = '';
        if (AppState.searchQuery) {
            message = `Search found ${resultsCount} result${resultsCount !== 1 ? 's' : ''} out of ${totalCount} items`;
        } else {
            message = `Showing all ${totalCount} items`;
        }

        // Create temporary announcement element
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;

        document.body.appendChild(announcement);
        setTimeout(() => {
            if (document.body.contains(announcement)) {
                document.body.removeChild(announcement);
            }
        }, 1000);
    },

    /**
     * Get current search query
     */
    getQuery() {
        return AppState.searchQuery;
    },

    /**
     * Set search query programmatically
     */
    setQuery(query) {
        if (this.searchInput) {
            this.searchInput.value = query;
            this.handleSearch(query);
        }
    }
};

// Make SearchComponent globally available
window.SearchComponent = SearchComponent;

/**
 * Bibliography Table Component for displaying literature items in a sortable, filterable table
 */
const BibliographyTable = {
    table: null,
    tbody: null,
    
    /**
     * Initialize the bibliography table component
     */
    init() {
        this.table = document.getElementById('bibliography-table');
        this.tbody = document.getElementById('bibliography-tbody');
        
        if (this.table && this.tbody) {
            this.initializeEventHandlers();
            this.update();
        }
    },
    
    /**
     * Initialize event handlers for table functionality
     */
    initializeEventHandlers() {
        // Handle column header clicks for sorting
        const headers = this.table.querySelectorAll('th.sortable');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const sortColumn = header.getAttribute('data-sort');
                this.handleSort(sortColumn);
            });
            
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const sortColumn = header.getAttribute('data-sort');
                    this.handleSort(sortColumn);
                }
            });
        });

        // Handle View Details button clicks and title link clicks using event delegation
        this.tbody.addEventListener('click', (e) => {
            const actionButton = e.target.closest('.action-btn');
            const titleLink = e.target.closest('.item-title-link');
            
            if (actionButton) {
                e.preventDefault();
                const itemId = actionButton.getAttribute('data-item-id');
                if (itemId && window.DetailedItemView) {
                    window.DetailedItemView.showItem(itemId);
                }
            } else if (titleLink) {
                e.preventDefault();
                const itemId = titleLink.getAttribute('data-item-id');
                if (itemId && window.DetailedItemView) {
                    window.DetailedItemView.showItem(itemId);
                }
            }
        });
    },
    
    /**
     * Handle column sorting
     */
    handleSort(column) {
        if (AppState.sortColumn === column) {
            AppState.sortDirection = AppState.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            AppState.sortColumn = column;
            AppState.sortDirection = 'asc';
        }
        
        AppState.currentPage = 1; // Reset to first page
        this.update();
        this.updateSortIndicators();
    },
    
    /**
     * Update sort indicators in column headers
     */
    updateSortIndicators() {
        const headers = this.table.querySelectorAll('th.sortable');
        headers.forEach(header => {
            const column = header.getAttribute('data-sort');
            if (column === AppState.sortColumn) {
                header.setAttribute('aria-sort', AppState.sortDirection === 'asc' ? 'ascending' : 'descending');
            } else {
                header.setAttribute('aria-sort', 'none');
            }
        });
    },
    
    /**
     * Update table display with current filtered and sorted data
     */
    update() {
        if (!this.tbody) return;
        
        // Sort the filtered items
        const sortedItems = this.sortItems([...AppState.filteredItems]);
        
        // Apply pagination
        const startIndex = (AppState.currentPage - 1) * AppState.itemsPerPage;
        const endIndex = startIndex + AppState.itemsPerPage;
        const pageItems = sortedItems.slice(startIndex, endIndex);
        
        // Clear existing rows
        this.tbody.innerHTML = '';
        
        if (pageItems.length === 0) {
            this.renderNoResults();
        } else {
            pageItems.forEach(item => {
                const row = this.createTableRow(item);
                this.tbody.appendChild(row);
            });
        }
        
        // Update pagination
        if (window.PaginationComponent) {
            window.PaginationComponent.update(sortedItems.length);
        }
        
        this.updateSortIndicators();
    },
    
    /**
     * Sort items based on current sort settings
     */
    sortItems(items) {
        return items.sort((a, b) => {
            let aValue = this.getSortValue(a, AppState.sortColumn);
            let bValue = this.getSortValue(b, AppState.sortColumn);
            
            // Handle null/undefined values
            if (aValue == null) aValue = '';
            if (bValue == null) bValue = '';
            
            // Convert to strings for comparison
            aValue = String(aValue).toLowerCase();
            bValue = String(bValue).toLowerCase();
            
            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            else if (aValue > bValue) comparison = 1;
            
            return AppState.sortDirection === 'desc' ? -comparison : comparison;
        });
    },
    
    /**
     * Get sort value for an item and column
     */
    getSortValue(item, column) {
        switch (column) {
            case 'title':
                return item.title || '';
            case 'authors':
                return (item.authors || []).map(author => author.name || author.fullName || '').join(', ');
            case 'year':
                return item.year || 0;
            case 'venue':
                return item.venue || '';
            case 'type':
                return item.type || '';
            default:
                return '';
        }
    },
    
    /**
     * Create a table row for an item
     */
    createTableRow(item) {
        const row = document.createElement('tr');
        row.className = 'bibliography-row';
        row.setAttribute('data-item-id', item.id);
        
        // Title column
        const titleCell = document.createElement('td');
        titleCell.innerHTML = `
            <div class="item-title">
                <a href="#" class="item-title-link" data-item-id="${item.id}">
                    ${this.escapeHtml(item.title || 'Untitled')}
                </a>
            </div>
        `;
        row.appendChild(titleCell);
        
        // Authors column
        const authorsCell = document.createElement('td');
        const authors = (item.authors || []).map(author => author.name || author.fullName || 'Unknown').join(', ');
        authorsCell.innerHTML = `<div class="item-authors">${this.escapeHtml(authors || 'Unknown authors')}</div>`;
        row.appendChild(authorsCell);
        
        // Year column
        const yearCell = document.createElement('td');
        yearCell.innerHTML = `<div class="item-year">${item.year || 'Unknown'}</div>`;
        row.appendChild(yearCell);
        
        // Venue column
        const venueCell = document.createElement('td');
        venueCell.innerHTML = `<div class="item-venue">${this.escapeHtml(item.venue || 'Unknown venue')}</div>`;
        row.appendChild(venueCell);
        
        // Type column
        const typeCell = document.createElement('td');
        typeCell.innerHTML = `<div class="item-type">${item.type || 'unknown'}</div>`;
        row.appendChild(typeCell);
        
        // Actions column
        const actionsCell = document.createElement('td');
        actionsCell.innerHTML = `
            <div class="item-actions">
                <button type="button" class="action-btn primary" data-item-id="${item.id}">
                    View Details
                </button>
            </div>
        `;
        row.appendChild(actionsCell);
        
        return row;
    },
    
    /**
     * Render no results message
     */
    renderNoResults() {
        const row = document.createElement('tr');
        row.className = 'no-results-row';
        
        const cell = document.createElement('td');
        cell.colSpan = 6;
        cell.className = 'no-results-cell';
        
        let message = 'No items found';
        if (AppState.searchQuery) {
            message = `No items found matching "${AppState.searchQuery}"`;
        } else if (AppState.currentCollection) {
            const collection = AppState.collections[AppState.currentCollection];
            if (collection) {
                message = `No items found in "${collection.title}"`;
            }
        }
        
        cell.innerHTML = `
            <div class="search-no-results">
                <div class="search-no-results-icon">📚</div>
                <div class="search-no-results-title">No Results</div>
                <div class="search-no-results-message">${message}</div>
                ${AppState.searchQuery || AppState.currentCollection ? `
                <div class="search-suggestions">
                    <button type="button" id="clear-all-filters" class="filter-btn clear-filters">
                        Clear All Filters
                    </button>
                </div>
                ` : ''}
            </div>
        `;
        
        row.appendChild(cell);
        this.tbody.appendChild(row);
        
        // Add event listener for clear filters button
        const clearButton = cell.querySelector('#clear-all-filters');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                if (window.FilterController) {
                    window.FilterController.clearAllFilters();
                }
            });
        }
    },
    
    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Make BibliographyTable globally available
window.BibliographyTable = BibliographyTable;

/**
 * Detailed Item View Component for displaying full item information in a modal
 */
const DetailedItemView = {
    modal: null,
    modalTitle: null,
    modalBody: null,
    
    /**
     * Initialize the detailed item view component
     */
    init() {
        this.modal = document.getElementById('item-modal');
        this.modalTitle = document.getElementById('modal-title');
        this.modalBody = document.querySelector('.modal-body');
        
        if (this.modal) {
            this.initializeEventHandlers();
        }
    },
    
    /**
     * Initialize event handlers for modal functionality
     */
    initializeEventHandlers() {
        // Close modal when clicking close button
        const closeButton = this.modal.querySelector('.modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        // Close modal when clicking overlay
        const overlay = this.modal.querySelector('.modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal && this.modal.getAttribute('aria-hidden') === 'false') {
                this.hideModal();
            }
        });
    },
    
    /**
     * Show detailed information for an item
     */
    showItem(itemId) {
        // Find the item in the bibliography data
        const item = AppState.bibliography.find(bibItem => bibItem.id === itemId);
        
        if (!item) {
            console.error('Item not found:', itemId);
            return;
        }
        
        // Update modal content
        if (this.modalTitle) {
            this.modalTitle.textContent = item.title || 'Untitled';
        }
        
        if (this.modalBody) {
            this.modalBody.innerHTML = this.renderItemDetails(item);
        }
        
        // Show the modal
        this.showModal();
    },
    
    /**
     * Render detailed item information
     */
    renderItemDetails(item) {
        const authors = (item.authors || []).map(author => 
            author.fullName || author.name || `${author.givenName || ''} ${author.surname || ''}`.trim()
        ).join(', ') || 'Unknown authors';
        
        const collections = (item.collections || []).map(colId => {
            const collection = AppState.collections[colId];
            return collection ? collection.title : colId;
        }).join(', ') || 'No collections';
        
        return `
            <div class="item-details">
                <div class="item-detail-section">
                    <h3>Authors</h3>
                    <p>${this.escapeHtml(authors)}</p>
                </div>
                
                ${item.year ? `
                <div class="item-detail-section">
                    <h3>Year</h3>
                    <p>${item.year}</p>
                </div>
                ` : ''}
                
                ${item.venue ? `
                <div class="item-detail-section">
                    <h3>Venue</h3>
                    <p>${this.escapeHtml(item.venue)}</p>
                </div>
                ` : ''}
                
                <div class="item-detail-section">
                    <h3>Type</h3>
                    <p>${this.escapeHtml(item.type || 'Unknown')}</p>
                </div>
                
                ${item.abstract ? `
                <div class="item-detail-section">
                    <h3>Abstract</h3>
                    <p>${this.escapeHtml(item.abstract)}</p>
                </div>
                ` : ''}
                
                ${item.doi ? `
                <div class="item-detail-section">
                    <h3>DOI</h3>
                    <p><a href="${this.escapeHtml(item.doi)}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(item.doi)}</a></p>
                </div>
                ` : ''}
                
                ${item.url ? `
                <div class="item-detail-section">
                    <h3>URL</h3>
                    <p><a href="${this.escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(item.url)}</a></p>
                </div>
                ` : ''}
                
                <div class="item-detail-section">
                    <h3>Collections</h3>
                    <p>${this.escapeHtml(collections)}</p>
                </div>
                
                ${item.keywords && item.keywords.length > 0 ? `
                <div class="item-detail-section">
                    <h3>Keywords</h3>
                    <div class="keywords-list">
                        ${item.keywords.map(keyword => 
                            `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    },
    
    /**
     * Show the modal
     */
    showModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            this.modal.setAttribute('aria-hidden', 'false');
            
            // Focus the close button for accessibility
            const closeButton = this.modal.querySelector('.modal-close');
            if (closeButton) {
                closeButton.focus();
            }
        }
    },
    
    /**
     * Hide the modal
     */
    hideModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
            this.modal.setAttribute('aria-hidden', 'true');
        }
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Make DetailedItemView globally available
window.DetailedItemView = DetailedItemView;

/**
 * Breadcrumb Component for displaying current collection hierarchy path
 */
const BreadcrumbComponent = {
    breadcrumbList: null,
    
    /**
     * Initialize the breadcrumb component
     */
    init() {
        this.breadcrumbList = document.getElementById('breadcrumb-list');
        if (this.breadcrumbList) {
            this.initializeEventHandlers();
            this.updateBreadcrumbs(null); // Initialize with "All Collections"
        }
    },

    /**
     * Initialize event handlers for breadcrumb navigation
     */
    initializeEventHandlers() {
        // Use event delegation for breadcrumb clicks
        this.breadcrumbList.addEventListener('click', (e) => {
            if (e.target.classList.contains('breadcrumb-link')) {
                e.preventDefault();
                const collectionId = e.target.getAttribute('data-collection-id');
                this.handleBreadcrumbClick(collectionId);
            }
        });

        // Keyboard navigation support
        this.breadcrumbList.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('breadcrumb-link')) {
                this.handleBreadcrumbKeyboard(e);
            }
        });

        // Global keyboard shortcuts for breadcrumb navigation
        document.addEventListener('keydown', (e) => {
            // Alt + Up Arrow to navigate to parent collection
            if (e.altKey && e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateToParent();
            }
            // Alt + Home to navigate to root (All Collections)
            else if (e.altKey && e.key === 'Home') {
                e.preventDefault();
                this.handleBreadcrumbClick(null);
            }
        });
    },

    /**
     * Handle keyboard navigation within breadcrumbs
     */
    handleBreadcrumbKeyboard(e) {
        const breadcrumbLinks = Array.from(this.breadcrumbList.querySelectorAll('.breadcrumb-link'));
        const currentIndex = breadcrumbLinks.indexOf(e.target);

        switch (e.key) {
            case 'Enter':
            case ' ':
                e.preventDefault();
                const collectionId = e.target.getAttribute('data-collection-id');
                this.handleBreadcrumbClick(collectionId);
                break;

            case 'ArrowLeft':
                e.preventDefault();
                if (currentIndex > 0) {
                    breadcrumbLinks[currentIndex - 1].focus();
                }
                break;

            case 'ArrowRight':
                e.preventDefault();
                if (currentIndex < breadcrumbLinks.length - 1) {
                    breadcrumbLinks[currentIndex + 1].focus();
                }
                break;

            case 'Home':
                e.preventDefault();
                breadcrumbLinks[0].focus();
                break;

            case 'End':
                e.preventDefault();
                breadcrumbLinks[breadcrumbLinks.length - 1].focus();
                break;
        }
    },

    /**
     * Handle breadcrumb link clicks
     */
    handleBreadcrumbClick(collectionId) {
        // Use FilterController if available for coordinated filtering
        if (window.FilterController) {
            window.FilterController.onCollectionChanged(collectionId || null);
        } else if (window.CollectionTree) {
            // Fallback to direct collection tree selection
            window.CollectionTree.selectCollection(collectionId);
        } else {
            // Direct state management fallback
            AppState.currentCollection = collectionId || null;
            AppState.currentPage = 1;
            
            DataLoader.filterItems();
            DataLoader.updateResultsCount();
            
            if (window.BibliographyTable && window.BibliographyTable.update) {
                window.BibliographyTable.update();
            }
        }

        // Update breadcrumbs to reflect new selection
        this.updateBreadcrumbs(collectionId);
        
        // Announce navigation to screen readers
        this.announceNavigation(collectionId);
    },

    /**
     * Update breadcrumb navigation display
     */
    updateBreadcrumbs(collectionId) {
        if (!this.breadcrumbList) return;

        // Clear existing breadcrumbs
        this.breadcrumbList.innerHTML = '';

        // Always add "All Collections" as root
        const rootItem = this.createBreadcrumbItem('', 'All Collections', !collectionId);
        this.breadcrumbList.appendChild(rootItem);

        // If a specific collection is selected, build the path
        if (collectionId) {
            const path = this.getCollectionPath(collectionId);
            path.forEach((collection, index) => {
                const isLast = index === path.length - 1;
                const breadcrumbItem = this.createBreadcrumbItem(
                    collection.id, 
                    collection.title, 
                    isLast
                );
                this.breadcrumbList.appendChild(breadcrumbItem);
            });
        }

        // Update ARIA attributes for accessibility
        this.updateAccessibilityAttributes();
    },

    /**
     * Create a breadcrumb item element
     */
    createBreadcrumbItem(collectionId, title, isCurrent = false) {
        const breadcrumbItem = document.createElement('li');
        breadcrumbItem.className = 'breadcrumb-item';
        breadcrumbItem.setAttribute('role', 'listitem');

        const breadcrumbLink = document.createElement('a');
        breadcrumbLink.href = '#';
        breadcrumbLink.className = 'breadcrumb-link';
        breadcrumbLink.setAttribute('data-collection-id', collectionId);
        breadcrumbLink.textContent = title;
        breadcrumbLink.setAttribute('tabindex', '0');

        // Add tooltip for long titles
        if (title.length > 25) {
            breadcrumbLink.setAttribute('title', title);
        }

        // Add accessibility attributes
        if (isCurrent) {
            breadcrumbLink.setAttribute('aria-current', 'page');
            breadcrumbLink.classList.add('current');
        } else {
            breadcrumbLink.setAttribute('aria-label', `Navigate to ${title}`);
        }

        // Add keyboard shortcut hints
        if (!isCurrent) {
            const shortcutHint = collectionId === '' ? ' (Alt+Home)' : '';
            breadcrumbLink.setAttribute('aria-label', `Navigate to ${title}${shortcutHint}`);
        }

        breadcrumbItem.appendChild(breadcrumbLink);
        return breadcrumbItem;
    },

    /**
     * Get the path from root to a specific collection
     */
    getCollectionPath(collectionId) {
        const path = [];
        let currentId = collectionId;

        while (currentId && AppState.collections[currentId]) {
            const collection = AppState.collections[currentId];
            path.unshift({
                id: collection.id,
                title: collection.title,
                parentId: collection.parentId
            });
            currentId = collection.parentId;
        }

        return path;
    },

    /**
     * Update accessibility attributes for the breadcrumb navigation
     */
    updateAccessibilityAttributes() {
        if (!this.breadcrumbList) return;

        // Update the breadcrumb navigation aria-label
        const currentCollection = AppState.currentCollection;
        const collection = currentCollection ? AppState.collections[currentCollection] : null;
        const label = collection 
            ? `Breadcrumb navigation, current location: ${collection.title}`
            : 'Breadcrumb navigation, current location: All Collections';
        
        const breadcrumbNav = this.breadcrumbList.closest('.breadcrumb-nav');
        if (breadcrumbNav) {
            breadcrumbNav.setAttribute('aria-label', label);
        }
    },

    /**
     * Announce navigation change to screen readers
     */
    announceNavigation(collectionId) {
        const collection = collectionId ? AppState.collections[collectionId] : null;
        const message = collection 
            ? `Navigated to ${collection.title} collection`
            : 'Navigated to all collections';

        // Create temporary announcement element
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;

        document.body.appendChild(announcement);
        setTimeout(() => {
            if (document.body.contains(announcement)) {
                document.body.removeChild(announcement);
            }
        }, 1000);
    },

    /**
     * Get current breadcrumb path as text
     */
    getCurrentPath() {
        if (!AppState.currentCollection) {
            return 'All Collections';
        }

        const path = this.getCollectionPath(AppState.currentCollection);
        const pathNames = ['All Collections', ...path.map(c => c.title)];
        return pathNames.join(' › ');
    },

    /**
     * Navigate to parent collection
     */
    navigateToParent() {
        if (!AppState.currentCollection) return;

        const collection = AppState.collections[AppState.currentCollection];
        if (collection && collection.parentId) {
            this.handleBreadcrumbClick(collection.parentId);
        } else {
            // Navigate to root (All Collections)
            this.handleBreadcrumbClick(null);
        }
    },

    /**
     * Get breadcrumb data for URL sharing
     */
    getBreadcrumbData() {
        return {
            currentCollection: AppState.currentCollection,
            path: AppState.currentCollection ? this.getCollectionPath(AppState.currentCollection) : []
        };
    },

    /**
     * Set breadcrumb state from URL or external data
     */
    setBreadcrumbState(collectionId) {
        this.updateBreadcrumbs(collectionId);
    },

    /**
     * Get navigation suggestions based on current location
     */
    getNavigationSuggestions() {
        if (!AppState.currentCollection) {
            return {
                canGoUp: false,
                siblings: [],
                children: this.getTopLevelCollections()
            };
        }

        const currentCollection = AppState.collections[AppState.currentCollection];
        if (!currentCollection) {
            return { canGoUp: false, siblings: [], children: [] };
        }

        return {
            canGoUp: !!currentCollection.parentId,
            siblings: this.getSiblingCollections(AppState.currentCollection),
            children: this.getChildCollections(AppState.currentCollection)
        };
    },

    /**
     * Get top-level collections
     */
    getTopLevelCollections() {
        return AppState.collectionTree.map(id => ({
            id,
            title: AppState.collections[id]?.title || 'Unknown Collection'
        }));
    },

    /**
     * Get sibling collections of the current collection
     */
    getSiblingCollections(collectionId) {
        const collection = AppState.collections[collectionId];
        if (!collection || !collection.parentId) {
            return this.getTopLevelCollections().filter(c => c.id !== collectionId);
        }

        const parent = AppState.collections[collection.parentId];
        if (!parent || !parent.children) return [];

        return parent.children
            .filter(id => id !== collectionId)
            .map(id => ({
                id,
                title: AppState.collections[id]?.title || 'Unknown Collection'
            }));
    },

    /**
     * Get child collections of the current collection
     */
    getChildCollections(collectionId) {
        const collection = AppState.collections[collectionId];
        if (!collection || !collection.children) return [];

        return collection.children.map(id => ({
            id,
            title: AppState.collections[id]?.title || 'Unknown Collection'
        }));
    },

    /**
     * Check if breadcrumb navigation is available
     */
    isNavigationAvailable() {
        return !!(this.breadcrumbList && AppState.collections && Object.keys(AppState.collections).length > 0);
    }
};

// Make BreadcrumbComponent globally available
window.BreadcrumbComponent = BreadcrumbComponent;

/**
 * Performance Optimization Module
 */
const PerformanceOptimizer = {
    /**
     * Initialize performance optimizations
     */
    init() {
        this.initializeSearchIndex();
        this.initializeVirtualScrolling();
        this.initializeLazyLoading();
        this.setupPerformanceMonitoring();
    },

    /**
     * Create search index for faster text searching
     */
    initializeSearchIndex() {
        if (!AppState.bibliography.length) return;

        console.time('Search Index Creation');
        
        const index = new Map();
        
        AppState.bibliography.forEach((item, itemIndex) => {
            const searchableText = this.getSearchableText(item).toLowerCase();
            const words = searchableText.split(/\s+/).filter(word => word.length > 2);
            
            // Create word-based index
            words.forEach(word => {
                if (!index.has(word)) {
                    index.set(word, new Set());
                }
                index.get(word).add(itemIndex);
            });
            
            // Create n-gram index for partial matches
            for (let i = 0; i < searchableText.length - 2; i++) {
                const trigram = searchableText.substr(i, 3);
                if (!index.has(trigram)) {
                    index.set(trigram, new Set());
                }
                index.get(trigram).add(itemIndex);
            }
        });

        AppState.searchIndex = index;
        console.timeEnd('Search Index Creation');
        console.log(`Search index created with ${index.size} entries`);
    },

    /**
     * Get searchable text from an item
     */
    getSearchableText(item) {
        return [
            item.title || '',
            (item.authors || []).map(author => author.name || author.fullName || '').join(' '),
            item.abstract || '',
            (item.keywords || []).join(' '),
            item.venue || '',
            item.type || ''
        ].join(' ');
    },

    /**
     * Perform optimized search using the index
     */
    performIndexedSearch(query) {
        if (!AppState.searchIndex || !query) {
            return new Set(AppState.bibliography.map((_, index) => index));
        }

        const searchTerms = query.toLowerCase().split(/\s+/).filter(term => term.length > 0);
        let resultIndices = null;

        searchTerms.forEach(term => {
            let termResults = new Set();

            // Exact word matches
            if (AppState.searchIndex.has(term)) {
                AppState.searchIndex.get(term).forEach(index => termResults.add(index));
            }

            // Partial matches using n-grams
            if (term.length >= 3) {
                for (let i = 0; i <= term.length - 3; i++) {
                    const trigram = term.substr(i, 3);
                    if (AppState.searchIndex.has(trigram)) {
                        AppState.searchIndex.get(trigram).forEach(index => {
                            // Verify the full term exists in the item
                            const item = AppState.bibliography[index];
                            if (item && this.getSearchableText(item).toLowerCase().includes(term)) {
                                termResults.add(index);
                            }
                        });
                    }
                }
            }

            // Intersection with previous results (AND logic)
            if (resultIndices === null) {
                resultIndices = termResults;
            } else {
                resultIndices = new Set([...resultIndices].filter(x => termResults.has(x)));
            }
        });

        return resultIndices || new Set();
    },

    /**
     * Initialize virtual scrolling for large tables
     */
    initializeVirtualScrolling() {
        const tableContainer = document.querySelector('.table-wrapper');
        if (!tableContainer) return;

        // Enable virtual scrolling for large datasets
        const threshold = 200;
        if (AppState.bibliography.length > threshold) {
            AppState.virtualScrolling.enabled = true;
            this.setupVirtualScrollContainer(tableContainer);
        }
    },

    /**
     * Setup virtual scroll container
     */
    setupVirtualScrollContainer(container) {
        const virtualContainer = document.createElement('div');
        virtualContainer.className = 'virtual-scroll-container';
        virtualContainer.style.height = '600px';
        virtualContainer.style.overflow = 'auto';
        virtualContainer.style.position = 'relative';

        const table = container.querySelector('#bibliography-table');
        if (table) {
            // Wrap table in virtual container
            container.insertBefore(virtualContainer, table);
            virtualContainer.appendChild(table);

            // Add scroll listener
            virtualContainer.addEventListener('scroll', () => {
                this.handleVirtualScroll(virtualContainer);
            });

            AppState.virtualScrolling.containerHeight = virtualContainer.clientHeight;
        }
    },

    /**
     * Handle virtual scrolling
     */
    handleVirtualScroll(container) {
        const scrollTop = container.scrollTop;
        const itemHeight = AppState.virtualScrolling.itemHeight;
        const containerHeight = AppState.virtualScrolling.containerHeight;
        const bufferSize = AppState.virtualScrolling.bufferSize;

        const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - bufferSize);
        const visibleEnd = Math.min(
            AppState.filteredItems.length,
            Math.ceil((scrollTop + containerHeight) / itemHeight) + bufferSize
        );

        AppState.virtualScrolling.scrollTop = scrollTop;
        AppState.virtualScrolling.visibleStart = visibleStart;
        AppState.virtualScrolling.visibleEnd = visibleEnd;

        // Update table with only visible items
        this.updateVirtualTable();
    },

    /**
     * Update virtual table with visible items only
     */
    updateVirtualTable() {
        const tbody = document.getElementById('bibliography-tbody');
        if (!tbody || !AppState.virtualScrolling.enabled) return;

        const { visibleStart, visibleEnd } = AppState.virtualScrolling;
        const itemHeight = AppState.virtualScrolling.itemHeight;
        
        // Clear existing rows
        tbody.innerHTML = '';

        // Add spacer for items before visible range
        if (visibleStart > 0) {
            const topSpacer = document.createElement('tr');
            topSpacer.style.height = `${visibleStart * itemHeight}px`;
            topSpacer.innerHTML = '<td colspan="6"></td>';
            tbody.appendChild(topSpacer);
        }

        // Render visible items
        const sortedItems = BibliographyTable.sortItems(AppState.filteredItems);
        for (let i = visibleStart; i < visibleEnd; i++) {
            const item = sortedItems[i];
            if (item) {
                const row = BibliographyTable.createTableRow(item, i);
                tbody.appendChild(row);
            }
        }

        // Add spacer for items after visible range
        if (visibleEnd < AppState.filteredItems.length) {
            const bottomSpacer = document.createElement('tr');
            const remainingItems = AppState.filteredItems.length - visibleEnd;
            bottomSpacer.style.height = `${remainingItems * itemHeight}px`;
            bottomSpacer.innerHTML = '<td colspan="6"></td>';
            tbody.appendChild(bottomSpacer);
        }
    },

    /**
     * Initialize lazy loading for large collections
     */
    initializeLazyLoading() {
        if (!AppState.lazyLoading.enabled) return;

        // Setup intersection observer for lazy loading
        this.setupIntersectionObserver();
    },

    /**
     * Setup intersection observer for lazy loading
     */
    setupIntersectionObserver() {
        if (!window.IntersectionObserver) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadChunk(entry.target);
                }
            });
        }, {
            rootMargin: '100px'
        });

        this.lazyLoadObserver = observer;
    },

    /**
     * Load a chunk of data lazily
     */
    loadChunk(element) {
        const chunkId = element.dataset.chunkId;
        if (!chunkId || AppState.lazyLoading.loadedChunks.has(chunkId)) return;

        console.log(`Lazy loading chunk: ${chunkId}`);
        
        // Mark chunk as loaded
        AppState.lazyLoading.loadedChunks.add(chunkId);
        
        // Load chunk data (simulate async loading)
        setTimeout(() => {
            this.renderChunk(element, chunkId);
        }, 50);
    },

    /**
     * Render a lazy-loaded chunk
     */
    renderChunk(element, chunkId) {
        const chunkIndex = parseInt(chunkId);
        const startIndex = chunkIndex * AppState.lazyLoading.chunkSize;
        const endIndex = Math.min(startIndex + AppState.lazyLoading.chunkSize, AppState.filteredItems.length);
        
        const sortedItems = BibliographyTable.sortItems(AppState.filteredItems);
        const chunkItems = sortedItems.slice(startIndex, endIndex);
        
        // Replace placeholder with actual content
        element.innerHTML = '';
        chunkItems.forEach((item, index) => {
            const row = BibliographyTable.createTableRow(item, startIndex + index);
            element.appendChild(row);
        });
        
        element.classList.remove('lazy-chunk');
        element.classList.add('loaded-chunk');
    },

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor search performance
        this.monitorSearchPerformance();
        
        // Monitor rendering performance
        this.monitorRenderingPerformance();
        
        // Monitor memory usage
        this.monitorMemoryUsage();
    },

    /**
     * Monitor search performance
     */
    monitorSearchPerformance() {
        const originalSearch = SearchComponent.performFullTextSearch;
        
        SearchComponent.performFullTextSearch = (item, query) => {
            const start = performance.now();
            const result = this.performIndexedSearch(query).has(AppState.bibliography.indexOf(item));
            const end = performance.now();
            
            if (end - start > 10) {
                console.warn(`Slow search detected: ${end - start}ms for query "${query}"`);
            }
            
            return result;
        };
    },

    /**
     * Monitor rendering performance
     */
    monitorRenderingPerformance() {
        const originalUpdate = BibliographyTable.update;
        
        BibliographyTable.update = function() {
            const start = performance.now();
            
            if (AppState.virtualScrolling.enabled) {
                PerformanceOptimizer.updateVirtualTable();
            } else {
                originalUpdate.call(this);
            }
            
            const end = performance.now();
            
            if (end - start > 100) {
                console.warn(`Slow table update: ${end - start}ms`);
            }
        };
    },

    /**
     * Monitor memory usage
     */
    monitorMemoryUsage() {
        if (!performance.memory) return;

        setInterval(() => {
            const memory = performance.memory;
            const usedMB = Math.round(memory.usedJSHeapSize / 1048576);
            const limitMB = Math.round(memory.jsHeapSizeLimit / 1048576);
            
            if (usedMB > limitMB * 0.8) {
                console.warn(`High memory usage: ${usedMB}MB / ${limitMB}MB`);
                this.optimizeMemoryUsage();
            }
        }, 30000); // Check every 30 seconds
    },

    /**
     * Optimize memory usage when needed
     */
    optimizeMemoryUsage() {
        // Clear unused search results
        if (AppState.searchIndex && AppState.searchIndex.size > 10000) {
            console.log('Optimizing search index...');
            this.initializeSearchIndex();
        }
        
        // Clear DOM elements outside viewport
        if (AppState.virtualScrolling.enabled) {
            this.cleanupVirtualScrollDOM();
        }
    },

    /**
     * Cleanup virtual scroll DOM elements
     */
    cleanupVirtualScrollDOM() {
        const tbody = document.getElementById('bibliography-tbody');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr:not([style*="height"])');
        const { visibleStart, visibleEnd } = AppState.virtualScrolling;
        
        rows.forEach((row, index) => {
            const actualIndex = visibleStart + index;
            if (actualIndex < visibleStart - 10 || actualIndex > visibleEnd + 10) {
                row.remove();
            }
        });
    },

    /**
     * Debounce function for performance optimization
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function for performance optimization
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Make PerformanceOptimizer globally available
window.PerformanceOptimizer = PerformanceOptimizer;

/**
 * Filter Controller for managing combined collection and search filters
 */
const FilterController = {
    /**
     * Initialize the filter controller
     */
    init() {
        this.initializeURLParameters();
        this.initializeFilterControls();
        this.applyInitialFilters();
    },

    /**
     * Initialize URL parameter handling for shareable views
     */
    initializeURLParameters() {
        // Listen for browser back/forward navigation
        window.addEventListener('popstate', (e) => {
            this.loadFiltersFromURL();
        });

        // Update URL when filters change
        this.setupFilterChangeListeners();
    },

    /**
     * Setup listeners for filter changes to update URL
     */
    setupFilterChangeListeners() {
        // Listen for search changes
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                // Debounce URL updates
                clearTimeout(this.urlUpdateTimeout);
                this.urlUpdateTimeout = setTimeout(() => {
                    this.updateURL();
                }, 500);
            });
        }
    },

    /**
     * Apply initial filters from URL parameters
     */
    applyInitialFilters() {
        this.loadFiltersFromURL();
    },

    /**
     * Load and apply filters from URL parameters
     */
    loadFiltersFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Load search query
        const searchQuery = urlParams.get('search') || '';
        if (searchQuery && window.SearchComponent) {
            window.SearchComponent.setQuery(searchQuery);
        }

        // Load collection filter
        const collectionId = urlParams.get('collection') || '';
        if (collectionId && window.CollectionTree) {
            window.CollectionTree.selectCollection(collectionId);
        }

        // Load pagination
        const page = parseInt(urlParams.get('page')) || 1;
        if (page > 1) {
            AppState.currentPage = page;
        }

        // Load sort settings
        const sortColumn = urlParams.get('sort') || 'title';
        const sortDirection = urlParams.get('dir') || 'asc';
        if (sortColumn && sortDirection) {
            AppState.sortColumn = sortColumn;
            AppState.sortDirection = sortDirection;
        }
    },

    /**
     * Update URL with current filter state
     */
    updateURL() {
        const params = new URLSearchParams();

        // Add search query
        if (AppState.searchQuery) {
            params.set('search', AppState.searchQuery);
        }

        // Add collection filter
        if (AppState.currentCollection) {
            params.set('collection', AppState.currentCollection);
        }

        // Add pagination (only if not on first page)
        if (AppState.currentPage > 1) {
            params.set('page', AppState.currentPage.toString());
        }

        // Add sort settings (only if not default)
        if (AppState.sortColumn !== 'title' || AppState.sortDirection !== 'asc') {
            params.set('sort', AppState.sortColumn);
            params.set('dir', AppState.sortDirection);
        }

        // Update URL without triggering page reload
        const newURL = params.toString() ? 
            `${window.location.pathname}?${params.toString()}` : 
            window.location.pathname;
        
        window.history.replaceState(null, '', newURL);
    },

    /**
     * Apply multiple filters simultaneously
     */
    applyFilters(filters = {}) {
        let filtersChanged = false;

        // Apply search filter
        if (filters.hasOwnProperty('search')) {
            const newSearch = filters.search || '';
            if (AppState.searchQuery !== newSearch) {
                AppState.searchQuery = newSearch;
                filtersChanged = true;
                
                // Update search input
                const searchInput = document.getElementById('search-input');
                if (searchInput && searchInput.value !== newSearch) {
                    searchInput.value = newSearch;
                }
            }
        }

        // Apply collection filter
        if (filters.hasOwnProperty('collection')) {
            const newCollection = filters.collection || null;
            if (AppState.currentCollection !== newCollection) {
                AppState.currentCollection = newCollection;
                filtersChanged = true;
            }
        }

        // Apply sort settings
        if (filters.hasOwnProperty('sort')) {
            if (AppState.sortColumn !== filters.sort) {
                AppState.sortColumn = filters.sort;
                filtersChanged = true;
            }
        }

        if (filters.hasOwnProperty('direction')) {
            if (AppState.sortDirection !== filters.direction) {
                AppState.sortDirection = filters.direction;
                filtersChanged = true;
            }
        }

        // Reset pagination when filters change
        if (filtersChanged && !filters.hasOwnProperty('page')) {
            AppState.currentPage = 1;
        }

        // Apply page filter
        if (filters.hasOwnProperty('page')) {
            const newPage = Math.max(1, parseInt(filters.page) || 1);
            if (AppState.currentPage !== newPage) {
                AppState.currentPage = newPage;
                filtersChanged = true;
            }
        }

        if (filtersChanged) {
            this.refreshView();
            this.updateURL();
        }

        return filtersChanged;
    },

    /**
     * Clear all filters
     */
    clearAllFilters() {
        this.applyFilters({
            search: '',
            collection: null,
            sort: 'title',
            direction: 'asc',
            page: 1
        });

        // Update UI components
        if (window.SearchComponent) {
            window.SearchComponent.clearSearch();
        }

        if (window.CollectionTree) {
            window.CollectionTree.selectCollection('');
        }
    },

    /**
     * Get current filter state
     */
    getCurrentFilters() {
        return {
            search: AppState.searchQuery,
            collection: AppState.currentCollection,
            sort: AppState.sortColumn,
            direction: AppState.sortDirection,
            page: AppState.currentPage
        };
    },

    /**
     * Check if any filters are active
     */
    hasActiveFilters() {
        return !!(AppState.searchQuery || 
                 AppState.currentCollection || 
                 AppState.sortColumn !== 'title' || 
                 AppState.sortDirection !== 'asc');
    },

    /**
     * Get shareable URL for current filter state
     */
    getShareableURL() {
        const params = new URLSearchParams();

        if (AppState.searchQuery) {
            params.set('search', AppState.searchQuery);
        }

        if (AppState.currentCollection) {
            params.set('collection', AppState.currentCollection);
        }

        if (AppState.sortColumn !== 'title' || AppState.sortDirection !== 'asc') {
            params.set('sort', AppState.sortColumn);
            params.set('dir', AppState.sortDirection);
        }

        return params.toString() ? 
            `${window.location.origin}${window.location.pathname}?${params.toString()}` : 
            `${window.location.origin}${window.location.pathname}`;
    },

    /**
     * Refresh the view with current filters
     */
    refreshView() {
        // Filter items
        DataLoader.filterItems();
        DataLoader.updateResultsCount();

        // Update bibliography table
        if (window.BibliographyTable) {
            if (window.BibliographyTable.updateSortIndicators) {
                window.BibliographyTable.updateSortIndicators();
            }
            if (window.BibliographyTable.update) {
                window.BibliographyTable.update();
            }
        }

        // Update collection tree selection
        if (window.CollectionTree && window.CollectionTree.updateSelection) {
            window.CollectionTree.updateSelection(AppState.currentCollection);
        }

        // Update search component state
        if (window.SearchComponent) {
            window.SearchComponent.updateClearButton();
            window.SearchComponent.updateSearchInputState();
        }

        // Update breadcrumb navigation
        if (window.BreadcrumbComponent) {
            window.BreadcrumbComponent.updateBreadcrumbs(AppState.currentCollection);
        }

        // Update filter controls visibility
        this.updateFilterControlsVisibility();
    },

    /**
     * Handle collection selection from tree
     */
    onCollectionSelected(collectionId) {
        this.applyFilters({ 
            collection: collectionId,
            page: 1 
        });
    },

    /**
     * Handle collection change from breadcrumb navigation
     */
    onCollectionChanged(collectionId) {
        this.applyFilters({ 
            collection: collectionId,
            page: 1 
        });

        // Update breadcrumb display
        if (window.BreadcrumbComponent) {
            window.BreadcrumbComponent.updateBreadcrumbs(collectionId);
        }
    },

    /**
     * Handle search query change
     */
    onSearchChanged(query) {
        this.applyFilters({ 
            search: query,
            page: 1 
        });
    },

    /**
     * Handle sort change
     */
    onSortChanged(column, direction) {
        this.applyFilters({ 
            sort: column,
            direction: direction,
            page: 1 
        });
    },

    /**
     * Handle page change
     */
    onPageChanged(page) {
        this.applyFilters({ page: page });
    },

    /**
     * Initialize filter control buttons
     */
    initializeFilterControls() {
        const clearButton = document.getElementById('clear-filters');
        const shareButton = document.getElementById('share-filters');

        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }

        if (shareButton) {
            shareButton.addEventListener('click', () => {
                this.shareCurrentView();
            });
        }
    },

    /**
     * Update visibility of filter controls based on active filters
     */
    updateFilterControlsVisibility() {
        const filterControls = document.getElementById('filter-controls');
        if (filterControls) {
            const hasFilters = this.hasActiveFilters();
            filterControls.style.display = hasFilters ? 'flex' : 'none';
        }
    },

    /**
     * Share current view by copying URL to clipboard
     */
    async shareCurrentView() {
        const shareableURL = this.getShareableURL();
        
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(shareableURL);
                this.showShareSuccess('URL copied to clipboard!');
            } else {
                // Fallback for older browsers or non-secure contexts
                this.fallbackCopyToClipboard(shareableURL);
            }
        } catch (error) {
            console.error('Failed to copy URL:', error);
            this.showShareError('Failed to copy URL. Please copy manually: ' + shareableURL);
        }
    },

    /**
     * Fallback method to copy text to clipboard
     */
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                this.showShareSuccess('URL copied to clipboard!');
            } else {
                this.showShareError('Failed to copy URL. Please copy manually: ' + text);
            }
        } catch (error) {
            this.showShareError('Failed to copy URL. Please copy manually: ' + text);
        } finally {
            document.body.removeChild(textArea);
        }
    },

    /**
     * Show success message for sharing
     */
    showShareSuccess(message) {
        this.showTemporaryMessage(message, 'success');
    },

    /**
     * Show error message for sharing
     */
    showShareError(message) {
        this.showTemporaryMessage(message, 'error');
    },

    /**
     * Show temporary message to user
     */
    showTemporaryMessage(message, type = 'info') {
        // Create temporary message element
        const messageEl = document.createElement('div');
        messageEl.className = `temporary-message temporary-message-${type}`;
        messageEl.textContent = message;
        messageEl.setAttribute('role', 'status');
        messageEl.setAttribute('aria-live', 'polite');

        // Position it near the share button
        const shareButton = document.getElementById('share-filters');
        if (shareButton) {
            const rect = shareButton.getBoundingClientRect();
            messageEl.style.position = 'fixed';
            messageEl.style.top = `${rect.bottom + 8}px`;
            messageEl.style.left = `${rect.left}px`;
            messageEl.style.zIndex = '1000';
        }

        document.body.appendChild(messageEl);

        // Remove after 3 seconds
        setTimeout(() => {
            if (document.body.contains(messageEl)) {
                document.body.removeChild(messageEl);
            }
        }, 3000);
    }
};

// Make FilterController globally available
window.FilterController = FilterController;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    DataLoader.init();
});
/*
*
 * Collection Tree Navigation Component
 */
const CollectionTree = {
    /**
     * Initialize the collection tree component
     */
    init() {
        this.render();
        this.initializeEventHandlers();
    },

    /**
     * Render the collection tree in the sidebar
     */
    render() {
        const treeContainer = document.getElementById('collection-tree');
        if (!treeContainer) return;

        // Clear existing content
        treeContainer.innerHTML = '';

        // Create "All Collections" root item
        const allCollectionsItem = this.createTreeItem({
            id: '',
            title: 'All Collections',
            itemCount: AppState.bibliography.length,
            isRoot: true
        });
        treeContainer.appendChild(allCollectionsItem);

        // Render collection tree
        if (AppState.collectionTree.length > 0) {
            const treeList = document.createElement('ul');
            treeList.className = 'collection-list';
            treeList.setAttribute('role', 'group');
            
            AppState.collectionTree.forEach(collectionId => {
                const treeItem = this.renderCollectionNode(collectionId);
                if (treeItem) {
                    treeList.appendChild(treeItem);
                }
            });
            
            treeContainer.appendChild(treeList);
        }
    },

    /**
     * Render a single collection node and its children
     */
    renderCollectionNode(collectionId, level = 0) {
        const collection = AppState.collections[collectionId];
        if (!collection) return null;

        const listItem = document.createElement('li');
        listItem.className = 'collection-item';
        listItem.setAttribute('role', 'treeitem');
        listItem.setAttribute('data-collection-id', collectionId);
        listItem.setAttribute('data-level', level);

        const hasChildren = collection.children && collection.children.length > 0;
        if (hasChildren) {
            listItem.setAttribute('aria-expanded', 'false');
        }

        // Create the collection button/link
        const collectionButton = this.createTreeItem(collection, hasChildren, level);
        listItem.appendChild(collectionButton);

        // Create children container if there are children
        if (hasChildren) {
            const childrenList = document.createElement('ul');
            childrenList.className = 'collection-children';
            childrenList.setAttribute('role', 'group');
            childrenList.style.display = 'none';

            collection.children.forEach(childId => {
                const childItem = this.renderCollectionNode(childId, level + 1);
                if (childItem) {
                    childrenList.appendChild(childItem);
                }
            });

            listItem.appendChild(childrenList);
        }

        return listItem;
    },

    /**
     * Create a tree item element (button or link)
     */
    createTreeItem(collection, hasChildren = false, level = 0) {
        const item = document.createElement('div');
        item.className = 'collection-tree-item';
        
        // Add indentation for nested levels
        if (level > 0) {
            item.style.paddingLeft = `${level * 20 + 12}px`;
        }

        // Expand/collapse button for items with children
        if (hasChildren) {
            const expandButton = document.createElement('button');
            expandButton.type = 'button';
            expandButton.className = 'collection-expand';
            expandButton.setAttribute('aria-label', `Expand ${collection.title}`);
            expandButton.innerHTML = '<span class="expand-icon" aria-hidden="true">▶</span>';
            item.appendChild(expandButton);
        } else if (level > 0) {
            // Add spacing for items without children to align with expanded items
            const spacer = document.createElement('span');
            spacer.className = 'collection-spacer';
            spacer.setAttribute('aria-hidden', 'true');
            item.appendChild(spacer);
        }

        // Collection selection button
        const selectButton = document.createElement('button');
        selectButton.type = 'button';
        selectButton.className = 'collection-select';
        selectButton.setAttribute('data-collection-id', collection.id || '');
        selectButton.setAttribute('aria-label', `Select ${collection.title} collection`);

        // Collection title and count
        const titleSpan = document.createElement('span');
        titleSpan.className = 'collection-title';
        titleSpan.textContent = collection.title;

        const countSpan = document.createElement('span');
        countSpan.className = 'collection-count';
        countSpan.textContent = `(${collection.itemCount || 0})`;
        countSpan.setAttribute('aria-label', `${collection.itemCount || 0} items`);

        selectButton.appendChild(titleSpan);
        selectButton.appendChild(countSpan);
        item.appendChild(selectButton);

        return item;
    },

    /**
     * Initialize event handlers for tree interaction
     */
    initializeEventHandlers() {
        const treeContainer = document.getElementById('collection-tree');
        if (!treeContainer) return;

        // Handle collection selection
        treeContainer.addEventListener('click', (e) => {
            const selectButton = e.target.closest('.collection-select');
            const expandButton = e.target.closest('.collection-expand');

            if (selectButton) {
                e.preventDefault();
                const collectionId = selectButton.getAttribute('data-collection-id');
                this.selectCollection(collectionId);
            } else if (expandButton) {
                e.preventDefault();
                const treeItem = expandButton.closest('.collection-item');
                this.toggleExpansion(treeItem);
            }
        });

        // Handle keyboard navigation
        treeContainer.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        // Initialize sidebar toggle
        this.initializeSidebarToggle();
    },

    /**
     * Handle keyboard navigation in the tree
     */
    handleKeyboardNavigation(e) {
        const focusedElement = document.activeElement;
        const treeItems = Array.from(document.querySelectorAll('.collection-select, .collection-expand'));
        const currentIndex = treeItems.indexOf(focusedElement);

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                const nextIndex = Math.min(currentIndex + 1, treeItems.length - 1);
                treeItems[nextIndex]?.focus();
                break;

            case 'ArrowUp':
                e.preventDefault();
                const prevIndex = Math.max(currentIndex - 1, 0);
                treeItems[prevIndex]?.focus();
                break;

            case 'ArrowRight':
                if (focusedElement.classList.contains('collection-expand')) {
                    e.preventDefault();
                    const treeItem = focusedElement.closest('.collection-item');
                    this.expandCollection(treeItem);
                }
                break;

            case 'ArrowLeft':
                if (focusedElement.classList.contains('collection-expand')) {
                    e.preventDefault();
                    const treeItem = focusedElement.closest('.collection-item');
                    this.collapseCollection(treeItem);
                }
                break;

            case 'Enter':
            case ' ':
                e.preventDefault();
                focusedElement.click();
                break;
        }
    },

    /**
     * Select a collection and update the view
     */
    selectCollection(collectionId) {
        const normalizedId = collectionId || null;
        
        // Use FilterController if available for coordinated filtering
        if (window.FilterController) {
            window.FilterController.onCollectionSelected(normalizedId);
        } else {
            // Fallback to direct state management
            AppState.currentCollection = normalizedId;
            AppState.currentPage = 1;
            
            DataLoader.filterItems();
            DataLoader.updateResultsCount();
            
            if (window.BibliographyTable && window.BibliographyTable.update) {
                window.BibliographyTable.update();
            }
        }

        // Update visual selection
        this.updateSelection(normalizedId);

        // Update breadcrumbs using BreadcrumbComponent
        if (window.BreadcrumbComponent) {
            window.BreadcrumbComponent.updateBreadcrumbs(normalizedId);
        }

        // Announce selection to screen readers
        this.announceSelection(normalizedId);
    },

    /**
     * Update visual selection state in the tree
     */
    updateSelection(selectedId) {
        // Remove previous selection
        const previousSelected = document.querySelector('.collection-select.selected');
        if (previousSelected) {
            previousSelected.classList.remove('selected');
            previousSelected.setAttribute('aria-selected', 'false');
        }

        // Add new selection
        const newSelected = document.querySelector(`[data-collection-id="${selectedId || ''}"]`);
        if (newSelected) {
            newSelected.classList.add('selected');
            newSelected.setAttribute('aria-selected', 'true');
        }
    },

    /**
     * Toggle expansion state of a collection item
     */
    toggleExpansion(treeItem) {
        if (!treeItem) return;

        const isExpanded = treeItem.getAttribute('aria-expanded') === 'true';
        if (isExpanded) {
            this.collapseCollection(treeItem);
        } else {
            this.expandCollection(treeItem);
        }
    },

    /**
     * Expand a collection to show its children
     */
    expandCollection(treeItem) {
        if (!treeItem) return;

        const childrenList = treeItem.querySelector('.collection-children');
        const expandButton = treeItem.querySelector('.collection-expand');
        const expandIcon = expandButton?.querySelector('.expand-icon');

        if (childrenList) {
            childrenList.style.display = 'block';
            treeItem.setAttribute('aria-expanded', 'true');
            
            if (expandIcon) {
                expandIcon.textContent = '▼';
            }
            if (expandButton) {
                const collectionTitle = treeItem.querySelector('.collection-title')?.textContent || 'collection';
                expandButton.setAttribute('aria-label', `Collapse ${collectionTitle}`);
            }
        }
    },

    /**
     * Collapse a collection to hide its children
     */
    collapseCollection(treeItem) {
        if (!treeItem) return;

        const childrenList = treeItem.querySelector('.collection-children');
        const expandButton = treeItem.querySelector('.collection-expand');
        const expandIcon = expandButton?.querySelector('.expand-icon');

        if (childrenList) {
            childrenList.style.display = 'none';
            treeItem.setAttribute('aria-expanded', 'false');
            
            if (expandIcon) {
                expandIcon.textContent = '▶';
            }
            if (expandButton) {
                const collectionTitle = treeItem.querySelector('.collection-title')?.textContent || 'collection';
                expandButton.setAttribute('aria-label', `Expand ${collectionTitle}`);
            }
        }
    },



    /**
     * Announce selection change to screen readers
     */
    announceSelection(collectionId) {
        const collection = collectionId ? AppState.collections[collectionId] : null;
        const message = collection 
            ? `Selected ${collection.title} collection with ${collection.itemCount || 0} items`
            : 'Selected all collections';

        // Create temporary announcement element
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;

        document.body.appendChild(announcement);
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    },

    /**
     * Initialize sidebar toggle functionality
     */
    initializeSidebarToggle() {
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        const sidebar = document.querySelector('.sidebar');

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', () => {
                const isCollapsed = sidebar.classList.contains('collapsed');
                
                if (isCollapsed) {
                    sidebar.classList.remove('collapsed');
                    sidebarToggle.setAttribute('aria-label', 'Collapse collection sidebar');
                } else {
                    sidebar.classList.add('collapsed');
                    sidebarToggle.setAttribute('aria-label', 'Expand collection sidebar');
                }
            });
        }
    }
};

// Make CollectionTree globally available
window.CollectionTree = CollectionTree;
