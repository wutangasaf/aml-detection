#!/usr/bin/env python3
"""
AML Regulatory Documents Vector Ingestion Pipeline
Extracts text from PDFs, chunks, embeds with OpenAI, uploads to MongoDB Atlas.
"""

import os
import re
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import certifi

# --- Configuration ---
BASE_DIR = Path("/Users/asaferez/Projects/aml/documents")
MONGODB_URI = "mongodb+srv://dev_db_user:EyMpA37VXGa3Kjmc@aml-research.sgpnzv8.mongodb.net/?appName=AML-Research"
DATABASE_NAME = "aml_db"
COLLECTION_NAME = "regulatory_docs"
VECTOR_INDEX_NAME = "vector_index"

# Chunking settings
CHUNK_SIZE = 500  # tokens (approx 4 chars per token)
CHUNK_OVERLAP = 50  # tokens overlap between chunks
CHARS_PER_TOKEN = 4  # rough estimate

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 100  # embeddings per batch

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def install_dependencies():
    """Install required packages if missing."""
    import subprocess
    import sys

    packages = [
        'pymupdf',  # PDF text extraction (fitz)
        'openai',
        'pymongo',
        'tiktoken',  # Token counting
        'python-docx',  # DOCX support
    ]

    for package in packages:
        try:
            __import__(package.replace('-', '_').split('[')[0])
        except ImportError:
            logger.info(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])


# Install dependencies first
install_dependencies()

import fitz  # PyMuPDF
import tiktoken
from openai import OpenAI
from pymongo import MongoClient
from pymongo.operations import UpdateOne

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def get_mongo_client():
    """Get MongoDB client with SSL fix for macOS."""
    return MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=30000,  # 30 seconds
        connectTimeoutMS=30000,
        socketTimeoutMS=60000,
        tlsCAFile=certifi.where()
    )


def get_openai_client():
    """Get OpenAI client, checking for API key."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Run:\n"
            "  export OPENAI_API_KEY='your-key-here'\n"
            "Or add to ~/.zshrc"
        )
    return OpenAI(api_key=api_key)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text_parts = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")

        doc.close()
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def extract_text_from_docx(docx_path: Path) -> str:
    """Extract text from DOCX file."""
    if not HAS_DOCX:
        logger.warning(f"python-docx not installed, skipping {docx_path}")
        return ""

    try:
        doc = DocxDocument(docx_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error extracting text from {docx_path}: {e}")
        return ""


def extract_text_from_txt(txt_path: Path) -> str:
    """Extract text from TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text from {txt_path}: {e}")
        return ""


def parse_combined_translation(file_path: Path) -> List[Dict[str, str]]:
    """
    Parse combined translated file into individual documents.
    Returns list of {source, content} dictionaries.
    """
    text = extract_text_from_txt(file_path)
    if not text:
        return []

    # Pattern matches document headers like:
    # ================================================================================
    # === SOURCE: filename (TRANSLATED TO ENGLISH) ===
    # ================================================================================
    pattern = r'={80}\n=== SOURCE: (.+?) (?:\(TRANSLATED TO ENGLISH\) )?===\n={80}\n'

    parts = re.split(pattern, text)
    documents = []

    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            source_name = parts[i].strip()
            content = parts[i + 1].strip()
            if content and len(content) > 100:  # Skip empty/tiny sections
                documents.append({
                    'source': source_name,
                    'content': content
                })

    return documents


def clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove page numbers and headers (common patterns)
    text = re.sub(r'\n\d+\s*\n', '\n', text)
    # Remove null characters
    text = text.replace('\x00', '')
    return text.strip()


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks.
    Returns list of {text, start_char, end_char, token_count}
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)

        # Find character positions (approximate)
        char_start = len(encoding.decode(tokens[:start])) if start > 0 else 0
        char_end = char_start + len(chunk_text)

        chunks.append({
            "text": chunk_text,
            "start_char": char_start,
            "end_char": char_end,
            "token_count": len(chunk_tokens)
        })

        # Move start, accounting for overlap
        start = end - overlap if end < len(tokens) else end

        # Prevent infinite loop
        if start >= len(tokens) - overlap:
            break

    return chunks


def generate_embeddings(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS
    )
    return [item.embedding for item in response.data]


def get_document_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from document path."""
    # Determine source category from folder
    parts = file_path.relative_to(BASE_DIR).parts
    source = parts[0] if len(parts) > 1 else "unknown"

    # Map folder names to proper source names
    source_map = {
        "fatf": "FATF",
        "eu": "EU",
        "eba": "EBA",
        "jmlsg": "JMLSG",
        "wolfsberg": "Wolfsberg Group",
        "basel": "Basel Committee",
        "us": "US (FinCEN/OCC)",
        "uk": "UK",
        "enforcement": "Enforcement",
        "typologies": "FATF Typologies",
        "impa": "IMPA",
        "israel": "Israel/IMPA",
    }

    # Check for typologies subfolder
    if len(parts) > 2 and parts[1] == "typologies":
        source = "FATF Typologies"
    else:
        source = source_map.get(source, source.upper())

    # Generate document ID from filename
    doc_id = hashlib.md5(file_path.name.encode()).hexdigest()[:12]

    return {
        "doc_id": doc_id,
        "filename": file_path.name,
        "source": source,
        "file_path": str(file_path.relative_to(BASE_DIR)),
        "file_size": file_path.stat().st_size,
    }


def process_document(file_path: Path, openai_client: OpenAI) -> List[Dict[str, Any]]:
    """Process a single document: extract, chunk, embed."""
    logger.info(f"Processing: {file_path.name}")

    # Extract text
    if file_path.suffix.lower() == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_path.suffix.lower() == '.docx':
        text = extract_text_from_docx(file_path)
    else:
        logger.warning(f"Unsupported file type: {file_path}")
        return []

    if not text or len(text) < 100:
        logger.warning(f"No/insufficient text extracted from {file_path.name}")
        return []

    text = clean_text(text)
    total_tokens = count_tokens(text)
    logger.info(f"  Extracted {len(text):,} chars, {total_tokens:,} tokens")

    # Get metadata
    metadata = get_document_metadata(file_path)

    # Chunk text
    chunks = chunk_text(text)
    logger.info(f"  Created {len(chunks)} chunks")

    # Generate embeddings in batches
    chunk_texts = [c["text"] for c in chunks]
    all_embeddings = []

    for i in range(0, len(chunk_texts), BATCH_SIZE):
        batch = chunk_texts[i:i + BATCH_SIZE]
        embeddings = generate_embeddings(openai_client, batch)
        all_embeddings.extend(embeddings)
        logger.info(f"  Embedded batch {i // BATCH_SIZE + 1}/{(len(chunk_texts) - 1) // BATCH_SIZE + 1}")

    # Create document records
    records = []
    for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
        record = {
            "_id": f"{metadata['doc_id']}_chunk_{i:04d}",
            "doc_id": metadata["doc_id"],
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk["text"],
            "token_count": chunk["token_count"],
            "embedding": embedding,
            "metadata": {
                "filename": metadata["filename"],
                "source": metadata["source"],
                "file_path": metadata["file_path"],
            },
            "ingested_at": datetime.utcnow(),
        }
        records.append(record)

    return records


def process_translated_documents(file_path: Path, openai_client: OpenAI) -> List[Dict[str, Any]]:
    """Process combined translated document file into multiple document entries."""
    logger.info(f"Processing translated file: {file_path.name}")

    # Parse into individual documents
    docs = parse_combined_translation(file_path)
    logger.info(f"  Found {len(docs)} documents in translation file")

    if not docs:
        return []

    all_records = []

    for doc_idx, doc in enumerate(docs):
        source_name = doc['source']
        content = doc['content']

        # Clean and validate content
        content = clean_text(content)
        if len(content) < 100:
            logger.warning(f"  Skipping {source_name} (too short)")
            continue

        total_tokens = count_tokens(content)
        logger.info(f"  [{doc_idx + 1}/{len(docs)}] {source_name}: {len(content):,} chars, {total_tokens:,} tokens")

        # Generate doc_id from source name
        doc_id = hashlib.md5(source_name.encode()).hexdigest()[:12]

        # Chunk text
        chunks = chunk_text(content)
        logger.info(f"    Created {len(chunks)} chunks")

        # Generate embeddings in batches
        chunk_texts = [c["text"] for c in chunks]
        all_embeddings = []

        for i in range(0, len(chunk_texts), BATCH_SIZE):
            batch = chunk_texts[i:i + BATCH_SIZE]
            embeddings = generate_embeddings(openai_client, batch)
            all_embeddings.extend(embeddings)

        # Create records
        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            record = {
                "_id": f"{doc_id}_chunk_{i:04d}",
                "doc_id": doc_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "text": chunk["text"],
                "token_count": chunk["token_count"],
                "embedding": embedding,
                "metadata": {
                    "filename": source_name,
                    "source": "Israel/IMPA",
                    "file_path": f"israel/{source_name}",
                    "translated_from": "Hebrew",
                },
                "ingested_at": datetime.utcnow(),
            }
            all_records.append(record)

    return all_records


def create_vector_index(db):
    """Create MongoDB Atlas Vector Search index."""
    collection = db[COLLECTION_NAME]

    # Check if index exists
    existing_indexes = list(collection.list_search_indexes())
    for idx in existing_indexes:
        if idx.get("name") == VECTOR_INDEX_NAME:
            logger.info(f"Vector index '{VECTOR_INDEX_NAME}' already exists")
            return

    # Create vector search index
    index_definition = {
        "name": VECTOR_INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": EMBEDDING_DIMENSIONS,
                    "similarity": "cosine"
                },
                {
                    "type": "filter",
                    "path": "metadata.source"
                }
            ]
        }
    }

    try:
        collection.create_search_index(index_definition)
        logger.info(f"Created vector search index: {VECTOR_INDEX_NAME}")
    except Exception as e:
        logger.warning(f"Could not create vector index (may need Atlas UI): {e}")
        logger.info("Create index manually in Atlas UI with:")
        logger.info(f"  Collection: {COLLECTION_NAME}")
        logger.info(f"  Index name: {VECTOR_INDEX_NAME}")
        logger.info(f"  Field: embedding, Dimensions: {EMBEDDING_DIMENSIONS}, Similarity: cosine")


def main():
    """Main ingestion pipeline."""
    logger.info("=" * 60)
    logger.info("AML REGULATORY DOCUMENTS VECTOR INGESTION")
    logger.info("=" * 60)

    # Initialize clients
    logger.info("Connecting to OpenAI...")
    openai_client = get_openai_client()

    logger.info("Connecting to MongoDB Atlas...")
    mongo_client = get_mongo_client()
    db = mongo_client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Find all documents
    doc_files = list(BASE_DIR.rglob("*.pdf")) + list(BASE_DIR.rglob("*.docx"))
    # Filter out download list and scripts
    doc_files = [f for f in doc_files if not f.name.startswith(("DOWNLOAD", "bulk_"))]

    logger.info(f"Found {len(doc_files)} documents to process")

    # Process each document
    total_chunks = 0
    successful_docs = 0

    for file_path in doc_files:
        try:
            # Check if already processed
            existing = collection.find_one({"metadata.filename": file_path.name})
            if existing:
                logger.info(f"SKIP: {file_path.name} already in database")
                continue

            records = process_document(file_path, openai_client)

            if records:
                # Bulk upsert
                operations = [
                    UpdateOne(
                        {"_id": r["_id"]},
                        {"$set": r},
                        upsert=True
                    )
                    for r in records
                ]
                result = collection.bulk_write(operations)
                total_chunks += len(records)
                successful_docs += 1
                logger.info(f"  Uploaded {len(records)} chunks to MongoDB")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            continue

    # Process Israeli translated documents
    israel_translated = BASE_DIR / "israel" / "aml_english_translated.txt"
    if israel_translated.exists():
        logger.info("")
        logger.info("Processing Israeli translated documents...")

        # Check if already processed
        existing = collection.find_one({"metadata.source": "Israel/IMPA"})
        if existing:
            logger.info("SKIP: Israeli documents already in database")
        else:
            try:
                records = process_translated_documents(israel_translated, openai_client)
                if records:
                    operations = [
                        UpdateOne(
                            {"_id": r["_id"]},
                            {"$set": r},
                            upsert=True
                        )
                        for r in records
                    ]
                    result = collection.bulk_write(operations)
                    total_chunks += len(records)
                    successful_docs += 1
                    logger.info(f"  Uploaded {len(records)} Israeli document chunks to MongoDB")
            except Exception as e:
                logger.error(f"Error processing Israeli documents: {e}")

    # Create vector index
    logger.info("")
    logger.info("Setting up vector search index...")
    create_vector_index(db)

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Documents processed: {successful_docs}")
    logger.info(f"Total chunks created: {total_chunks}")
    logger.info(f"Collection: {DATABASE_NAME}.{COLLECTION_NAME}")

    # Show collection stats
    doc_count = collection.count_documents({})
    logger.info(f"Total documents in collection: {doc_count}")


if __name__ == "__main__":
    main()
