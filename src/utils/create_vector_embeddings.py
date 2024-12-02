from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex
import os
from dotenv import load_dotenv
from .logger_config import logger

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger = logger(__name__, 'app.log', level='DEBUG')

def create_vector_embeddings_data():
    """
    Creates vector embeddings from PDF files and stores them in a vector store.
    Returns the vector index if successful, None if vector store already exists.
    """
    try:
        logger.info("Starting vector embeddings creation process...")
        pdf_output_dir = "src/data/pdf_files"
        vector_store_dir = "src/data/vector_store"

        if not os.path.exists(pdf_output_dir):
            logger.error(f"PDF directory {pdf_output_dir} does not exist")
            raise FileNotFoundError(f"PDF directory {pdf_output_dir} does not exist")

        if os.path.exists(vector_store_dir):
            logger.info("Vector store already exists, skipping creation...")
            return None

        logger.info("Loading PDF files into memory...")
        documents = SimpleDirectoryReader(input_dir=pdf_output_dir).load_data()
        
        if not documents:
            logger.warning("No documents found in PDF directory")
            return None

        logger.debug(f"Loaded {len(documents)} documents")
        
        splitter = SentenceSplitter(chunk_size=1024)
        nodes = splitter.get_nodes_from_documents(documents)
        logger.debug(f"Created {len(nodes)} nodes from documents")

        Settings.llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
        Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=OPENAI_API_KEY)

        logger.info("Creating Vector Store Index...")
        vector_index = VectorStoreIndex(nodes)
        vector_index.storage_context.persist(vector_store_dir)
        logger.info("Successfully created and persisted vector store")

        return vector_index

    except Exception as e:
        logger.error(f"Error creating vector embeddings: {str(e)}", exc_info=True)
        raise
