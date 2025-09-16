"""Static site generation functionality."""

import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


@dataclass
class SiteConfig:
    """Configuration for static site generation."""
    title: str = "Literature Collection Webviewer"
    collection_title: str = "Literature Collection"
    description: str = "Interactive browser for academic literature collections exported from Zotero"
    author: str = ""
    base_url: str = ""
    theme: str = "default"


class SiteGenerationError(Exception):
    """Exception raised when site generation fails."""
    pass


class SiteGenerator:
    """Generates static HTML, CSS, and JavaScript files for the web interface."""
    
    def __init__(self, output_dir: str, templates_dir: str = "templates"):
        self.output_dir = Path(output_dir)
        self.templates_dir = Path(templates_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure Jinja2 is available
        if not JINJA2_AVAILABLE:
            raise SiteGenerationError(
                "Static site generation requires the 'jinja2' package. "
                "Install it with: pip install jinja2"
            )
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.jinja_env.filters['format_authors'] = self._format_authors
        self.jinja_env.filters['truncate_text'] = self._truncate_text
        self.jinja_env.filters['format_year'] = self._format_year
    
    def generate_site(self, config: Optional[SiteConfig] = None) -> List[str]:
        """
        Generate complete static website.
        
        Args:
            config: Site configuration options
            
        Returns:
            List of generated file paths
            
        Raises:
            SiteGenerationError: If generation fails
        """
        if config is None:
            config = SiteConfig()
        
        generated_files = []
        
        try:
            self.logger.info("Starting static site generation")
            
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate HTML file
            html_file = self._generate_html(config)
            generated_files.append(html_file)
            
            # Copy CSS file
            css_file = self._copy_css()
            generated_files.append(css_file)
            
            # Copy JavaScript file
            js_file = self._copy_javascript()
            generated_files.append(js_file)
            
            # Create assets directory and copy any additional assets
            assets_files = self._copy_assets()
            generated_files.extend(assets_files)
            
            self.logger.info(f"Generated {len(generated_files)} static files")
            return generated_files
            
        except Exception as e:
            raise SiteGenerationError(f"Failed to generate static site: {str(e)}")
    
    def _generate_html(self, config: SiteConfig) -> str:
        """Generate the main HTML file."""
        try:
            template = self.jinja_env.get_template('index.html')
            
            # Prepare template context
            context = {
                'title': config.title,
                'collection_title': config.collection_title,
                'description': config.description,
                'author': config.author,
                'base_url': config.base_url,
                'theme': config.theme,
            }
            
            # Render template
            html_content = template.render(**context)
            
            # Write to output file
            output_file = self.output_dir / 'index.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Generated HTML file: {output_file}")
            return str(output_file)
            
        except Exception as e:
            raise SiteGenerationError(f"Failed to generate HTML: {str(e)}")
    
    def _copy_css(self) -> str:
        """Copy CSS file to output directory."""
        try:
            source_file = self.templates_dir / 'styles.css'
            output_file = self.output_dir / 'styles.css'
            
            if source_file.exists():
                shutil.copy2(source_file, output_file)
                self.logger.info(f"Copied CSS file: {output_file}")
            else:
                # Generate basic CSS if template doesn't exist
                self._generate_basic_css(output_file)
                self.logger.warning(f"Template CSS not found, generated basic CSS: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            raise SiteGenerationError(f"Failed to copy CSS: {str(e)}")
    
    def _copy_javascript(self) -> str:
        """Copy JavaScript file to output directory."""
        try:
            source_file = self.templates_dir / 'app.js'
            output_file = self.output_dir / 'app.js'
            
            if source_file.exists():
                # Read the JavaScript file and add detailed item view functionality
                with open(source_file, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                
                # Add detailed item view functionality if not already present
                if 'const DetailedItemView' not in js_content:
                    js_content += self._get_detailed_item_view_js()
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                
                self.logger.info(f"Generated JavaScript file: {output_file}")
            else:
                # Generate basic JavaScript if template doesn't exist
                self._generate_basic_javascript(output_file)
                self.logger.warning(f"Template JavaScript not found, generated basic JS: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            raise SiteGenerationError(f"Failed to copy JavaScript: {str(e)}")
    
    def _copy_assets(self) -> List[str]:
        """Copy additional assets to output directory."""
        assets_files = []
        
        try:
            # Create assets directory
            assets_dir = self.output_dir / 'assets'
            assets_dir.mkdir(exist_ok=True)
            
            # Copy any assets from templates/assets if it exists
            template_assets_dir = self.templates_dir / 'assets'
            if template_assets_dir.exists():
                for asset_file in template_assets_dir.rglob('*'):
                    if asset_file.is_file():
                        relative_path = asset_file.relative_to(template_assets_dir)
                        output_asset = assets_dir / relative_path
                        output_asset.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(asset_file, output_asset)
                        assets_files.append(str(output_asset))
            
            if assets_files:
                self.logger.info(f"Copied {len(assets_files)} asset files")
            
            return assets_files
            
        except Exception as e:
            self.logger.warning(f"Failed to copy assets: {str(e)}")
            return assets_files
    
    def _generate_basic_css(self, output_file: Path) -> None:
        """Generate basic CSS if template is not available."""
        basic_css = """
/* Basic styles for literature webviewer */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f8fafc;
}

.app-container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    overflow: hidden;
}

.app-header {
    background: #2563eb;
    color: white;
    padding: 1rem 2rem;
}

.app-title {
    margin: 0;
    font-size: 1.5rem;
}

.search-input {
    width: 100%;
    max-width: 400px;
    padding: 0.5rem;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    font-size: 1rem;
}

.bibliography-table {
    width: 100%;
    border-collapse: collapse;
}

.bibliography-table th,
.bibliography-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
}

.bibliography-table th {
    background-color: #f9fafb;
    font-weight: 600;
}

.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    z-index: 1000;
}

.modal.active {
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: white;
    border-radius: 8px;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-header {
    padding: 1rem 2rem;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-body {
    padding: 2rem;
}

.modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
}
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(basic_css)
    
    def _generate_basic_javascript(self, output_file: Path) -> None:
        """Generate basic JavaScript if template is not available."""
        basic_js = """
// Basic JavaScript for literature webviewer
console.log('Literature Webviewer loaded');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Literature Webviewer...');
    
    // Load data and initialize components
    loadData().then(() => {
        console.log('Data loaded successfully');
    }).catch(error => {
        console.error('Failed to load data:', error);
    });
});

async function loadData() {
    try {
        const [bibliographyResponse, collectionsResponse] = await Promise.all([
            fetch('data/bibliography.json'),
            fetch('data/collections.json')
        ]);
        
        const bibliography = await bibliographyResponse.json();
        const collections = await collectionsResponse.json();
        
        // Initialize UI with data
        initializeUI(bibliography, collections);
        
    } catch (error) {
        throw new Error('Failed to load data: ' + error.message);
    }
}

function initializeUI(bibliography, collections) {
    // Basic UI initialization
    console.log('UI initialized with', bibliography.items?.length || 0, 'items');
}
""" + self._get_detailed_item_view_js()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(basic_js)
    
    def _get_detailed_item_view_js(self) -> str:
        """Get JavaScript code for detailed item view functionality."""
        return """

/**
 * Detailed Item View Component for displaying complete bibliography information
 */
const DetailedItemView = {
    modal: null,
    modalTitle: null,
    modalBody: null,
    modalClose: null,
    currentItem: null,
    
    /**
     * Initialize the detailed item view component
     */
    init() {
        this.modal = document.getElementById('item-modal');
        this.modalTitle = document.getElementById('modal-title');
        this.modalBody = document.querySelector('.modal-body');
        this.modalClose = document.querySelector('.modal-close');
        
        if (this.modal) {
            this.initializeEventHandlers();
        }
    },
    
    /**
     * Initialize event handlers for modal functionality
     */
    initializeEventHandlers() {
        // Close modal on close button click
        if (this.modalClose) {
            this.modalClose.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // Close modal on overlay click
        const modalOverlay = this.modal.querySelector('.modal-overlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen()) {
                this.closeModal();
            }
        });
        
        // Handle item clicks in bibliography table
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('item-title-link') || 
                e.target.closest('.item-title-link')) {
                e.preventDefault();
                const itemId = e.target.getAttribute('data-item-id') || 
                              e.target.closest('.item-title-link').getAttribute('data-item-id');
                if (itemId) {
                    this.showItemDetails(itemId);
                }
            }
            
            // Handle "View Details" button clicks
            if (e.target.classList.contains('action-btn') && 
                e.target.textContent.includes('Details')) {
                e.preventDefault();
                const row = e.target.closest('tr');
                const itemId = row ? row.getAttribute('data-item-id') : null;
                if (itemId) {
                    this.showItemDetails(itemId);
                }
            }
        });
    },
    
    /**
     * Show detailed information for a bibliography item
     */
    showItemDetails(itemId) {
        // Find the item in the bibliography data
        const item = this.findItemById(itemId);
        if (!item) {
            console.error('Item not found:', itemId);
            return;
        }
        
        this.currentItem = item;
        this.renderItemDetails(item);
        this.openModal();
        
        // Announce to screen readers
        this.announceModalOpen(item.title);
    },
    
    /**
     * Find an item by ID in the bibliography data
     */
    findItemById(itemId) {
        if (window.AppState && window.AppState.bibliography) {
            return window.AppState.bibliography.find(item => item.id === itemId);
        }
        return null;
    },
    
    /**
     * Render detailed item information in the modal
     */
    renderItemDetails(item) {
        if (!this.modalTitle || !this.modalBody) return;
        
        // Set modal title
        this.modalTitle.textContent = 'Item Details';
        
        // Generate detailed content
        const content = this.generateDetailedContent(item);
        this.modalBody.innerHTML = content;
        
        // Initialize copy-to-clipboard functionality
        this.initializeCopyButtons();
    },
    
    /**
     * Generate HTML content for detailed item view
     */
    generateDetailedContent(item) {
        const authors = this.formatAuthors(item.authors || []);
        const year = item.year || 'Unknown';
        const venue = item.venue || 'Unknown venue';
        const type = item.type || 'unknown';
        const abstract = item.abstract || 'No abstract available';
        const keywords = (item.keywords || []).join(', ') || 'No keywords';
        const collections = this.getItemCollections(item);
        
        return `
            <div class="item-details">
                <div class="item-header">
                    <h3 class="item-detail-title">${this.escapeHtml(item.title || 'Untitled')}</h3>
                    <div class="item-meta">
                        <span class="item-type-badge type-${type}">${type.toUpperCase()}</span>
                        <span class="item-year">${year}</span>
                    </div>
                </div>
                
                <div class="item-section">
                    <h4>Authors</h4>
                    <p class="item-authors">${authors}</p>
                    <button class="copy-btn" data-copy-text="${this.escapeHtml(authors)}" title="Copy authors">
                        📋 Copy
                    </button>
                </div>
                
                <div class="item-section">
                    <h4>Publication Details</h4>
                    <p><strong>Venue:</strong> ${this.escapeHtml(venue)}</p>
                    <p><strong>Year:</strong> ${year}</p>
                    <p><strong>Type:</strong> ${type}</p>
                </div>
                
                ${item.abstract ? `
                <div class="item-section">
                    <h4>Abstract</h4>
                    <div class="item-abstract">${this.escapeHtml(abstract)}</div>
                    <button class="copy-btn" data-copy-text="${this.escapeHtml(abstract)}" title="Copy abstract">
                        📋 Copy Abstract
                    </button>
                </div>
                ` : ''}
                
                ${item.keywords && item.keywords.length > 0 ? `
                <div class="item-section">
                    <h4>Keywords</h4>
                    <div class="item-keywords">
                        ${item.keywords.map(keyword => 
                            `<span class="keyword-tag">${this.escapeHtml(keyword)}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${collections.length > 0 ? `
                <div class="item-section">
                    <h4>Collections</h4>
                    <div class="item-collections">
                        ${collections.map(collection => 
                            `<span class="collection-tag">${this.escapeHtml(collection)}</span>`
                        ).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${this.generateLinksSection(item)}
                
                <div class="item-actions">
                    <button class="copy-btn primary" data-copy-citation="${item.id}" title="Copy citation">
                        📋 Copy Citation
                    </button>
                    <button class="copy-btn" data-copy-bibtex="${item.id}" title="Copy BibTeX">
                        📋 Copy BibTeX
                    </button>
                    ${item.url ? `
                    <a href="${this.escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer" class="external-link">
                        🔗 Open Link
                    </a>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    /**
     * Generate links section for DOI, URL, etc.
     */
    generateLinksSection(item) {
        const links = [];
        
        if (item.doi) {
            links.push(`<a href="https://doi.org/${this.escapeHtml(item.doi)}" target="_blank" rel="noopener noreferrer">DOI: ${this.escapeHtml(item.doi)}</a>`);
        }
        
        if (item.url && item.url !== item.doi) {
            links.push(`<a href="${this.escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">URL</a>`);
        }
        
        if (item.attachments && item.attachments.length > 0) {
            item.attachments.forEach(attachment => {
                if (attachment.url) {
                    links.push(`<a href="${this.escapeHtml(attachment.url)}" target="_blank" rel="noopener noreferrer">${this.escapeHtml(attachment.title || 'Attachment')}</a>`);
                }
            });
        }
        
        if (links.length === 0) {
            return '';
        }
        
        return `
            <div class="item-section">
                <h4>Links</h4>
                <div class="item-links">
                    ${links.join('<br>')}
                </div>
            </div>
        `;
    },
    
    /**
     * Get collection names for an item
     */
    getItemCollections(item) {
        if (!item.collections || !window.AppState || !window.AppState.collections) {
            return [];
        }
        
        return item.collections
            .map(collectionId => {
                const collection = window.AppState.collections[collectionId];
                return collection ? collection.title : null;
            })
            .filter(title => title !== null);
    },
    
    /**
     * Format authors list
     */
    formatAuthors(authors) {
        if (!authors || authors.length === 0) {
            return 'Unknown authors';
        }
        
        return authors.map(author => author.fullName || 'Unknown').join(', ');
    },
    
    /**
     * Initialize copy-to-clipboard functionality
     */
    initializeCopyButtons() {
        const copyButtons = this.modalBody.querySelectorAll('.copy-btn');
        
        copyButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                
                let textToCopy = '';
                
                if (button.hasAttribute('data-copy-text')) {
                    textToCopy = button.getAttribute('data-copy-text');
                } else if (button.hasAttribute('data-copy-citation')) {
                    textToCopy = this.generateCitation(this.currentItem);
                } else if (button.hasAttribute('data-copy-bibtex')) {
                    textToCopy = this.generateBibTeX(this.currentItem);
                }
                
                if (textToCopy) {
                    this.copyToClipboard(textToCopy, button);
                }
            });
        });
    },
    
    /**
     * Generate citation text for an item
     */
    generateCitation(item) {
        if (!item) return '';
        
        const authors = this.formatAuthors(item.authors || []);
        const year = item.year || 'n.d.';
        const title = item.title || 'Untitled';
        const venue = item.venue || '';
        
        return `${authors} (${year}). ${title}. ${venue}`.trim();
    },
    
    /**
     * Generate BibTeX entry for an item
     */
    generateBibTeX(item) {
        if (!item) return '';
        
        const type = item.type === 'article' ? 'article' : 'misc';
        const key = this.generateBibTeXKey(item);
        const authors = (item.authors || []).map(author => author.fullName || 'Unknown').join(' and ');
        const year = item.year || '';
        const title = item.title || 'Untitled';
        const venue = item.venue || '';
        
        let bibtex = `@${type}{${key},\n`;
        bibtex += `  title={${title}},\n`;
        if (authors) bibtex += `  author={${authors}},\n`;
        if (year) bibtex += `  year={${year}},\n`;
        if (venue) {
            if (item.type === 'article') {
                bibtex += `  journal={${venue}},\n`;
            } else {
                bibtex += `  publisher={${venue}},\n`;
            }
        }
        if (item.doi) bibtex += `  doi={${item.doi}},\n`;
        if (item.url) bibtex += `  url={${item.url}},\n`;
        bibtex += '}';
        
        return bibtex;
    },
    
    /**
     * Generate BibTeX key for an item
     */
    generateBibTeXKey(item) {
        const firstAuthor = item.authors && item.authors[0] ? 
            item.authors[0].surname || 'Unknown' : 'Unknown';
        const year = item.year || 'Unknown';
        const titleWords = (item.title || 'Untitled').split(' ').slice(0, 2);
        
        return `${firstAuthor}${year}${titleWords.join('')}`.replace(/[^a-zA-Z0-9]/g, '');
    },
    
    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text, button) {
        try {
            await navigator.clipboard.writeText(text);
            this.showCopyFeedback(button, 'Copied!');
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showCopyFeedback(button, 'Copied!');
            } catch (fallbackErr) {
                this.showCopyFeedback(button, 'Copy failed');
            }
            
            document.body.removeChild(textArea);
        }
    },
    
    /**
     * Show visual feedback for copy operation
     */
    showCopyFeedback(button, message) {
        const originalText = button.textContent;
        button.textContent = message;
        button.classList.add('copy-success');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copy-success');
        }, 2000);
    },
    
    /**
     * Open the modal
     */
    openModal() {
        if (this.modal) {
            this.modal.classList.add('active');
            this.modal.setAttribute('aria-hidden', 'false');
            
            // Focus the close button for accessibility
            if (this.modalClose) {
                this.modalClose.focus();
            }
            
            // Prevent body scrolling
            document.body.style.overflow = 'hidden';
        }
    },
    
    /**
     * Close the modal
     */
    closeModal() {
        if (this.modal) {
            this.modal.classList.remove('active');
            this.modal.setAttribute('aria-hidden', 'true');
            
            // Restore body scrolling
            document.body.style.overflow = '';
            
            // Clear current item
            this.currentItem = null;
        }
    },
    
    /**
     * Check if modal is currently open
     */
    isModalOpen() {
        return this.modal && this.modal.classList.contains('active');
    },
    
    /**
     * Announce modal opening to screen readers
     */
    announceModalOpen(itemTitle) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = `Opened detailed view for ${itemTitle}`;
        
        document.body.appendChild(announcement);
        setTimeout(() => {
            if (document.body.contains(announcement)) {
                document.body.removeChild(announcement);
            }
        }, 1000);
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

// Make DetailedItemView globally available
window.DetailedItemView = DetailedItemView;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        DetailedItemView.init();
    });
} else {
    DetailedItemView.init();
}
"""
    
    def _format_authors(self, authors: List[Dict[str, Any]]) -> str:
        """Jinja2 filter to format authors list."""
        if not authors:
            return "Unknown authors"
        
        author_names = []
        for author in authors:
            if isinstance(author, dict):
                name = author.get('fullName') or f"{author.get('givenName', '')} {author.get('surname', '')}".strip()
                if name:
                    author_names.append(name)
        
        return ", ".join(author_names) if author_names else "Unknown authors"
    
    def _truncate_text(self, text: str, length: int = 100) -> str:
        """Jinja2 filter to truncate text."""
        if not text or len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'
    
    def _format_year(self, year: Any) -> str:
        """Jinja2 filter to format year."""
        if not year:
            return "Unknown"
        return str(year)
    
    def get_generated_files_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about generated files.
        
        Returns:
            Dictionary with file information
        """
        files_info = {}
        
        for file_name in ['index.html', 'styles.css', 'app.js']:
            file_path = self.output_dir / file_name
            if file_path.exists():
                stat = file_path.stat()
                files_info[file_name] = {
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'exists': True
                }
            else:
                files_info[file_name] = {
                    'path': str(file_path),
                    'exists': False
                }
        
        return files_info