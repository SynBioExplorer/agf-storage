# AGF Data Infrastructure - Database Schema Documentation

## Overview
The Australian Genome Foundry data infrastructure uses Amazon DynamoDB (NoSQL) with 4 tables designed for high-performance queries across multiple access patterns. The schema supports tracking of scientific instrument data, experiments, and file inventories.

## Database Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DynamoDB Tables Architecture                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────┐        ┌──────────────────┐                 │
│  │  INSTRUMENTS      │───────►│  SYNC_RUNS       │                 │
│  │  (Registry)       │        │  (Run Tracking)   │                 │
│  └───────────────────┘        └──────────────────┘                 │
│           │                            │                             │
│           │                            │                             │
│           ▼                            ▼                             │
│  ┌───────────────────┐        ┌──────────────────┐                 │
│  │  EXPERIMENTS      │◄──────►│  FILE_INVENTORY  │                 │
│  │  (Metadata)       │        │  (File Tracking) │                 │
│  └───────────────────┘        └──────────────────┘                 │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Table Schemas

### 1. agf-file-inventory-{env}
**Purpose:** Track individual files uploaded from scientific instruments

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| **experiment_id** | String | HASH (PK) | Unique experiment identifier |
| **file_path** | String | RANGE (SK) | S3 path to the file |
| staff_name | String | GSI-1 HASH | Name of the researcher |
| uploaded_at | Number | GSI-1 RANGE | Unix timestamp of upload |
| run_id | String | GSI-2 HASH | Associated sync run ID |
| instrument_id | String | GSI-3 HASH | Instrument that generated file |
| file_size | Number | - | File size in bytes |
| checksum | String | - | SHA256 checksum |
| file_type | String | - | File extension/type |
| s3_bucket | String | - | S3 bucket name |
| s3_key | String | - | Full S3 object key |
| file_date | Number | - | Original file modification date |
| is_update | Boolean | - | Whether file was updated |

**Access Patterns:**
- Get all files for an experiment
- List files uploaded by a specific user (sorted by date)
- Find all files from a specific run
- Track files by instrument over time

**Global Secondary Indexes:**
1. **staff_name-uploaded_at-index**: Query files by user with time sorting
2. **run_id-file_path-index**: Query all files in a specific run
3. **instrument_id-uploaded_at-index**: Query files by instrument with time sorting

---

### 2. agf-experiments-{env}
**Purpose:** Store experiment metadata and summaries

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| **experiment_id** | String | HASH (PK) | Unique experiment identifier |
| **last_updated** | Number | RANGE (SK) | Unix timestamp of last update |
| staff_name | String | GSI-1 HASH | Researcher conducting experiment |
| instrument_id | String | GSI-2 HASH | Instrument used |
| created_at | Number | GSI-2 RANGE | Experiment creation timestamp |
| experiment_folder | String | - | Folder name in S3 |
| computer_name | String | - | Computer that uploaded data |
| file_count | Number | - | Total number of files |
| total_size_bytes | Number | - | Total size of all files |
| s3_location | String | - | S3 path prefix |
| description | String | - | Experiment description |
| status | String | - | Current status |

**Access Patterns:**
- Get experiment details and history
- List experiments by researcher (sorted by update time)
- Find experiments by instrument (sorted by creation time)
- Track experiment modifications over time

**Global Secondary Indexes:**
1. **staff_name-last_updated-index**: Query experiments by user, newest first
2. **instrument_id-created_at-index**: Query experiments by instrument chronologically

---

### 3. agf-sync-runs-{env}
**Purpose:** Track data synchronization runs from instruments

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| **run_id** | String | HASH (PK) | Unique run identifier (run_YYYYMMDD_HHMMSS_xxxxx) |
| **instrument_id** | String | RANGE (SK) | Instrument performing sync |
| sync_timestamp | Number | GSI-1 RANGE | Unix timestamp of sync |
| computer_name | String | - | Computer performing sync |
| files_in_batch | Number | - | Number of files synced |
| total_size_bytes | Number | - | Total bytes transferred |
| files_by_staff | Map | - | Breakdown by researcher |
| duration_seconds | Number | - | Sync duration |
| status | String | - | Success/Failed/Partial |
| error_message | String | - | Error details if failed |

**Access Patterns:**
- Get run details by ID
- List all runs for an instrument (sorted by time)
- Monitor sync frequency and success rates
- Track data volume trends

**Global Secondary Indexes:**
1. **instrument_id-sync_timestamp-index**: Query runs by instrument chronologically

---

### 4. agf-instruments-{env}
**Purpose:** Static registry of laboratory instruments (31 instruments)

| Attribute | Type | Key Type | Description |
|-----------|------|----------|-------------|
| **instrument_id** | String | HASH (PK) | Unique instrument ID (e.g., FLO302_FACS-Melody) |
| instrument_name | String | - | Display name |
| instrument_type | String | - | Category (FLO, ANA, ROB, etc.) |
| model | String | - | Model number |
| brand | String | - | Manufacturer |
| equipment_type | String | - | Type description |
| computer_name | String | - | Associated computer |
| location | String | - | Physical location |
| created_at | Number | - | Registry timestamp |
| last_sync | Number | - | Last successful sync |
| total_bytes | Number | - | Total data processed |
| total_files | Number | - | Total files processed |
| status | String | - | Active/Inactive/Maintenance |

**Access Patterns:**
- Get instrument details by ID
- List all active instruments
- Track instrument utilization

**No GSIs** (small table, scan operations are efficient)

---

## Data Relationships

### Entity Relationship Diagram (Logical)

```mermaid
erDiagram
    INSTRUMENTS ||--o{ SYNC_RUNS : "performs"
    INSTRUMENTS ||--o{ EXPERIMENTS : "conducts"
    INSTRUMENTS ||--o{ FILE_INVENTORY : "generates"
    EXPERIMENTS ||--o{ FILE_INVENTORY : "contains"
    SYNC_RUNS ||--o{ FILE_INVENTORY : "uploads"

    INSTRUMENTS {
        string instrument_id PK
        string instrument_name
        string model
        string brand
        number last_sync
    }

    SYNC_RUNS {
        string run_id PK
        string instrument_id SK
        number sync_timestamp
        number files_in_batch
        number total_size_bytes
    }

    EXPERIMENTS {
        string experiment_id PK
        number last_updated SK
        string staff_name
        string instrument_id
        number file_count
    }

    FILE_INVENTORY {
        string experiment_id PK
        string file_path SK
        string run_id
        string instrument_id
        string staff_name
        number file_size
    }
```

---

## Query Examples

### 1. Get all files for an experiment
```python
response = dynamodb.query(
    TableName='agf-file-inventory-dev',
    KeyConditionExpression='experiment_id = :exp_id',
    ExpressionAttributeValues={':exp_id': 'EXP_20250115_001'}
)
```

### 2. Find recent experiments by a researcher
```python
response = dynamodb.query(
    TableName='agf-experiments-dev',
    IndexName='staff_name-last_updated-index',
    KeyConditionExpression='staff_name = :staff',
    ExpressionAttributeValues={':staff': 'Felix_Meier'},
    ScanIndexForward=False,  # Newest first
    Limit=10
)
```

### 3. Track instrument usage over time
```python
response = dynamodb.query(
    TableName='agf-sync-runs-dev',
    IndexName='instrument_id-sync_timestamp-index',
    KeyConditionExpression='instrument_id = :inst AND sync_timestamp > :week_ago',
    ExpressionAttributeValues={
        ':inst': 'FLO302_FACS-Melody',
        ':week_ago': int((datetime.now() - timedelta(days=7)).timestamp())
    }
)
```

### 4. Get files from a specific run
```python
response = dynamodb.query(
    TableName='agf-file-inventory-dev',
    IndexName='run_id-file_path-index',
    KeyConditionExpression='run_id = :run',
    ExpressionAttributeValues={':run': 'run_20250115_143022_abc123'}
)
```

---

## Data Flow

```
1. Instrument generates data files
        ↓
2. agf_sync.py uploads to S3 with metadata
        ↓
3. S3 triggers EventBridge on JSON upload
        ↓
4. Lambda function processes metadata
        ↓
5. Data stored in DynamoDB tables
        ↓
6. Dashboard queries DynamoDB for display
```

---

## Performance Characteristics

### Scaling
- **Billing Mode:** PAY_PER_REQUEST (automatic scaling)
- **No capacity planning required**
- **Handles burst traffic automatically**

### Data Protection
- **Point-in-time Recovery:** Enabled (35-day backup window)
- **Encryption:** Server-side encryption at rest
- **Streams:** NEW_AND_OLD_IMAGES for change tracking

### Query Performance
- **Primary key queries:** < 10ms
- **GSI queries:** < 20ms typically
- **Scan operations:** Avoided except for small tables

### Cost Optimization
- **On-demand pricing:** Pay only for reads/writes
- **GSI projections:** ALL (trade storage for query performance)
- **Efficient key design:** Minimizes hot partitions

---

## Index Usage Guidelines

### When to use each index:

| Table | Index | Use Case |
|-------|-------|----------|
| file-inventory | Primary | Get files for specific experiment |
| file-inventory | staff_name-uploaded_at | User's recent uploads |
| file-inventory | run_id-file_path | Files from sync batch |
| file-inventory | instrument_id-uploaded_at | Instrument data timeline |
| experiments | Primary | Experiment version history |
| experiments | staff_name-last_updated | User's recent work |
| experiments | instrument_id-created_at | Instrument experiments |
| sync-runs | Primary | Run details lookup |
| sync-runs | instrument_id-sync_timestamp | Instrument sync history |

---

## Data Types and Formats

### Timestamps
- **Format:** Unix timestamps (seconds since epoch)
- **Type:** Number (DynamoDB Decimal)
- **Example:** 1736841600 (2025-01-14 12:00:00 UTC)

### IDs
- **experiment_id:** Extracted from folder name
- **run_id:** Format: `run_YYYYMMDD_HHMMSS_xxxxx`
- **instrument_id:** Format: `{TYPE}{NUMBER}_{NAME}` (e.g., FLO302_FACS-Melody)

### Checksums
- **Format:** `sha256:` prefix + hex digest
- **Example:** `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

### File Paths
- **S3 Key Format:** `raw/{instrument_id}/{date}/{run_id}/{staff_name}/payload/{experiment}/{file}`
- **Stored as:** Full S3 key in file_path attribute

---

## Future Considerations

### Potential Enhancements
1. **Time-series optimization:** Consider DynamoDB Time Series tables for metrics
2. **Search capability:** Add OpenSearch for full-text search
3. **Aggregations:** Use DynamoDB Streams + Lambda for real-time metrics
4. **Archival:** Implement lifecycle policies for old data
5. **Cross-region:** Consider Global Tables for multi-region access

### Monitoring Recommendations
- Set CloudWatch alarms for throttled requests
- Monitor consumed capacity if switching from on-demand
- Track hot partition metrics
- Implement item size monitoring (400KB limit)

---

## Compliance and Security

### Data Governance
- **PII Handling:** Staff names are stored; consider pseudonymization
- **Data Retention:** Implement TTL for compliance requirements
- **Audit Trail:** DynamoDB Streams provide change history
- **Access Control:** IAM policies restrict table access

### Best Practices Implemented
- ✅ Encryption at rest
- ✅ Point-in-time recovery
- ✅ Least privilege IAM roles
- ✅ CloudFormation for infrastructure as code
- ✅ Environment separation (dev/staging/prod)
- ✅ Tagging for cost allocation

---

*Generated: 2024-11-24 | Version: 1.0 | Environment: Development*