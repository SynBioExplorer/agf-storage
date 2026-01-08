# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This submodule contains storage infrastructure for the Australian Genome Foundry:
- **DynamoDB tables** (4 tables with GSI indexes)
- **S3 bucket configurations** (lifecycle rules, versioning)
- **Instrument registry** data and scripts

## Directory Structure

```
storage/
├── dynamodb/
│   ├── cloudformation/
│   │   └── agf-dynamodb-tables.yaml  # Table definitions
│   ├── scripts/
│   │   └── populate_instruments.py   # Seed instrument registry
│   ├── data/
│   │   └── Instrument_Inventory.csv  # 31 instruments
│   └── tables-config.json            # Exported table schemas
├── s3/
│   ├── bucket-config.json            # Bucket settings
│   └── lifecycle-rules.json          # Lifecycle policies
└── DATABASE_SCHEMA.md                # Full schema documentation
```

## DynamoDB Tables

| Table | PK | SK | GSIs | Items |
|-------|----|----|------|-------|
| agf-file-inventory-dev | experiment_id | file_path | 3 | 688 |
| agf-experiments-dev | experiment_id | last_updated | 2 | 120 |
| agf-sync-runs-dev | run_id | instrument_id | 1 | 60 |
| agf-instruments-dev | instrument_id | - | 0 | 30 |

## Common Commands

### Query DynamoDB
```bash
# Scan file inventory
aws dynamodb scan --table-name agf-file-inventory-dev --limit 10

# Query by staff
aws dynamodb query --table-name agf-experiments-dev --index-name staff_name-last_updated-index --key-condition-expression "staff_name = :staff" --expression-attribute-values '{":staff":{"S":"researcher@agf.edu"}}'
```

### Update Instrument Registry
```bash
python3 dynamodb/scripts/populate_instruments.py --environment dev --csv dynamodb/data/Instrument_Inventory.csv
```

### Deploy CloudFormation Stack
```bash
aws cloudformation deploy --template-file dynamodb/cloudformation/agf-dynamodb-tables.yaml --stack-name agf-dynamodb-dev --parameter-overrides Environment=dev
```

## S3 Buckets

| Bucket | Purpose |
|--------|---------|
| agf-instrument-data | Primary data storage (versioned) |
| agf-instrument-data-deployments | Lambda deployment packages |
