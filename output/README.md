# Literature Collection Webviewer

This is a static website for browsing academic literature collections exported from Zotero.

## How to View the Website

### Option 1: Local HTTP Server (Recommended)

Due to browser security restrictions (CORS), you need to serve the website over HTTP rather than opening the files directly.

**Using Python:**
```bash
# Navigate to the output directory
cd output

# Start a local HTTP server
python3 -m http.server 8000

# Open in your browser
# http://localhost:8000
```

**Using Node.js (if you have it installed):**
```bash
# Install a simple HTTP server
npm install -g http-server

# Navigate to the output directory and start server
cd output
http-server -p 8000

# Open in your browser
# http://localhost:8000
```

### Option 2: Deploy to a Web Server

Upload the contents of this directory to any web hosting service:
- GitHub Pages
- Netlify
- Vercel
- Any web server

## Features

- **Browse Literature:** View all your bibliography items in a sortable table
- **Search:** Full-text search across titles, authors, abstracts, and keywords
- **Collections:** Navigate through your Zotero collection hierarchy
- **Detailed View:** Click "View Details" to see complete item information
- **Copy Citations:** Copy formatted citations and BibTeX entries
- **Responsive Design:** Works on desktop and mobile devices

## Files Structure

- `index.html` - Main website page
- `styles.css` - Website styling
- `app.js` - Interactive functionality
- `data/` - JSON data files with your bibliography and collections

## Troubleshooting

If you see a CORS error when opening the website:
1. Make sure you're using an HTTP server (see Option 1 above)
2. Don't open `index.html` directly in your browser
3. The website must be served over `http://` or `https://`, not `file://`

## Generated From

This website was generated from your Zotero RDF export using the Literature Webviewer build tool.