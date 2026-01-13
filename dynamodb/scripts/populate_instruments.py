#!/usr/bin/env python3
"""
Populate AGF Instruments DynamoDB Table

Reads instrument inventory from CSV and populates the instruments table.
Author: Felix Meier
Version: 1.0
"""

import boto3
import csv
import argparse
import sys
from decimal import Decimal
from datetime import datetime

# Required columns in the CSV file
REQUIRED_COLUMNS = ['ID', 'PC_name', 'Model', 'Equipment Item', 'Equipment Type', 'Brand']


def validate_csv(csv_path: str):
    """
    Validate CSV has required columns and valid data.

    Args:
        csv_path: Path to the CSV file

    Raises:
        ValueError: If validation fails
    """
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        # Check headers
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no headers")

        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check each row
        for i, row in enumerate(reader, 2):  # Start at 2 (header is 1)
            for col in REQUIRED_COLUMNS:
                if not row.get(col, '').strip():
                    raise ValueError(f"Row {i}: Empty value for required column '{col}'")

            # Validate instrument ID format (should be alphanumeric with optional underscore)
            inst_id = row.get('ID', '')
            if not inst_id.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Row {i}: Invalid instrument ID format '{inst_id}'")

    print(f"✓ CSV validation passed")


def load_instruments_from_csv(csv_path: str) -> list:
    """Load instrument data from CSV"""
    instruments = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            instruments.append({
                'instrument_id': row['ID'],
                'computer_name': row['PC_name'],
                'model': row['Model'],
                'equipment_item': row['Equipment Item'],
                'equipment_type': row['Equipment Type'],
                'brand': row['Brand']
            })
    
    return instruments

def populate_instruments_table(table_name: str, instruments: list):
    """Populate DynamoDB table with instrument data"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    print(f"Populating {table_name} with {len(instruments)} instruments...")
    
    for inst in instruments:
        # Extract instrument type from ID (e.g., FLO302 -> FLO)
        instrument_type = ''.join([c for c in inst['instrument_id'].split('_')[0] if not c.isdigit()])
        
        item = {
            'instrument_id': inst['instrument_id'],
            'instrument_type': instrument_type,
            'instrument_name': inst['equipment_item'],
            'brand': inst['brand'],
            'model': inst['model'],
            'computer_name': inst['computer_name'],
            'equipment_type': inst['equipment_type'],
            'is_active': True,
            'last_sync': Decimal('0'),  # Will be updated by Lambda
            'total_runs': Decimal('0'),
            'total_bytes': Decimal('0'),
            'created_at': Decimal(str(int(datetime.now().timestamp())))
        }
        
        try:
            table.put_item(Item=item)
            print(f"  ✓ {inst['instrument_id']}: {inst['equipment_item']}")
        except Exception as e:
            print(f"  ✗ Error adding {inst['instrument_id']}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Populate AGF Instruments DynamoDB Table')
    parser.add_argument('--environment', default='dev', choices=['dev', 'staging', 'prod'],
                       help='Environment name')
    parser.add_argument('--csv', default='Instrument_Inventory.csv',
                       help='Path to instrument CSV file')
    args = parser.parse_args()
    
    # Construct table name
    table_name = f"agf-instruments-{args.environment}"
    
    print("========================================")
    print("AGF Instrument Registry Population")
    print(f"Environment: {args.environment}")
    print(f"Table: {table_name}")
    print("========================================\n")

    # Validate CSV before processing
    try:
        validate_csv(args.csv)
    except ValueError as e:
        print(f"❌ CSV validation failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ CSV file not found: {args.csv}")
        sys.exit(1)

    # Load instruments from CSV
    instruments = load_instruments_from_csv(args.csv)
    print(f"Loaded {len(instruments)} instruments from {args.csv}\n")
    
    # Populate DynamoDB
    populate_instruments_table(table_name, instruments)
    
    print("\n✓ Instrument registry populated successfully!")

if __name__ == '__main__':
    main()
