# Deployment Guide

This guide explains how to deploy the Literature Webviewer as a static website.

## Quick Start

### Using uv (Recommended)

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Build the website:**
   ```bash
   uv run build --input your-library.rdf --production
   ```

3. **Deploy to GitHub Pages:**
   - Push your RDF file to your GitHub repository
   - The GitHub Action will automatically build and deploy your site

### Manual Build

```bash
# Install the package
uv pip install -e .

# Build with production optimizations
literature-webviewer build --input library.rdf --output dist --production

# The dist/ directory contains your static website
```

## Deployment Options

### 1. GitHub Pages (Recommended)

**Automatic Deployment:**

1. Add your Zotero RDF export file to your repository (e.g., `library.rdf`)
2. Push to the `main` or `master` branch
3. The GitHub Action will automatically:
   - Build the static website
   - Deploy to GitHub Pages
   - Make it available at `https://yourusername.github.io/yourrepo`

**Manual Setup:**

1. Build locally: `uv run build --input library.rdf --production`
2. Push the `dist/` contents to the `gh-pages` branch
3. Enable GitHub Pages in repository settings

### 2. Netlify

1. Build locally: `uv run build --input library.rdf --production`
2. Drag and drop the `dist/` folder to Netlify
3. Or connect your GitHub repository and set:
   - Build command: `uv run build --input library.rdf --production`
   - Publish directory: `dist`

### 3. Vercel

1. Connect your GitHub repository
2. Set build settings:
   - Build command: `uv run build --input library.rdf --production`
   - Output directory: `dist`

### 4. Static File Hosting

Upload the contents of the `dist/` directory to any static file hosting service:
- AWS S3 + CloudFront
- Google Cloud Storage
- Azure Static Web Apps
- Any web server

## Build Options

### Production Build

```bash
uv run build --input library.rdf --production
```

Production builds include:
- CSS and JavaScript minification
- JSON compression
- Gzip compression for all static files
- Optimized file sizes
- GitHub Pages configuration

### Development Build

```bash
uv run build --input library.rdf
```

Development builds are faster but larger file sizes.

### Advanced Options

```bash
# Build with custom output directory
uv run build --input library.rdf --output my-site --production

# Build only data files (no HTML/CSS/JS)
literature-webviewer build --input library.rdf --data-only

# Build with validation disabled (faster)
literature-webviewer build --input library.rdf --no-validate

# Watch for changes and rebuild automatically
literature-webviewer watch --input library.rdf --production
```

## File Structure

After building, your output directory will contain:

```
dist/
├── index.html              # Main website page
├── styles.css              # Minified CSS styles
├── app.js                  # Minified JavaScript application
├── data/
│   ├── bibliography.json   # Bibliography data
│   ├── collections.json    # Collection hierarchy
│   └── search-index.json   # Search optimization data
├── .nojekyll              # GitHub Pages configuration
├── deployment-info.json   # Build information
└── *.gz                   # Gzip compressed versions
```

## Performance Optimizations

Production builds automatically include:

### File Optimization
- **CSS minification**: Removes whitespace and comments
- **JavaScript minification**: Basic minification while preserving functionality
- **JSON compression**: Removes unnecessary whitespace
- **HTML minification**: Reduces file size

### Compression
- **Gzip compression**: All static files have `.gz` versions
- **Modern browsers**: Automatically serve compressed versions when supported

### Client-Side Performance
- **Virtual scrolling**: For large bibliography collections (>200 items)
- **Search indexing**: Fast full-text search with n-gram indexing
- **Lazy loading**: Progressive loading of large datasets
- **Memory optimization**: Efficient handling of large collections

## Troubleshooting

### Build Fails

1. **Check RDF file**: Ensure your RDF export is valid
   ```bash
   literature-webviewer validate-rdf --input library.rdf
   ```

2. **Check dependencies**: Ensure all dependencies are installed
   ```bash
   uv sync
   ```

3. **Verbose output**: Use `--verbose` flag for detailed error information
   ```bash
   uv run build --input library.rdf --verbose
   ```

### GitHub Action Fails

1. **Check RDF file**: Ensure an RDF file exists in your repository
2. **Check file permissions**: Ensure the workflow has write permissions
3. **Check logs**: Review the GitHub Action logs for specific errors

### Large File Sizes

1. **Use production build**: Always use `--production` for deployment
2. **Check data size**: Large libraries may need chunked loading
3. **Enable compression**: Ensure your web server serves gzip files

### Performance Issues

1. **Enable virtual scrolling**: Automatically enabled for >200 items
2. **Optimize search**: Search indexing is automatically created
3. **Check browser**: Modern browsers perform better with large datasets

## Customization

### Custom Domain (GitHub Pages)

1. Add a `CNAME` file to your repository root with your domain
2. Configure DNS to point to GitHub Pages
3. Enable HTTPS in repository settings

### Custom Styling

1. Modify `templates/styles.css` before building
2. Add custom CSS variables in the `:root` section
3. Rebuild with your changes

### Custom Templates

1. Modify `templates/index.html` for layout changes
2. Update `templates/app.js` for functionality changes
3. Test thoroughly before deployment

## Security Considerations

### Static Site Security
- No server-side processing reduces attack surface
- All data processing happens during build time
- Client-side JavaScript is minified but not obfuscated

### Data Privacy
- All bibliography data is public in the generated site
- Ensure your RDF export doesn't contain sensitive information
- Consider removing private notes or attachments before export

### Content Security Policy

Add CSP headers if hosting on your own server:

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
```

## Monitoring and Analytics

### GitHub Pages Analytics
- Enable in repository settings
- View traffic and popular pages

### Custom Analytics
- Add Google Analytics or similar to `templates/index.html`
- Rebuild and redeploy after adding tracking code

### Performance Monitoring
- Use browser dev tools to monitor performance
- Check Core Web Vitals for user experience metrics
- Monitor file sizes and loading times

## Maintenance

### Updating Your Library

1. Export new RDF from Zotero
2. Replace the RDF file in your repository
3. Push changes to trigger automatic rebuild
4. Or rebuild manually: `uv run build --input new-library.rdf --production`

### Updating the Software

1. Update the package: `uv sync --upgrade`
2. Rebuild your site: `uv run build --input library.rdf --production`
3. Test the updated site before deploying

### Backup and Recovery

1. **Source data**: Keep your original Zotero library backed up
2. **RDF exports**: Version control your RDF files
3. **Generated sites**: GitHub automatically keeps deployment history