#!/usr/bin/env python3
"""
IBM AML Dataset Ingestion Script
Uploads HI-Small dataset to MongoDB Atlas with batch processing.

Usage:
    python aml_ingest.py --csv HI-Small_Trans.csv --batch-size 5000

Requirements:
    pip install pymongo pandas dnspython tqdm
"""

import argparse
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional

import certifi
import pandas as pd
from pymongo import MongoClient, UpdateOne, InsertOne
from pymongo.errors import BulkWriteError, ConnectionFailure
from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================

MONGODB_URI = "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
DATABASE_NAME = "aml_db"

# Collection names
TRANSACTIONS_COLLECTION = "transactions"
ACCOUNTS_COLLECTION = "accounts"
BANKS_COLLECTION = "banks"
INGESTION_LOG_COLLECTION = "ingestion_log"

# Processing settings
DEFAULT_BATCH_SIZE = 5000      # Records per batch (memory-safe)
MAX_MEMORY_MB = 800            # Target max memory usage
CHUNK_SIZE = 10000             # CSV read chunk size

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('aml_ingestion.log')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_mongo_client() -> MongoClient:
    """Create MongoDB client with connection validation."""
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            tlsCAFile=certifi.where()
        )
        # Validate connection
        client.admin.command('ping')
        logger.info("Connected to MongoDB Atlas")
        return client
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def setup_collections(db) -> None:
    """Create collections and indexes if they don't exist."""

    # Transactions indexes
    db[TRANSACTIONS_COLLECTION].create_index("txn_id", unique=True)
    db[TRANSACTIONS_COLLECTION].create_index("timestamp")
    db[TRANSACTIONS_COLLECTION].create_index("sender.account_id")
    db[TRANSACTIONS_COLLECTION].create_index("receiver.account_id")
    db[TRANSACTIONS_COLLECTION].create_index("is_laundering")
    db[TRANSACTIONS_COLLECTION].create_index("amount.received")
    db[TRANSACTIONS_COLLECTION].create_index([("sender.account_id", 1), ("timestamp", -1)])
    db[TRANSACTIONS_COLLECTION].create_index([("is_laundering", 1), ("amount.received", -1)])

    # Accounts indexes
    db[ACCOUNTS_COLLECTION].create_index("account_id")
    db[ACCOUNTS_COLLECTION].create_index("bank_id")
    db[ACCOUNTS_COLLECTION].create_index("suspicious_count")

    # Banks indexes
    db[BANKS_COLLECTION].create_index("bank_id", unique=True)

    logger.info("Indexes created/verified")


# ============================================================
# DATA TRANSFORMATION
# ============================================================

def generate_txn_id(row_index: int, timestamp: str, sender: str, receiver: str) -> str:
    """Generate deterministic transaction ID for idempotency."""
    # Create hash from unique combination
    unique_str = f"{row_index}_{timestamp}_{sender}_{receiver}"
    hash_suffix = hashlib.md5(unique_str.encode()).hexdigest()[:8]
    return f"TXN_{row_index:010d}_{hash_suffix}"


def transform_row(row: pd.Series, row_index: int, batch_id: str) -> Dict[str, Any]:
    """Transform a CSV row into MongoDB document format."""

    # Parse timestamp
    try:
        timestamp = pd.to_datetime(row.get('Timestamp', row.get('timestamp', '')))
    except:
        timestamp = datetime.utcnow()

    # Extract fields with fallbacks for different column naming conventions
    sender_account = str(row.get('Account', row.get('From Account', row.get('account', '')))).strip()
    sender_bank = str(row.get('From Bank', row.get('from_bank', ''))).strip()
    receiver_account = str(row.get('Account.1', row.get('To Account', row.get('account_1', '')))).strip()
    receiver_bank = str(row.get('To Bank', row.get('to_bank', ''))).strip()

    # Amounts
    amount_sent = float(row.get('Amount Paid', row.get('amount_paid', 0)) or 0)
    amount_received = float(row.get('Amount Received', row.get('amount_received', 0)) or 0)

    # If amount_sent is 0, use amount_received
    if amount_sent == 0:
        amount_sent = amount_received

    # Currencies
    currency_sent = str(row.get('Payment Currency', row.get('payment_currency', 'USD'))).strip()
    currency_received = str(row.get('Receiving Currency', row.get('receiving_currency', 'USD'))).strip()

    # Payment format
    payment_format = str(row.get('Payment Format', row.get('payment_format', 'Unknown'))).strip()

    # Laundering flag
    is_laundering = bool(int(row.get('Is Laundering', row.get('is_laundering', 0)) or 0))

    # Generate deterministic ID
    txn_id = generate_txn_id(row_index, str(timestamp), sender_account, receiver_account)

    return {
        "txn_id": txn_id,
        "timestamp": timestamp,
        "sender": {
            "account_id": sender_account,
            "bank_id": sender_bank
        },
        "receiver": {
            "account_id": receiver_account,
            "bank_id": receiver_bank
        },
        "amount": {
            "sent": amount_sent,
            "received": amount_received,
            "currency_sent": currency_sent,
            "currency_received": currency_received
        },
        "payment_format": payment_format,
        "is_laundering": is_laundering,
        "batch_id": batch_id,
        "ingested_at": datetime.utcnow()
    }


# ============================================================
# BATCH PROCESSING
# ============================================================

def read_csv_in_chunks(csv_path: str, chunk_size: int) -> Generator[pd.DataFrame, None, None]:
    """Read CSV file in memory-efficient chunks."""

    logger.info(f"Reading CSV: {csv_path}")

    # Get total rows for progress tracking
    total_rows = sum(1 for _ in open(csv_path, 'r')) - 1  # Subtract header
    logger.info(f"Total rows in CSV: {total_rows:,}")

    # Read in chunks
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=True):
        yield chunk


def get_last_processed_batch(db) -> int:
    """Get the last successfully processed batch number for resume capability."""

    last_log = db[INGESTION_LOG_COLLECTION].find_one(
        {"status": "completed"},
        sort=[("batch_number", -1)]
    )

    if last_log:
        return last_log["batch_number"]
    return 0


def log_batch(db, batch_id: str, batch_number: int, stats: Dict, status: str,
              error_msg: Optional[str] = None, start_row: int = 0, end_row: int = 0) -> None:
    """Log batch processing results."""

    db[INGESTION_LOG_COLLECTION].update_one(
        {"_id": batch_id},
        {"$set": {
            "batch_number": batch_number,
            "records_processed": stats.get("processed", 0),
            "records_inserted": stats.get("inserted", 0),
            "records_skipped": stats.get("skipped", 0),
            "start_time": stats.get("start_time"),
            "end_time": datetime.utcnow(),
            "duration_seconds": stats.get("duration", 0),
            "status": status,
            "error_message": error_msg,
            "csv_start_row": start_row,
            "csv_end_row": end_row
        }},
        upsert=True
    )


def process_batch(db, documents: List[Dict], batch_id: str) -> Dict[str, int]:
    """
    Process a batch of documents with bulk upsert.
    Uses upsert to ensure idempotency - re-running won't create duplicates.
    """

    if not documents:
        return {"inserted": 0, "skipped": 0, "errors": 0}

    # Prepare bulk operations (upsert for idempotency)
    operations = [
        UpdateOne(
            {"txn_id": doc["txn_id"]},  # Match on unique ID
            {"$setOnInsert": doc},       # Only insert if not exists
            upsert=True
        )
        for doc in documents
    ]

    try:
        result = db[TRANSACTIONS_COLLECTION].bulk_write(operations, ordered=False)
        return {
            "inserted": result.upserted_count,
            "skipped": result.matched_count,  # Already existed
            "errors": 0
        }
    except BulkWriteError as e:
        # Partial success - some documents may have been inserted
        write_errors = len(e.details.get('writeErrors', []))
        inserted = e.details.get('nUpserted', 0)
        logger.warning(f"Bulk write partial failure: {write_errors} errors, {inserted} inserted")
        return {
            "inserted": inserted,
            "skipped": 0,
            "errors": write_errors
        }


# ============================================================
# ENTITY EXTRACTION
# ============================================================

def extract_accounts(db) -> int:
    """Extract unique accounts from transactions using aggregation."""

    logger.info("Extracting accounts from transactions...")

    pipeline = [
        # Unwind to get both sender and receiver
        {"$project": {
            "accounts": [
                {
                    "account_id": "$sender.account_id",
                    "bank_id": "$sender.bank_id",
                    "amount": "$amount.sent",
                    "is_sender": True,
                    "is_laundering": "$is_laundering",
                    "timestamp": "$timestamp"
                },
                {
                    "account_id": "$receiver.account_id",
                    "bank_id": "$receiver.bank_id",
                    "amount": "$amount.received",
                    "is_sender": False,
                    "is_laundering": "$is_laundering",
                    "timestamp": "$timestamp"
                }
            ]
        }},
        {"$unwind": "$accounts"},
        # Group by account
        {"$group": {
            "_id": {
                "bank_id": "$accounts.bank_id",
                "account_id": "$accounts.account_id"
            },
            "first_seen": {"$min": "$accounts.timestamp"},
            "last_seen": {"$max": "$accounts.timestamp"},
            "transaction_count": {"$sum": 1},
            "total_sent": {"$sum": {"$cond": ["$accounts.is_sender", "$accounts.amount", 0]}},
            "total_received": {"$sum": {"$cond": ["$accounts.is_sender", 0, "$accounts.amount"]}},
            "suspicious_count": {"$sum": {"$cond": ["$accounts.is_laundering", 1, 0]}}
        }},
        # Reshape
        {"$project": {
            "_id": {"$concat": ["$_id.bank_id", "_", "$_id.account_id"]},
            "account_id": "$_id.account_id",
            "bank_id": "$_id.bank_id",
            "first_seen": 1,
            "last_seen": 1,
            "transaction_count": 1,
            "total_sent": 1,
            "total_received": 1,
            "suspicious_count": 1
        }},
        # Output to accounts collection
        {"$merge": {
            "into": ACCOUNTS_COLLECTION,
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }}
    ]

    db[TRANSACTIONS_COLLECTION].aggregate(pipeline, allowDiskUse=True)
    count = db[ACCOUNTS_COLLECTION].count_documents({})
    logger.info(f"Extracted {count:,} unique accounts")
    return count


def extract_banks(db) -> int:
    """Extract unique banks from transactions."""

    logger.info("Extracting banks from transactions...")

    pipeline = [
        {"$project": {"banks": ["$sender.bank_id", "$receiver.bank_id"]}},
        {"$unwind": "$banks"},
        {"$group": {
            "_id": "$banks",
            "transaction_count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "bank_id": "$_id",
            "transaction_count": 1
        }},
        {"$merge": {
            "into": BANKS_COLLECTION,
            "on": "bank_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert"
        }}
    ]

    db[TRANSACTIONS_COLLECTION].aggregate(pipeline, allowDiskUse=True)
    count = db[BANKS_COLLECTION].count_documents({})
    logger.info(f"Extracted {count:,} unique banks")
    return count


# ============================================================
# MAIN INGESTION FUNCTION
# ============================================================

def ingest_data(csv_path: str, batch_size: int = DEFAULT_BATCH_SIZE,
                resume: bool = True, skip_entities: bool = False) -> Dict[str, Any]:
    """
    Main ingestion function.

    Args:
        csv_path: Path to the HI-Small_Trans.csv file
        batch_size: Number of records per batch
        resume: If True, resume from last successful batch
        skip_entities: If True, skip account/bank extraction

    Returns:
        Dictionary with ingestion statistics
    """

    # Validate file exists
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Connect to MongoDB
    client = get_mongo_client()
    db = client[DATABASE_NAME]

    # Setup indexes
    setup_collections(db)

    # Check for resume point
    start_batch = 0
    if resume:
        start_batch = get_last_processed_batch(db)
        if start_batch > 0:
            logger.info(f"Resuming from batch {start_batch + 1}")

    # Statistics
    total_stats = {
        "total_processed": 0,
        "total_inserted": 0,
        "total_skipped": 0,
        "total_errors": 0,
        "batches_completed": 0,
        "start_time": datetime.utcnow()
    }

    # Process CSV in chunks
    batch_number = 0
    row_index = 0
    documents_buffer = []

    logger.info(f"Starting ingestion with batch_size={batch_size}")

    # Get total for progress bar
    total_rows = sum(1 for _ in open(csv_path, 'r')) - 1

    with tqdm(total=total_rows, desc="Ingesting", unit="rows") as pbar:
        for chunk in read_csv_in_chunks(csv_path, CHUNK_SIZE):
            for _, row in chunk.iterrows():
                # Skip rows if resuming
                if batch_number < start_batch:
                    row_index += 1
                    if row_index % batch_size == 0:
                        batch_number += 1
                    pbar.update(1)
                    continue

                # Transform row
                batch_id = f"batch_{batch_number:06d}"
                doc = transform_row(row, row_index, batch_id)
                documents_buffer.append(doc)
                row_index += 1
                pbar.update(1)

                # Process batch when buffer is full
                if len(documents_buffer) >= batch_size:
                    start_time = datetime.utcnow()

                    # Process batch
                    batch_stats = process_batch(db, documents_buffer, batch_id)

                    duration = (datetime.utcnow() - start_time).total_seconds()

                    # Log batch
                    log_batch(
                        db, batch_id, batch_number,
                        {
                            "processed": len(documents_buffer),
                            "inserted": batch_stats["inserted"],
                            "skipped": batch_stats["skipped"],
                            "start_time": start_time,
                            "duration": duration
                        },
                        status="completed",
                        start_row=row_index - len(documents_buffer),
                        end_row=row_index - 1
                    )

                    # Update totals
                    total_stats["total_processed"] += len(documents_buffer)
                    total_stats["total_inserted"] += batch_stats["inserted"]
                    total_stats["total_skipped"] += batch_stats["skipped"]
                    total_stats["total_errors"] += batch_stats["errors"]
                    total_stats["batches_completed"] += 1

                    # Log progress
                    logger.info(
                        f"Batch {batch_number}: {batch_stats['inserted']} inserted, "
                        f"{batch_stats['skipped']} skipped, {duration:.1f}s"
                    )

                    # Clear buffer and increment batch
                    documents_buffer = []
                    batch_number += 1

    # Process remaining documents
    if documents_buffer:
        batch_id = f"batch_{batch_number:06d}"
        start_time = datetime.utcnow()
        batch_stats = process_batch(db, documents_buffer, batch_id)
        duration = (datetime.utcnow() - start_time).total_seconds()

        log_batch(
            db, batch_id, batch_number,
            {
                "processed": len(documents_buffer),
                "inserted": batch_stats["inserted"],
                "skipped": batch_stats["skipped"],
                "start_time": start_time,
                "duration": duration
            },
            status="completed",
            start_row=row_index - len(documents_buffer),
            end_row=row_index - 1
        )

        total_stats["total_processed"] += len(documents_buffer)
        total_stats["total_inserted"] += batch_stats["inserted"]
        total_stats["total_skipped"] += batch_stats["skipped"]
        total_stats["batches_completed"] += 1

        logger.info(f"Final batch {batch_number}: {batch_stats['inserted']} inserted")

    # Extract entities
    if not skip_entities:
        logger.info("\nExtracting entities...")
        extract_accounts(db)
        extract_banks(db)

    # Final statistics
    total_stats["end_time"] = datetime.utcnow()
    total_stats["total_duration"] = (
        total_stats["end_time"] - total_stats["start_time"]
    ).total_seconds()

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("INGESTION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total processed:  {total_stats['total_processed']:,}")
    logger.info(f"Total inserted:   {total_stats['total_inserted']:,}")
    logger.info(f"Total skipped:    {total_stats['total_skipped']:,}")
    logger.info(f"Total errors:     {total_stats['total_errors']:,}")
    logger.info(f"Batches:          {total_stats['batches_completed']}")
    logger.info(f"Duration:         {total_stats['total_duration']:.1f} seconds")
    logger.info(f"Rate:             {total_stats['total_processed']/max(total_stats['total_duration'],1):.0f} rows/sec")
    logger.info("="*60)

    # Collection counts
    logger.info("\nCollection Statistics:")
    logger.info(f"  transactions: {db[TRANSACTIONS_COLLECTION].count_documents({}):,}")
    logger.info(f"  accounts:     {db[ACCOUNTS_COLLECTION].count_documents({}):,}")
    logger.info(f"  banks:        {db[BANKS_COLLECTION].count_documents({}):,}")

    # Laundering distribution
    laundering_count = db[TRANSACTIONS_COLLECTION].count_documents({"is_laundering": True})
    total_count = db[TRANSACTIONS_COLLECTION].count_documents({})
    logger.info(f"\nLaundering Distribution:")
    logger.info(f"  Suspicious: {laundering_count:,} ({100*laundering_count/max(total_count,1):.2f}%)")
    logger.info(f"  Normal:     {total_count - laundering_count:,}")

    client.close()
    return total_stats


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ingest IBM AML HI-Small dataset into MongoDB Atlas"
    )
    parser.add_argument(
        "--csv", "-c",
        type=str,
        default="HI-Small_Trans.csv",
        help="Path to HI-Small_Trans.csv file"
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Records per batch (default: {DEFAULT_BATCH_SIZE})"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from beginning, ignore previous progress"
    )
    parser.add_argument(
        "--skip-entities",
        action="store_true",
        help="Skip account/bank extraction"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection only"
    )

    args = parser.parse_args()

    if args.test:
        logger.info("Testing MongoDB connection...")
        try:
            client = get_mongo_client()
            db = client[DATABASE_NAME]
            logger.info(f"Database: {DATABASE_NAME}")
            logger.info(f"Collections: {db.list_collection_names()}")
            client.close()
            logger.info("Connection test successful!")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            sys.exit(1)
        return

    try:
        stats = ingest_data(
            csv_path=args.csv,
            batch_size=args.batch_size,
            resume=not args.no_resume,
            skip_entities=args.skip_entities
        )
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"{e}")
        logger.info("Download the dataset first:")
        logger.info("   kaggle datasets download -d ealtman2019/ibm-transactions-for-anti-money-laundering-aml")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise


if __name__ == "__main__":
    main()
