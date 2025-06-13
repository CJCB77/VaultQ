from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import(
    Document
)
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

import logging

log = logging.getLogger(__name__)
from pathlib import Path


@shared_task(bind=True)
def process_document_task(self, doc_id: int):
    """
    Celery task to:
    1) Mark doc PROCCESING
    2) Load & chunk
    3) embed & upsert into project's Chroma store
    """
    log.info(f"Starting processing for doc {doc_id}")
    try:
        doc = Document.objects.get(pk=doc_id)
        # 1) Mark as processing
        doc.processing_status = Document.ProcessingStatus.PROCESSING
        doc.save(update_fields=['processing_status'])

        # Prepare loader based on extension
        path = doc.file.path
        loader = (
            PyPDFLoader(path) 
            if path.lower().endswith('.pdf')
            else TextLoader(path)
        )
        pages = loader.load()

        # 2) Chunk
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(pages)

        # 3) Embedding & Chroma upsert
        # Ensure chroma db exists
        coll_name = doc.project.chroma_collection
        if not coll_name:
            coll_name = f"proj_{doc.project.id}_{timezone.now().timestamp():.0f}"
            doc.project.chroma_collection = coll_name
            doc.project.save(update_fields=["chroma_collection"])
        
        vectordir = Path(settings.CHROMA_ROOT) / "projects" / str(doc.project.id)
        vectordir.mkdir(parents=True, exist_ok=True)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(vectordir),
            collection_name=coll_name
        )

        # 4) Finalize 
        doc.chunks_count = len(chunks)
        doc.processing_status = Document.ProcessingStatus.COMPLETED
        doc.save(update_fields=["chunks_count", "processing_status"])

        return {
            'document_id': doc_id,
            'chunks_processed': len(chunks),
            'collection': coll_name
        }

    except Exception as e:
        # mark failure
        log.exception(f"Error processing doc {doc_id}")
        doc.processing_status = Document.ProcessingStatus.FAILED
        doc.save(update_fields=["processing_status"])
        # re-raise so celery knows it failed
        raise 