"""
RAG System Seeder

Seeds RAG collections and scans existing documents.
"""
import os
import hashlib
from datetime import datetime


def initialize_rag_system(db):
    """
    Initialize RAG system with default collections and scan existing documents.
    This runs on every app startup but uses idempotent checks.

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import RAGCollection, RAGDocument

    print("\n" + "="*60)
    print("Initializing RAG Document Management System...")
    print("="*60)

    # Create default collection if it doesn't exist
    default_collection = RAGCollection.query.filter_by(name='general').first()

    if not default_collection:
        default_collection = RAGCollection(
            name='general',
            display_name='Allgemeine Dokumente',
            description='Standard-Sammlung für allgemeine RAG-Dokumente',
            icon='📚',
            color='#4CAF50',
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            chunk_size=1000,
            chunk_overlap=200,
            retrieval_k=4,
            is_active=True,
            is_public=True,
            created_by='system',
            chroma_collection_name='llars_general_sentence-transformers_all-MiniLM-L6-v2'
        )
        db.session.add(default_collection)
        db.session.commit()
        print("✅ Created default collection: 'general'")
    else:
        print("✅ Default collection 'general' already exists")

    # Scan existing documents in /app/rag_docs/ and register them in database
    rag_docs_path = '/app/rag_docs'

    if not os.path.exists(rag_docs_path):
        print(f"⚠️  RAG docs directory not found: {rag_docs_path}")
        print("="*60)
        return

    # Get all PDF files
    existing_files = []
    for filename in os.listdir(rag_docs_path):
        if filename.endswith(('.pdf', '.txt', '.md')) and not filename.startswith('.'):
            existing_files.append(filename)

    if not existing_files:
        print(f"ℹ️  No documents found in {rag_docs_path}")
        print("="*60)
        return

    print(f"\n📄 Found {len(existing_files)} documents in {rag_docs_path}")
    print("-" * 60)

    registered_count = 0
    updated_count = 0

    for filename in sorted(existing_files):
        file_path = os.path.join(rag_docs_path, filename)

        try:
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            # Get file size
            file_size = os.path.getsize(file_path)

            # Check if document already exists by hash
            existing_doc = RAGDocument.query.filter_by(file_hash=file_hash).first()

            if existing_doc:
                # Document exists, just update metadata if needed
                # Only set default collection if no collection is assigned
                # Don't overwrite collection_id for documents created by crawler with specific collection
                if existing_doc.collection_id is None:
                    existing_doc.collection_id = default_collection.id
                    updated_count += 1
                # DON'T auto-set pending to indexed - let the embedding worker handle it
                # Documents need actual embeddings before being marked as indexed
                continue

            # Determine MIME type
            if filename.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif filename.endswith('.txt'):
                mime_type = 'text/plain'
            elif filename.endswith('.md'):
                mime_type = 'text/markdown'
            else:
                mime_type = 'application/octet-stream'

            # Create new document entry
            new_doc = RAGDocument(
                filename=filename,
                original_filename=filename,
                file_path=file_path,
                file_size_bytes=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                title=filename.replace('_', ' ').replace('.pdf', '').replace('.txt', '').replace('.md', ''),
                language='de',
                status='indexed',  # Mark as indexed since they exist in the system
                collection_id=default_collection.id,
                embedding_model='sentence-transformers/all-MiniLM-L6-v2',
                is_public=True,
                uploaded_by='system',
                uploaded_at=datetime.now(),
                indexed_at=datetime.now()
            )

            db.session.add(new_doc)
            registered_count += 1

        except Exception as e:
            print(f"⚠️  Error processing {filename}: {str(e)}")
            continue

    # Commit all changes
    if registered_count > 0 or updated_count > 0:
        db.session.commit()
        print(f"✅ Registered {registered_count} new documents")
        if updated_count > 0:
            print(f"✅ Updated {updated_count} existing documents")
    else:
        print("ℹ️  All documents already registered in database")

    # Update collection statistics for ALL collections (not just default)
    all_collections = RAGCollection.query.all()
    total_all_docs = 0
    total_all_size = 0

    for collection in all_collections:
        doc_count = RAGDocument.query.filter_by(collection_id=collection.id).count()
        size_bytes = db.session.query(
            db.func.sum(RAGDocument.file_size_bytes)
        ).filter_by(collection_id=collection.id).scalar() or 0

        collection.document_count = doc_count
        collection.total_size_bytes = size_bytes
        total_all_docs += doc_count
        total_all_size += size_bytes

    db.session.commit()

    print(f"\n📊 Collection Statistics:")
    print(f"   - Total Collections: {len(all_collections)}")
    print(f"   - Total Documents: {total_all_docs}")
    print(f"   - Total Size: {total_all_size / (1024*1024):.2f} MB")
    print("="*60)
    print("RAG Document Management System initialized successfully!")
    print("="*60 + "\n")
