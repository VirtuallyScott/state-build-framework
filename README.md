# gh-pages Branch

This branch contains the **MkDocs documentation source** for the State-Based Build Framework.

## Documentation Site

The built documentation is hosted at:  
**https://VirtuallyScott.github.io/state-build-framework/**

## Building & Deploying

From the `main` branch, run:

```bash
cd mkdocs
./setup_mkdocs.sh publish
```

This will:
1. Build the documentation from the mkdocs source
2. Deploy the built HTML site to GitHub Pages

## What's in this branch?

- `mkdocs/` - Documentation source files, configuration, and build scripts
- `.gitignore` - Prevents build artifacts from being tracked

**Note:** This branch does NOT contain the application source code.  
For source code, see the `main` branch.
