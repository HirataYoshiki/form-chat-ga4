from google.cloud import aiplatform_v1beta1 as aiplatform
from backend.config import settings
import logging
from typing import List, Optional # Added List, Optional
from fastapi.concurrency import run_in_threadpool # Added run_in_threadpool

logger = logging.getLogger(__name__)

def get_rag_data_service_client(project_id: str = None, location: str = None) -> aiplatform.VertexRagDataServiceClient:
    """Initializes and returns a VertexRagDataServiceClient."""
    p_id = project_id or settings.PROJECT_ID
    loc = location or settings.VERTEX_AI_REGION

    if not p_id:
        raise ValueError("Google Cloud Project ID is not set.")
    if not loc:
        raise ValueError("Vertex AI Region is not set.")

    client_options = {"api_endpoint": f"{loc}-aiplatform.googleapis.com"}
    try:
        client = aiplatform.VertexRagDataServiceClient(client_options=client_options)
        logger.info(f"VertexRagDataServiceClient initialized for project: {p_id}, location: {loc}")
        return client
    except Exception as e:
        logger.error(f"Error initializing VertexRagDataServiceClient: {e}")
        raise

def get_rag_service_client(project_id: str = None, location: str = None) -> aiplatform.VertexRagServiceClient:
    """Initializes and returns a VertexRagServiceClient."""
    p_id = project_id or settings.PROJECT_ID
    loc = location or settings.VERTEX_AI_REGION

    if not p_id:
        raise ValueError("Google Cloud Project ID is not set.")
    if not loc:
        raise ValueError("Vertex AI Region is not set.")

    client_options = {"api_endpoint": f"{loc}-aiplatform.googleapis.com"}
    try:
        client = aiplatform.VertexRagServiceClient(client_options=client_options)
        logger.info(f"VertexRagServiceClient initialized for project: {p_id}, location: {loc}")
        return client
    except Exception as e:
        logger.error(f"Error initializing VertexRagServiceClient: {e}")
        raise

async def create_rag_corpus(
    display_name: str,
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = "RAG Corpus for tenant"
) -> Optional[str]:
    """
    Creates a new RAG Corpus in Vertex AI and waits for its completion.
    Returns the resource name (ID) of the created RagCorpus if successful, else None.
    """
    p_id = project_id or settings.PROJECT_ID
    loc = location or settings.VERTEX_AI_REGION

    if not p_id or not loc:
        logger.error("Project ID or Location is not configured for creating RAG corpus.")
        return None

    logger.info(f"Creating RAG Corpus with display_name='{display_name}' in {p_id}/{loc}")

    try:
        sync_client = get_rag_data_service_client(project_id=p_id, location=loc)

        parent_path = f"projects/{p_id}/locations/{loc}"

        rag_corpus_config = aiplatform.RagCorpus(
            display_name=display_name,
            description=description
            # rag_embedding_model_config can be specified if needed, otherwise defaults.
        )

        create_corpus_request = aiplatform.CreateRagCorpusRequest(
            parent=parent_path,
            rag_corpus=rag_corpus_config
        )

        def lro_create_corpus():
            operation = sync_client.create_rag_corpus(request=create_corpus_request)
            logger.info(f"CreateRagCorpus LRO started: {operation.operation.name}. Waiting for completion (timeout 300s)...")
            # Wait for the LRO to complete. Timeout in seconds.
            created_corpus = operation.result(timeout=300)
            return created_corpus

        created_corpus_obj = await run_in_threadpool(lro_create_corpus)

        if created_corpus_obj and created_corpus_obj.name:
            logger.info(f"Successfully created RAG Corpus: {created_corpus_obj.name} with display_name: {created_corpus_obj.display_name}")
            return created_corpus_obj.name
        else:
            logger.error(f"RAG Corpus creation LRO completed but returned no name for display_name {display_name}.")
            return None
    except Exception as e:
        logger.error(f"Error creating RAG Corpus with display_name {display_name}: {e}", exc_info=True)
        return None

# Placeholder for import_files_to_rag_corpus function
async def import_files_to_rag_corpus(rag_corpus_name: str, gcs_uris: list[str], parsing_config: dict, chunking_config: dict):
    # To be implemented:
    # 1. Get client
    # 2. Construct ImportRagFilesConfig (gcs_source, rag_file_parsing_config, rag_file_chunking_config)
    # 3. Construct ImportRagFilesRequest (parent=rag_corpus_name, import_rag_files_config)
    # 4. Call client.import_rag_files(request) - this is a long-running operation
    # 5. Handle the operation
    pass

# Placeholder for retrieve_rag_contexts function
async def retrieve_rag_contexts(rag_corpus_names: list[str], query: str, similarity_top_k: int = 5):
    # To be implemented:
    # 1. Get client
    # 2. Construct RagQuery object (text=query, similarity_top_k)
    # 3. Construct RetrieveContextsRequest (parent=rag_corpus_names[0] for now, query)
    #    (Note: RetrieveContextsRequest takes a single parent, but can query multiple corpora if engine is configured so.
    #     For direct SDK use with specific corpus, parent is likely the corpus name)
    # 4. Call client.retrieve_contexts(request)
    # 5. Process and return contexts
    # Placeholder implementation - replace with actual logic
    logger.info(f"Retrieving RAG contexts for corpus '{rag_corpus_names[0]}' with query: '{query[:50]}...'")

    p_id = project_id or settings.PROJECT_ID
    loc = location or settings.VERTEX_AI_REGION

    if not rag_corpus_names or not rag_corpus_names[0]: # Simplified to use first corpus for now
        logger.error("RAG Corpus ID/Name is required.")
        return []

    rag_corpus_id = rag_corpus_names[0] # Use the first one for now

    try:
        sync_client = get_rag_service_client(project_id=p_id, location=loc)
        rag_query = aiplatform.RagQuery(text=query, similarity_top_k=similarity_top_k)

        request_parent = f"projects/{p_id}/locations/{loc}"
        rag_resources = [aiplatform.RagResource(rag_corpus=rag_corpus_id)]

        retrieve_contexts_request = aiplatform.RetrieveContextsRequest(
            parent=request_parent,
            rag_resources=rag_resources,
            query=rag_query,
        )

        response = await run_in_threadpool(sync_client.retrieve_contexts, request=retrieve_contexts_request)

        contexts = []
        if response and response.contexts and response.contexts.contexts:
            for context_item in response.contexts.contexts:
                contexts.append(context_item.text)

        logger.info(f"Retrieved {len(contexts)} contexts for query '{query[:50]}...' from corpus {rag_corpus_id}")
        return contexts

    except Exception as e:
        logger.error(f"Error retrieving RAG contexts for corpus {rag_corpus_id}: {e}", exc_info=True)
        return []


if __name__ == '__main__':
    # Example usage (requires GOOGLE_APPLICATION_CREDENTIALS and other .env settings)
    # Ensure .env has PROJECT_ID, VERTEX_AI_REGION
    # This is for local testing of client initialization
    import time # Added for timestamp_micros in placeholder send_ga4_event
    from typing import List, Dict, Any, Optional # Added for placeholder send_ga4_event
    logging.basicConfig(level=logging.INFO)
    try:
        data_client = get_rag_data_service_client()
        logger.info(f"Data client: {data_client}")
        rag_client = get_rag_service_client()
        logger.info(f"RAG service client: {rag_client}")
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
