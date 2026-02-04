# Rhylthyme Web Visualizer

Generate interactive HTML DAG visualizations from Rhylthyme program files.

## Installation

```bash
# From the rhylthyme-split directory
pip install -e .              # Install main rhylthyme package
pip install -e rhylthyme-web  # Install web visualizer
```

## Usage

### Web App (with upload support)

Start the web server:

```bash
rhylthyme-web
```

Then open http://localhost:5000 in your browser. You can:
- **Upload** a local .json or .yaml file
- **Paste a URL** to load from https
- **Try examples** with one click

Options:
```
rhylthyme-web --help

  -p, --port PORT   Port to run on (default: 5000)
  --host HOST       Host to bind to (default: 127.0.0.1)
  --debug           Enable debug mode
```

### Command Line - Single File

```bash
# Opens in browser
rhylthyme-visualize program.json

# Save to specific file
rhylthyme-visualize program.json -o output.html --no-browser
```

### Command Line - Batch Generation

```bash
cd rhylthyme-web

# Generate DAGs for all examples
python generate_dags.py

# Generate DAGs for specific files
python generate_dags.py ../rhylthyme-examples/programs/breakfast_schedule.json

# Generate DAGs for a directory
python generate_dags.py ../rhylthyme-examples/programs/ -o my_output/
```

## Output

Each visualization is a self-contained HTML file with:
- Interactive DAG showing task dependencies
- Timeline view with resource usage
- Step details and durations
- Resource constraint indicators
