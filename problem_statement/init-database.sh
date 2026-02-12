#!/bin/bash
# Initialize State-Based Build Framework Database
# Creates SQLite database with schema and sample data

set -e

DB_FILE="${1:-builds.db}"
echo "Initializing database: $DB_FILE"

# Create database and load schema
sqlite3 "$DB_FILE" < database-schema.sql
echo "✓ Schema loaded"

# Load sample data
sqlite3 "$DB_FILE" < sample-data.sql
echo "✓ Sample data loaded"

echo "Database initialized successfully!"
echo ""
echo "Example queries:"
echo ""
echo "# View all builds:"
echo "sqlite3 $DB_FILE 'SELECT * FROM build_summary;'"
echo ""
echo "# View current status:"
echo "sqlite3 $DB_FILE 'SELECT * FROM current_build_status;'"
echo ""
echo "# View failed builds:"
echo "sqlite3 $DB_FILE 'SELECT build_number, current_state, status FROM builds WHERE status = \"failed\";'"
echo ""
echo "# View build failures:"
echo "sqlite3 $DB_FILE 'SELECT b.build_number, f.state, f.failure_type, f.error_message FROM build_failures f JOIN builds b ON f.build_id = b.id;'"