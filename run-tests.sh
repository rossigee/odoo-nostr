#!/bin/bash
set -e

# Export PostgreSQL environment variables
export PGHOST=postgres
export PGPORT=5432
export PGUSER=odoo
export PGPASSWORD=odoo

# Install additional dependencies
pip install secp256k1 coincurve coverage

# Handle vault_connector dependency
if [ ! -d "/mnt/extra-addons/vault_connector" ]; then
    echo "Downloading vault_connector module..."
    cd /tmp
    curl -L -o 16.0-develop.zip https://github.com/rossigee/currency/archive/refs/heads/16.0-develop.zip
    python3 -c "
import zipfile
import shutil
with zipfile.ZipFile('16.0-develop.zip', 'r') as zip_ref:
    zip_ref.extractall('.')
shutil.copytree('currency-16.0-develop/vault_connector', '/mnt/extra-addons/vault_connector')
"
    cd /
fi

# Initialize database
odoo -d test_db --init=base --stop-after-init

# Install module and run tests
odoo -d test_db --init=nostr_manager --stop-after-init --test-tags=/nostr_manager --log-level=info

# Run tests
# echo "Running tests with module path..."
# odoo -d test_db --test-tags=/nostr_manager --stop-after-init

echo "Tests completed successfully!"