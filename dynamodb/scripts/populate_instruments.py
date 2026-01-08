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
from decimal import Decimal
from datetime import datetime

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
    
    # Load instruments from CSV
    instruments = load_instruments_from_csv(args.csv)
    print(f"Loaded {len(instruments)} instruments from {args.csv}\n")
    
    # Populate DynamoDB
    populate_instruments_table(table_name, instruments)
    
    print("\n✓ Instrument registry populated successfully!")

if __name__ == '__main__':
    main()
