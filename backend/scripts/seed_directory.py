# Copyright (c) 2025 Ape4, Inc. All rights reserved.
# Unauthorized copying of this file is strictly prohibited.

"""
Seed directory lists with CSV data.

Implements delete-and-replace strategy for idempotent data loading.

Usage:
    python backend/scripts/seed_directory.py \
        --account wyckoff \
        --list doctors \
        --entry-type medical_professional \
        --csv backend/data/wyckoff/doctors_profile.csv \
        --mapper medical_professional \
        --description "Wyckoff Heights Medical Center - Medical Professionals"
"""

import asyncio
import argparse
import sys
from pathlib import Path
from sqlalchemy import select, delete

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import get_database_service
from app.models.account import Account
from app.models.directory import DirectoryList, DirectoryEntry
from app.services.directory_importer import DirectoryImporter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Available field mappers
MAPPERS = {
    'medical_professional': DirectoryImporter.medical_professional_mapper,
    'pharmaceutical': DirectoryImporter.pharmaceutical_mapper,
    'product': DirectoryImporter.product_mapper,
    'contact_information': DirectoryImporter.contact_information_mapper,
    'department': DirectoryImporter.department_mapper,
    'service': DirectoryImporter.service_mapper,
    'location': DirectoryImporter.location_mapper,
    'faq': DirectoryImporter.faq_mapper,
    'cross_sell': DirectoryImporter.cross_sell_mapper,
    'up_sell': DirectoryImporter.up_sell_mapper,
    'competitive_sell': DirectoryImporter.competitive_sell_mapper,
    'classes': DirectoryImporter.classes_mapper,
}


async def seed_directory(
    account_slug: str,
    list_name: str,
    entry_type: str,
    schema_file: str,
    csv_path: str,
    mapper_name: str,
    list_description: str = None
):
    """
    Seed a directory list with CSV data using delete-and-replace strategy.
    
    Args:
        account_slug: Account identifier (e.g., "wyckoff")
        list_name: Directory list name (e.g., "doctors")
        entry_type: Entry type matching schema (e.g., "medical_professional")
        schema_file: YAML schema file (e.g., "medical_professional.yaml")
        csv_path: Path to CSV file
        mapper_name: Field mapper name (must be in MAPPERS dict)
        list_description: Optional description for the list
    """
    logger.info("═══════════════════════════════════════════════════════════════════════════════")
    logger.info("  DIRECTORY SEEDING")
    logger.info("═══════════════════════════════════════════════════════════════════════════════")
    
    # Validate mapper
    mapper = MAPPERS.get(mapper_name)
    if not mapper:
        logger.error(f"❌ Unknown mapper: {mapper_name}")
        logger.error(f"   Available mappers: {', '.join(MAPPERS.keys())}")
        return False
    
    # Validate CSV exists
    csv_file = Path(csv_path)
    if not csv_file.exists():
        logger.error(f"❌ CSV file not found: {csv_path}")
        return False
    
    logger.info(f"\n📋 Configuration:")
    logger.info(f"   Account: {account_slug}")
    logger.info(f"   List: {list_name}")
    logger.info(f"   Entry Type: {entry_type}")
    logger.info(f"   Schema: {schema_file}")
    logger.info(f"   CSV: {csv_file}")
    logger.info(f"   Mapper: {mapper_name}")
    
    # Initialize database
    db = get_database_service()
    await db.initialize()
    
    async with db.get_session() as session:
        # Get account
        logger.info(f"\n🔍 Looking up account: {account_slug}")
        result = await session.execute(
            select(Account).where(Account.slug == account_slug)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            logger.error(f"❌ Account not found: {account_slug}")
            logger.error(f"   Run admin_queries.sql to list available accounts")
            return False
        
        logger.info(f"✅ Account found: {account.name} (ID: {account.id})")
        
        # Clear existing list (delete-and-replace strategy)
        logger.info(f"\n🗑️  Clearing existing data for list: {list_name}")
        result = await session.execute(
            delete(DirectoryList).where(
                DirectoryList.account_id == account.id,
                DirectoryList.list_name == list_name
            )
        )
        deleted_count = result.rowcount
        await session.commit()
        
        if deleted_count > 0:
            logger.info(f"   Deleted {deleted_count} existing list(s)")
        else:
            logger.info(f"   No existing data (first run)")
        
        # Create new directory list
        logger.info(f"\n📋 Creating directory list: {list_name}")
        directory_list = DirectoryList(
            account_id=account.id,
            list_name=list_name,
            list_description=list_description or f"{entry_type} directory - {list_name}",
            entry_type=entry_type,
            schema_file=schema_file
        )
        session.add(directory_list)
        await session.commit()
        await session.refresh(directory_list)
        
        logger.info(f"✅ Created: {directory_list.list_name}")
        logger.info(f"   ID: {directory_list.id}")
        logger.info(f"   Description: {directory_list.list_description}")
        
        # Import entries from CSV
        logger.info(f"\n📥 Importing entries from CSV...")
        try:
            entries = DirectoryImporter.parse_csv(
                csv_path=str(csv_file),
                directory_list_id=directory_list.id,
                field_mapper=mapper,
                schema_file=schema_file
            )
        except Exception as e:
            logger.error(f"❌ Failed to parse CSV: {e}")
            await session.rollback()
            return False
        
        if not entries:
            logger.warning("⚠️  No valid entries found in CSV")
            return False
        
        # Save entries to database
        logger.info(f"\n💾 Saving {len(entries)} entries to database...")
        session.add_all(entries)
        await session.commit()
        
        logger.info(f"✅ Saved {len(entries)} entries")
        
        # Display sample entries
        if entries:
            logger.info(f"\n📝 Sample entries:")
            for i, sample in enumerate(entries[:3], 1):
                logger.info(f"\n   {i}. {sample.name}")
                logger.info(f"      Tags: {sample.tags if sample.tags else '(none)'}")
                
                # Entry-type specific details
                if entry_type == "medical_professional":
                    dept = sample.entry_data.get('department', 'N/A')
                    spec = sample.entry_data.get('specialty', 'N/A')
                    logger.info(f"      Department: {dept}")
                    logger.info(f"      Specialty: {spec}")
                    if sample.contact_info.get('location'):
                        logger.info(f"      Location: {sample.contact_info['location']}")
                
                elif entry_type == "pharmaceutical":
                    drug_class = sample.entry_data.get('drug_class', 'N/A')
                    logger.info(f"      Drug Class: {drug_class}")
                    if sample.entry_data.get('active_ingredients'):
                        logger.info(f"      Active Ingredients: {', '.join(sample.entry_data['active_ingredients'][:2])}")
                
                elif entry_type == "product":
                    category = sample.entry_data.get('category', 'N/A')
                    price = sample.entry_data.get('price')
                    logger.info(f"      Category: {category}")
                    if price:
                        logger.info(f"      Price: ${price}")
        
        logger.info("\n" + "═" * 79)
        logger.info(f"✅ SEEDING COMPLETE!")
        logger.info(f"   Account: {account.name}")
        logger.info(f"   List: {list_name}")
        logger.info(f"   Entries: {len(entries)}")
        logger.info("═" * 79 + "\n")
        
        return True


async def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Seed directory lists with CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load Wyckoff doctors
  python backend/scripts/seed_directory.py \\
      --account wyckoff \\
      --list doctors \\
      --entry-type medical_professional \\
      --csv backend/data/wyckoff/doctors_profile.csv \\
      --mapper medical_professional
  
  # Load pharmaceutical data
  python backend/scripts/seed_directory.py \\
      --account pharma_co \\
      --list prescription_drugs \\
      --entry-type pharmaceutical \\
      --csv data/drugs.csv \\
      --mapper pharmaceutical \\
      --description "Prescription drug database"
        """
    )
    
    parser.add_argument(
        '--account',
        required=True,
        help='Account slug (e.g., wyckoff, acme)'
    )
    parser.add_argument(
        '--list',
        required=True,
        help='Directory list name (e.g., doctors, products)'
    )
    parser.add_argument(
        '--entry-type',
        required=True,
        help='Entry type matching schema (e.g., medical_professional, pharmaceutical, product)'
    )
    parser.add_argument(
        '--schema-file',
        help='Schema YAML file (defaults to {entry-type}.yaml)'
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Path to CSV file'
    )
    parser.add_argument(
        '--mapper',
        required=True,
        choices=list(MAPPERS.keys()),
        help='Field mapper name'
    )
    parser.add_argument(
        '--description',
        help='Optional list description'
    )
    
    args = parser.parse_args()
    
    # Default schema file to entry_type.yaml if not provided
    schema_file = args.schema_file or f"{args.entry_type}.yaml"
    
    success = await seed_directory(
        account_slug=args.account,
        list_name=args.list,
        entry_type=args.entry_type,
        schema_file=schema_file,
        csv_path=args.csv,
        mapper_name=args.mapper,
        list_description=args.description
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

