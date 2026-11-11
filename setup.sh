#!/usr/bin/env bash
# Creates the resource group and the storage account that your alerts will watch. Run once: ./setup.sh
set -u
cd "$(dirname "$0")"
for c in az python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
az account show >/dev/null 2>&1 || { echo "Not logged in to Azure. Run: az login"; exit 1; }
RG=rg-monitor-alerts; L=azure-monitor-alerts; LOC=${AZ_LOCATION:-eastus}
SUB=$(az account show --query id -o tsv)
SA=stmon$(echo "$SUB" | tr -d '-' | cut -c1-10)
if az group exists -n $RG | grep -q true; then echo "The resource group already exists."; exit 0; fi
az group create -n $RG -l $LOC --tags lab=$L >/dev/null || { echo "could not create the resource group"; exit 1; }
az storage account create -g $RG -n $SA -l $LOC --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2 --allow-blob-public-access false --tags lab=$L owner=you >/dev/null || { echo "could not create the storage account"; exit 1; }
az storage container create --account-name $SA -n receipts --auth-mode key --account-key "$(az storage account keys list -g $RG -n $SA --query '[0].value' -o tsv)" >/dev/null 2>&1
cat <<TXT
Ready.
  Resource group:   $RG ($LOC)
  Storage account:  $SA   (this is what your alerts watch)
Names to use:       action group ag-beanie-oncall, metric alert alert-storage-transactions, activity log alert alert-storage-deleted
Quota/capacity errors? They are normal in Azure and not your mistake: see the note in the lab.
TXT
