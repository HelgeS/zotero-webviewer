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
    error: null
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
            throw new Error(`Data loading failed: ${error.message}`);
        }
    },

    /**
     * Initialize UI components and event handlers
     */
    initializeUI() {
        // Initialize filter controller first
        if (window.FilterController) {
            window.FilterController.init();
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
            (item.authors || []).map(author => author.fullName || '').join(' '),
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
            errorMessage.textContent = message;
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
            (item.authors || []).map(author => author.fullName || '').join(' '),
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
 * Filter Controller for managing combined collection and search filters
 */
const FilterController = {
    /**
     * Initialize the filter controller
     */
    init() {
        this.initializeURLParameters();
        this.initializeEventHandlers();
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

        // Update breadcrumbs
        this.updateBreadcrumbs(normalizedId);

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
     * Update breadcrumb navigation
     */
    updateBreadcrumbs(collectionId) {
        const breadcrumbList = document.getElementById('breadcrumb-list');
        if (!breadcrumbList) return;

        // Clear existing breadcrumbs except the root
        const existingItems = breadcrumbList.querySelectorAll('.breadcrumb-item:not(:first-child)');
        existingItems.forEach(item => item.remove());

        if (!collectionId) {
            // Just show "All Collections"
            return;
        }

        // Build breadcrumb path
        const path = this.getCollectionPath(collectionId);
        path.forEach((collection, index) => {
            const breadcrumbItem = document.createElement('li');
            breadcrumbItem.className = 'breadcrumb-item';

            const breadcrumbLink = document.createElement('a');
            breadcrumbLink.href = '#';
            breadcrumbLink.className = 'breadcrumb-link';
            breadcrumbLink.setAttribute('data-collection-id', collection.id);
            breadcrumbLink.textContent = collection.title;

            breadcrumbItem.appendChild(breadcrumbLink);
            breadcrumbList.appendChild(breadcrumbItem);
        });

        // Add click handlers to breadcrumb links
        breadcrumbList.addEventListener('click', (e) => {
            if (e.target.classList.contains('breadcrumb-link')) {
                e.preventDefault();
                const collectionId = e.target.getAttribute('data-collection-id');
                this.selectCollection(collectionId);
            }
        });
    },

    /**
     * Get the path from root to a specific collection
     */
    getCollectionPath(collectionId) {
        const path = [];
        let currentId = collectionId;

        while (currentId && AppState.collections[currentId]) {
            const collection = AppState.collections[currentId];
            path.unshift(collection);
            currentId = collection.parentId;
        }

        return path;
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
};/**
 
* Bibliography Table Component
 */
const BibliographyTable = {
    /**
     * Initialize the bibliography table component
     */
    init() {
        this.initializeEventHandlers();
        this.initializePagination();
        this.update();
    },

    /**
     * Initialize event handlers for table functionality
     */
    initializeEventHandlers() {
        const table = document.getElementById('bibliography-table');
        if (!table) return;

        // Handle column sorting
        table.addEventListener('click', (e) => {
            const sortableHeader = e.target.closest('.sortable');
            if (sortableHeader) {
                e.preventDefault();
                const sortColumn = sortableHeader.getAttribute('data-sort');
                this.handleSort(sortColumn);
            }
        });

        // Handle keyboard navigation for sortable headers
        table.addEventListener('keydown', (e) => {
            if (e.target.classList.contains('sortable') && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault();
                const sortColumn = e.target.getAttribute('data-sort');
                this.handleSort(sortColumn);
            }
        });

        // Initialize view toggle
        this.initializeViewToggle();
    },  
  /**
     * Handle column sorting
     */
    handleSort(column) {
        let newDirection;
        
        if (AppState.sortColumn === column) {
            // Toggle direction if same column
            newDirection = AppState.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, default to ascending
            newDirection = 'asc';
        }

        // Use FilterController if available for coordinated filtering
        if (window.FilterController) {
            window.FilterController.onSortChanged(column, newDirection);
        } else {
            // Fallback to direct state management
            AppState.sortColumn = column;
            AppState.sortDirection = newDirection;
            AppState.currentPage = 1;
            
            this.updateSortIndicators();
            this.update();
        }
    },

    /**
     * Update sort indicators in table headers
     */
    updateSortIndicators() {
        const headers = document.querySelectorAll('.sortable');
        headers.forEach(header => {
            const column = header.getAttribute('data-sort');
            const indicator = header.querySelector('.sort-indicator');
            
            if (column === AppState.sortColumn) {
                header.setAttribute('aria-sort', AppState.sortDirection === 'asc' ? 'ascending' : 'descending');
                if (indicator) {
                    indicator.textContent = AppState.sortDirection === 'asc' ? '↑' : '↓';
                }
            } else {
                header.setAttribute('aria-sort', 'none');
                if (indicator) {
                    indicator.textContent = '';
                }
            }
        });
    },    /**

     * Sort items based on current sort settings
     */
    sortItems(items) {
        return [...items].sort((a, b) => {
            let aValue, bValue;

            switch (AppState.sortColumn) {
                case 'title':
                    aValue = (a.title || '').toLowerCase();
                    bValue = (b.title || '').toLowerCase();
                    break;
                case 'authors':
                    aValue = (a.authors || []).map(author => author.fullName || '').join(', ').toLowerCase();
                    bValue = (b.authors || []).map(author => author.fullName || '').join(', ').toLowerCase();
                    break;
                case 'year':
                    aValue = a.year || 0;
                    bValue = b.year || 0;
                    break;
                case 'venue':
                    aValue = (a.venue || '').toLowerCase();
                    bValue = (b.venue || '').toLowerCase();
                    break;
                case 'type':
                    aValue = (a.type || '').toLowerCase();
                    bValue = (b.type || '').toLowerCase();
                    break;
                default:
                    return 0;
            }

            let comparison = 0;
            if (aValue < bValue) comparison = -1;
            else if (aValue > bValue) comparison = 1;

            return AppState.sortDirection === 'desc' ? -comparison : comparison;
        });
    },    /**
   
  * Update the table display with current filtered and sorted items
     */
    update() {
        const tbody = document.getElementById('bibliography-tbody');
        if (!tbody) return;

        // Sort the filtered items
        const sortedItems = this.sortItems(AppState.filteredItems);
        
        // Calculate pagination
        const startIndex = (AppState.currentPage - 1) * AppState.itemsPerPage;
        const endIndex = startIndex + AppState.itemsPerPage;
        const pageItems = sortedItems.slice(startIndex, endIndex);

        // Clear existing rows
        tbody.innerHTML = '';

        if (pageItems.length === 0) {
            // Show search-specific empty state
            const emptyRow = document.createElement('tr');
            emptyRow.className = 'empty-row';
            
            let emptyContent = '';
            if (AppState.searchQuery) {
                emptyContent = `
                    <div class="search-no-results">
                        <div class="search-no-results-icon">🔍</div>
                        <div class="search-no-results-title">No results found</div>
                        <div class="search-no-results-message">
                            No items match your search for "<strong>${AppState.searchQuery}</strong>"
                        </div>
                        <div class="search-suggestions">
                            <strong>Try:</strong>
                            <ul>
                                <li>Checking your spelling</li>
                                <li>Using different keywords</li>
                                <li>Searching for author names or publication venues</li>
                                <li>Clearing filters to see all items</li>
                            </ul>
                        </div>
                    </div>
                `;
            } else if (AppState.currentCollection) {
                const collection = AppState.collections[AppState.currentCollection];
                emptyContent = `
                    <div class="search-no-results">
                        <div class="search-no-results-icon">📁</div>
                        <div class="search-no-results-title">Collection is empty</div>
                        <div class="search-no-results-message">
                            The collection "${collection?.title || 'Unknown'}" contains no items.
                        </div>
                    </div>
                `;
            } else {
                emptyContent = `
                    <div class="search-no-results">
                        <div class="search-no-results-icon">📚</div>
                        <div class="search-no-results-title">No items available</div>
                        <div class="search-no-results-message">
                            No bibliography items have been loaded.
                        </div>
                    </div>
                `;
            }
            
            emptyRow.innerHTML = `<td colspan="6" class="empty-cell">${emptyContent}</td>`;
            tbody.appendChild(emptyRow);
        } else {
            // Render items
            pageItems.forEach(item => {
                const row = this.createTableRow(item);
                tbody.appendChild(row);
            });
        }

        // Update pagination
        this.updatePagination(sortedItems.length);
        this.updateSortIndicators();
    }, 
   /**
     * Create a table row for a bibliography item
     */
    createTableRow(item) {
        const row = document.createElement('tr');
        row.className = 'bibliography-row';
        row.setAttribute('data-item-id', item.id);

        const searchQuery = AppState.searchQuery;

        // Title cell with search highlighting
        const titleCell = document.createElement('td');
        titleCell.className = 'title-cell';
        
        const titleContainer = document.createElement('div');
        titleContainer.className = 'item-title';
        
        const titleLink = document.createElement('button');
        titleLink.type = 'button';
        titleLink.className = 'item-title-link';
        
        const titleText = item.title || 'Untitled';
        if (searchQuery && window.SearchComponent) {
            titleLink.innerHTML = window.SearchComponent.highlightSearchTerms(titleText, searchQuery);
        } else {
            titleLink.textContent = titleText;
        }
        
        titleLink.setAttribute('aria-label', `View details for ${titleText}`);
        titleLink.addEventListener('click', () => this.showItemDetails(item));
        titleContainer.appendChild(titleLink);

        // Add search context for abstract if there's a search query
        if (searchQuery && item.abstract && window.SearchComponent) {
            const contextDiv = document.createElement('div');
            contextDiv.className = 'search-context';
            contextDiv.innerHTML = window.SearchComponent.getSearchContext(item.abstract, searchQuery, 120);
            titleContainer.appendChild(contextDiv);
        }

        titleCell.appendChild(titleContainer);

        // Authors cell with search highlighting
        const authorsCell = document.createElement('td');
        authorsCell.className = 'authors-cell';
        const authorsText = (item.authors || []).map(author => author.fullName || '').join(', ') || 'Unknown';
        
        if (searchQuery && window.SearchComponent) {
            authorsCell.innerHTML = window.SearchComponent.highlightSearchTerms(authorsText, searchQuery);
        } else {
            authorsCell.textContent = authorsText;
        }

        // Year cell
        const yearCell = document.createElement('td');
        yearCell.className = 'year-cell';
        yearCell.textContent = item.year || '';

        // Venue cell with search highlighting
        const venueCell = document.createElement('td');
        venueCell.className = 'venue-cell';
        const venueText = item.venue || '';
        
        if (searchQuery && venueText && window.SearchComponent) {
            venueCell.innerHTML = window.SearchComponent.highlightSearchTerms(venueText, searchQuery);
        } else {
            venueCell.textContent = venueText;
        }

        // Type cell
        const typeCell = document.createElement('td');
        typeCell.className = 'type-cell';
        const typeSpan = document.createElement('span');
        typeSpan.className = `item-type item-type-${item.type || 'other'}`;
        typeSpan.textContent = this.formatItemType(item.type);
        typeCell.appendChild(typeSpan);

        // Actions cell
        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions-cell';
        const detailsButton = document.createElement('button');
        detailsButton.type = 'button';
        detailsButton.className = 'action-button details-button';
        detailsButton.textContent = 'Details';
        detailsButton.setAttribute('aria-label', `View details for ${titleText}`);
        detailsButton.addEventListener('click', () => this.showItemDetails(item));
        actionsCell.appendChild(detailsButton);

        row.appendChild(titleCell);
        row.appendChild(authorsCell);
        row.appendChild(yearCell);
        row.appendChild(venueCell);
        row.appendChild(typeCell);
        row.appendChild(actionsCell);

        return row;
    },    /
**
     * Format item type for display
     */
    formatItemType(type) {
        const typeMap = {
            'article': 'Article',
            'book': 'Book',
            'conference': 'Conference',
            'thesis': 'Thesis',
            'other': 'Other'
        };
        return typeMap[type] || 'Other';
    },

    /**
     * Show detailed view of an item (placeholder for modal functionality)
     */
    showItemDetails(item) {
        // This will be implemented in a future task
        console.log('Show details for item:', item.title);
        // For now, just log the item details
        alert(`Details for: ${item.title}\n\nAuthors: ${(item.authors || []).map(a => a.fullName).join(', ')}\nYear: ${item.year || 'Unknown'}\nVenue: ${item.venue || 'Unknown'}\nType: ${this.formatItemType(item.type)}`);
    },

    /**
     * Initialize pagination functionality
     */
    initializePagination() {
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');

        if (prevButton) {
            prevButton.addEventListener('click', () => {
                if (AppState.currentPage > 1) {
                    const newPage = AppState.currentPage - 1;
                    if (window.FilterController) {
                        window.FilterController.onPageChanged(newPage);
                    } else {
                        AppState.currentPage = newPage;
                        this.update();
                    }
                }
            });
        }

        if (nextButton) {
            nextButton.addEventListener('click', () => {
                const totalPages = Math.ceil(AppState.filteredItems.length / AppState.itemsPerPage);
                if (AppState.currentPage < totalPages) {
                    const newPage = AppState.currentPage + 1;
                    if (window.FilterController) {
                        window.FilterController.onPageChanged(newPage);
                    } else {
                        AppState.currentPage = newPage;
                        this.update();
                    }
                }
            });
        }
    },   
 /**
     * Update pagination controls and info
     */
    updatePagination(totalItems) {
        const totalPages = Math.ceil(totalItems / AppState.itemsPerPage);
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');
        const paginationInfo = document.getElementById('pagination-info');
        const pageNumbers = document.querySelector('.page-numbers');

        // Update navigation buttons
        if (prevButton) {
            prevButton.disabled = AppState.currentPage <= 1;
        }
        if (nextButton) {
            nextButton.disabled = AppState.currentPage >= totalPages;
        }

        // Update pagination info
        if (paginationInfo) {
            if (totalItems === 0) {
                paginationInfo.textContent = '';
            } else {
                const startItem = (AppState.currentPage - 1) * AppState.itemsPerPage + 1;
                const endItem = Math.min(AppState.currentPage * AppState.itemsPerPage, totalItems);
                paginationInfo.textContent = `${startItem}-${endItem} of ${totalItems.toLocaleString()}`;
            }
        }

        // Update page numbers
        if (pageNumbers) {
            pageNumbers.innerHTML = '';
            if (totalPages > 1) {
                this.renderPageNumbers(pageNumbers, totalPages);
            }
        }
    },

    /**
     * Render page number buttons
     */
    renderPageNumbers(container, totalPages) {
        const maxVisiblePages = 5;
        let startPage = Math.max(1, AppState.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // Adjust start page if we're near the end
        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // First page and ellipsis
        if (startPage > 1) {
            this.createPageButton(container, 1);
            if (startPage > 2) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '...';
                ellipsis.setAttribute('aria-hidden', 'true');
                container.appendChild(ellipsis);
            }
        }

        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            this.createPageButton(container, i);
        }

        // Last page and ellipsis
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '...';
                ellipsis.setAttribute('aria-hidden', 'true');
                container.appendChild(ellipsis);
            }
            this.createPageButton(container, totalPages);
        }
    },    /**

     * Create a page number button
     */
    createPageButton(container, pageNumber) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'page-number';
        button.textContent = pageNumber;
        button.setAttribute('aria-label', `Go to page ${pageNumber}`);
        
        if (pageNumber === AppState.currentPage) {
            button.classList.add('current');
            button.setAttribute('aria-current', 'page');
        }

        button.addEventListener('click', () => {
            if (window.FilterController) {
                window.FilterController.onPageChanged(pageNumber);
            } else {
                AppState.currentPage = pageNumber;
                this.update();
            }
        });

        container.appendChild(button);
    },

    /**
     * Initialize view toggle functionality
     */
    initializeViewToggle() {
        const viewToggles = document.querySelectorAll('.view-toggle');
        
        viewToggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const view = toggle.getAttribute('data-view');
                this.switchView(view);
            });
        });
    },

    /**
     * Switch between table and card views
     */
    switchView(view) {
        const tableContainer = document.querySelector('.bibliography-container');
        const cardsContainer = document.getElementById('bibliography-cards');
        const viewToggles = document.querySelectorAll('.view-toggle');

        // Update toggle states
        viewToggles.forEach(toggle => {
            const isActive = toggle.getAttribute('data-view') === view;
            toggle.setAttribute('aria-pressed', isActive);
            toggle.classList.toggle('active', isActive);
        });

        // Show/hide containers
        if (view === 'cards') {
            if (tableContainer) tableContainer.style.display = 'none';
            if (cardsContainer) cardsContainer.style.display = 'block';
            // Card view implementation would go here
        } else {
            if (tableContainer) tableContainer.style.display = 'block';
            if (cardsContainer) cardsContainer.style.display = 'none';
        }
    }
};// 
Update the DataLoader initialization to include new components
DataLoader.initializeUI = function() {
    // Update results count
    this.updateResultsCount();
    
    // Initialize search functionality
    this.initializeSearch();
    
    // Initialize error handling
    this.initializeErrorHandling();
    
    // Set up keyboard navigation
    this.initializeKeyboardNavigation();
    
    // Initialize components
    CollectionTree.init();
    BibliographyTable.init();
};

// Make components available globally for cross-component communication
window.CollectionTree = CollectionTree;
window.BibliographyTable = BibliographyTable;