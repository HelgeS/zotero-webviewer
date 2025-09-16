# Literature Collection Webviewer

A static website generator that transforms Zotero RDF exports into interactive, searchable web interfaces for browsing academic literature collections.

## Features

- **Interactive Bibliography Table**: Sortable columns, pagination, and detailed item views
- **Hierarchical Collection Navigation**: Tree-style browsing of your Zotero collections
- **Full-Text Search**: Fast search across titles, authors, abstracts, and keywords
- **Responsive Design**: Works on desktop and mobile devices
- **Static Deployment**: No server required - deploy anywhere
- **Performance Optimized**: Virtual scrolling and search indexing for large collections
- **Production Ready**: Minification, compression, and deployment automation

## Quick Start

### 1. Export from Zotero

1. In Zotero: **File → Export Library...**
2. Choose **Zotero RDF** format
3. Save as `library.rdf` in your project directory

### 2. Build Your Website

```bash
# Install dependencies
uv sync

# Build the website
uv run build --input library.rdf --production

# Your static website is now in the 'output' directory
```

### 3. Deploy to GitHub Pages

1. Add your `library.rdf` file to your GitHub repository
2. Push to the `main` branch
3. GitHub Actions will automatically build and deploy your site
4. Access at `https://yourusername.github.io/yourrepo`

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/literature-webviewer.git
cd literature-webviewer

# Install with uv
uv sync
```

### Using pip

```bash
# Install from source
pip install -e .

# Or install dependencies manually
pip install rdflib jinja2 click
```

## Usage

### Command Line Interface

```bash
# Basic build
literature-webviewer build --input library.rdf

# Production build with optimizations
literature-webviewer build --input library.rdf --production

# Custom output directory
literature-webviewer build --input library.rdf --output my-site

# Watch for changes and rebuild automatically
literature-webviewer watch --input library.rdf

# Validate RDF file
literature-webviewer validate-rdf --input library.rdf

# Show build information
literature-webviewer info --output output
```

### Simple Build Script

```bash
# Auto-detect RDF file and build
python build.py

# Production build
python build.py --production

# Specify input file
python build.py --input my-library.rdf --production
```

### uv Run Commands

```bash
# Quick build (auto-detects RDF file)
uv run build

# Production build
uv run build --production

# With specific input
uv run build --input library.rdf --production
```

## Build Options

| Option | Description |
|--------|-------------|
| `--input` | Input RDF file path |
| `--output` | Output directory (default: output) |
| `--production` | Enable minification and compression |
| `--data-only` | Generate only JSON files, skip HTML/CSS/JS |
| `--combined` | Single JSON file instead of separate files |
| `--validate` | Validate generated files (default: enabled) |
| `--incremental` | Enable incremental builds (default: enabled) |
| `--verbose` | Enable detailed logging |

## Deployment

### GitHub Pages (Automatic)

1. **Add RDF file** to your repository
2. **Push to main branch** - GitHub Actions handles the rest
3. **Enable Pages** in repository settings (if not auto-enabled)

The included GitHub Action (`.github/workflows/deploy.yml`) automatically:
- Detects your RDF file
- Builds with production optimizations
- Deploys to GitHub Pages

### Other Platforms

- **Netlify**: Drag & drop the `output` folder or connect your GitHub repo
- **Vercel**: Connect GitHub repo with build command `uv run build --production`
- **Static Hosting**: Upload `output` folder contents to any web server

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Performance Features

### For Large Collections

- **Virtual Scrolling**: Handles thousands of items smoothly
- **Search Indexing**: Fast full-text search with n-gram indexing
- **Lazy Loading**: Progressive loading of large datasets
- **Memory Optimization**: Efficient handling of large collections

### Production Optimizations

- **File Minification**: CSS, JavaScript, and HTML compression
- **Gzip Compression**: Automatic compression for all static files
- **JSON Optimization**: Compact data format
- **Caching Headers**: Optimized for browser caching

## Project Structure

```
literature-webviewer/
├── src/literature_webviewer/    # Python source code
│   ├── cli.py                   # Command-line interface
│   ├── rdf_parser.py           # RDF parsing logic
│   ├── data_transformer.py     # Data transformation
│   ├── collection_builder.py   # Collection hierarchy
│   ├── json_generator.py       # JSON output generation
│   ├── site_generator.py       # Static site generation
│   ├── build_pipeline.py       # Build orchestration
│   └── production_optimizer.py # Production optimizations
├── templates/                   # Website templates
│   ├── index.html              # Main HTML template
│   ├── styles.css              # CSS styles
│   └── app.js                  # JavaScript application
├── .github/workflows/           # GitHub Actions
│   └── deploy.yml              # Automatic deployment
├── build.py                    # Simple build script
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## Generated Website Structure

```
output/
├── index.html                  # Main website page
├── styles.css                  # Minified CSS
├── app.js                      # Minified JavaScript
├── data/
│   ├── bibliography.json       # Bibliography data
│   ├── collections.json        # Collection hierarchy
│   └── search-index.json       # Search optimization
├── .nojekyll                   # GitHub Pages config
└── *.gz                        # Compressed versions
```

## Development

### Setting Up Development Environment

```bash
# Clone and install
git clone https://github.com/yourusername/literature-webviewer.git
cd literature-webviewer
uv sync

# Run tests (when available)
uv run pytest

# Build development version
uv run build --input sample.rdf --verbose
```

### Making Changes

1. **Templates**: Modify files in `templates/` directory
2. **Python Code**: Update source files in `src/literature_webviewer/`
3. **Rebuild**: Run `uv run build` to test changes
4. **Production Test**: Use `--production` flag before deploying

## Troubleshooting

### Common Issues

**Build fails with "No RDF file found":**
- Ensure your RDF file exists and has `.rdf` or `.xml` extension
- Use `--input` to specify the file path explicitly

**Large file sizes:**
- Use `--production` flag for minification and compression
- Check that gzip compression is enabled on your web server

**Performance issues with large libraries:**
- Virtual scrolling automatically enables for >200 items
- Consider splitting very large libraries into smaller collections

**GitHub Action fails:**
- Ensure an RDF file exists in your repository
- Check that the workflow has write permissions for Pages

### Getting Help

1. **Validate your RDF**: `literature-webviewer validate-rdf --input library.rdf`
2. **Use verbose mode**: Add `--verbose` to any command for detailed output
3. **Check logs**: Review build output for specific error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with sample data
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [rdflib](https://rdflib.readthedocs.io/) for RDF parsing
- Uses [Jinja2](https://jinja.palletsprojects.com/) for templating
- Styled with modern CSS Grid and Flexbox
- Optimized for performance with virtual scrolling and search indexing