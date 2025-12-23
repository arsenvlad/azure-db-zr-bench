#!/bin/bash
# cleanup.sh - Delete the benchmark resource group
#
# Usage: ./scripts/cleanup.sh -g <resource-group>

set -e

RESOURCE_GROUP=""

while getopts "g:h" opt; do
    case $opt in
        g) RESOURCE_GROUP="$OPTARG" ;;
        h)
            echo "Usage: $0 -g <resource-group>"
            echo ""
            echo "Options:"
            echo "  -g  Resource group name to delete (required)"
            echo "  -h  Show this help message"
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$RESOURCE_GROUP" ]; then
    echo "Error: Resource group (-g) is required"
    exit 1
fi

echo "=========================================="
echo "Azure DB ZR Benchmark Cleanup"
echo "=========================================="
echo ""
echo "This will DELETE the resource group: $RESOURCE_GROUP"
echo "ALL resources in this group will be permanently deleted."
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Deleting resource group $RESOURCE_GROUP..."
az group delete --name "$RESOURCE_GROUP" --yes --no-wait

echo ""
echo "Resource group deletion initiated."
echo "This may take several minutes to complete."
echo ""
echo "To check status:"
echo "  az group show --name $RESOURCE_GROUP --query provisioningState -o tsv"
