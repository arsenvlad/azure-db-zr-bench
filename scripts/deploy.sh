#!/bin/bash
# deploy.sh - Deploy Azure DB Zone Redundancy Benchmark Infrastructure
#
# Usage:
#   ./scripts/deploy.sh -g <resource-group> -l <location> -p <ssh-public-key> -s <db-password>
#
# Example:
#   ./scripts/deploy.sh -g rg-zrbench -l centralus -p "$(cat ~/.ssh/id_rsa.pub)" -s "MySecureP@ssw0rd123!"

set -e

# Default values
LOCATION="centralus"
RESOURCE_GROUP=""
SSH_PUBLIC_KEY=""
DB_PASSWORD=""
ADMIN_USERNAME="benchadmin"
TEMPLATE_FILE="infra/main.bicep"

# Parse command line arguments
while getopts "g:l:p:s:u:h" opt; do
    case $opt in
        g) RESOURCE_GROUP="$OPTARG" ;;
        l) LOCATION="$OPTARG" ;;
        p) SSH_PUBLIC_KEY="$OPTARG" ;;
        s) DB_PASSWORD="$OPTARG" ;;
        u) ADMIN_USERNAME="$OPTARG" ;;
        h)
            echo "Usage: $0 -g <resource-group> -l <location> -p <ssh-public-key> -s <db-password>"
            echo ""
            echo "Options:"
            echo "  -g  Resource group name (required)"
            echo "  -l  Azure region (default: centralus)"
            echo "  -p  SSH public key for VM access (required)"
            echo "  -s  Database admin password (required)"
            echo "  -u  Admin username (default: benchadmin)"
            echo "  -h  Show this help message"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    echo "Error: Resource group (-g) is required"
    exit 1
fi

if [ -z "$SSH_PUBLIC_KEY" ]; then
    echo "Error: SSH public key (-p) is required"
    exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
    echo "Error: Database password (-s) is required"
    exit 1
fi

# Validate password complexity
if [[ ${#DB_PASSWORD} -lt 12 ]]; then
    echo "Error: Password must be at least 12 characters long"
    exit 1
fi

echo "=========================================="
echo "Azure DB Zone Redundancy Benchmark Deploy"
echo "=========================================="
echo ""
echo "Resource Group: $RESOURCE_GROUP"
echo "Location:       $LOCATION"
echo "Admin User:     $ADMIN_USERNAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed"
    echo "Install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "Error: Not logged in to Azure CLI"
    echo "Run: az login"
    exit 1
fi

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# Deploy infrastructure
echo ""
echo "Deploying infrastructure (this may take 20-30 minutes)..."
echo ""

DEPLOYMENT_OUTPUT=$(az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$TEMPLATE_FILE" \
    --parameters \
        location="$LOCATION" \
        adminUsername="$ADMIN_USERNAME" \
        adminPassword="$DB_PASSWORD" \
        sshPublicKey="$SSH_PUBLIC_KEY" \
    --output json)

# Extract outputs
VM_PUBLIC_IP=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.vmPublicIp.value')
VM_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.vmName.value')
NAME_SUFFIX=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.nameSuffix.value')

PG_NOHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.postgresNonHaHost.value')
PG_SZHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.postgresSameZoneHaHost.value')
PG_CZHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.postgresCrossZoneHaHost.value')

MYSQL_NOHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.mysqlNonHaHost.value')
MYSQL_SZHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.mysqlSameZoneHaHost.value')
MYSQL_CZHA_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.mysqlCrossZoneHaHost.value')

SQL_HOST=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.sqlServerHost.value')
SQL_NONZR_DB=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.sqlDbNonZrName.value')
SQL_ZR_DB=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.properties.outputs.sqlDbZrName.value')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "VM Public IP: $VM_PUBLIC_IP"
echo "SSH Command:  ssh $ADMIN_USERNAME@$VM_PUBLIC_IP"
echo ""
echo "Name Suffix:  $NAME_SUFFIX"
echo ""
echo "PostgreSQL Hosts:"
echo "  Non-HA:       $PG_NOHA_HOST"
echo "  SameZone-HA:  $PG_SZHA_HOST"
echo "  CrossZone-HA: $PG_CZHA_HOST"
echo ""
echo "MySQL Hosts:"
echo "  Non-HA:       $MYSQL_NOHA_HOST"
echo "  SameZone-HA:  $MYSQL_SZHA_HOST"
echo "  CrossZone-HA: $MYSQL_CZHA_HOST"
echo ""
echo "Azure SQL:"
echo "  Server:       $SQL_HOST"
echo "  Non-ZR DB:    $SQL_NONZR_DB"
echo "  ZR DB:        $SQL_ZR_DB"
echo ""

# Generate config file
CONFIG_FILE="config.generated.yaml"
cat > "$CONFIG_FILE" << EOF
# Azure DB Zone Redundancy Benchmark Configuration
# Auto-generated by deploy.sh on $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# 
# Set the DB_PASSWORD environment variable before running benchmarks:
#   export DB_PASSWORD='your-password'

targets:
  # PostgreSQL Flexible Server targets
  pg-noha:
    host: "$PG_NOHA_HOST"
    port: 5432
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "postgres"
    mode: "no-ha"
    ssl_mode: "require"

  pg-samezoneha:
    host: "$PG_SZHA_HOST"
    port: 5432
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "postgres"
    mode: "samezone-ha"
    ssl_mode: "require"

  pg-crosszoneha:
    host: "$PG_CZHA_HOST"
    port: 5432
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "postgres"
    mode: "crosszone-ha"
    ssl_mode: "require"

  # MySQL Flexible Server targets
  mysql-noha:
    host: "$MYSQL_NOHA_HOST"
    port: 3306
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "mysql"
    mode: "no-ha"
    ssl_mode: "REQUIRED"

  mysql-samezoneha:
    host: "$MYSQL_SZHA_HOST"
    port: 3306
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "mysql"
    mode: "samezone-ha"
    ssl_mode: "REQUIRED"

  mysql-crosszoneha:
    host: "$MYSQL_CZHA_HOST"
    port: 3306
    database: "benchmark"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "mysql"
    mode: "crosszone-ha"
    ssl_mode: "REQUIRED"

  # Azure SQL Database targets
  sqldb-nonzr:
    host: "$SQL_HOST"
    port: 1433
    database: "$SQL_NONZR_DB"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "sqldb"
    mode: "non-zr"
    driver: "ODBC Driver 18 for SQL Server"

  sqldb-zr:
    host: "$SQL_HOST"
    port: 1433
    database: "$SQL_ZR_DB"
    username: "$ADMIN_USERNAME"
    password: "\${DB_PASSWORD}"
    service: "sqldb"
    mode: "zr"
    driver: "ODBC Driver 18 for SQL Server"
EOF

echo "Configuration file generated: $CONFIG_FILE"
echo ""
echo "Next steps:"
echo "1. SSH into the VM:  ssh $ADMIN_USERNAME@$VM_PUBLIC_IP"
echo "2. Copy the config file to the VM"
echo "3. Install the benchmark tool: pip install -e ."
echo "4. Set DB_PASSWORD: export DB_PASSWORD='your-password'"
echo "5. Run benchmarks: azure-db-zr-bench suite --service all"
