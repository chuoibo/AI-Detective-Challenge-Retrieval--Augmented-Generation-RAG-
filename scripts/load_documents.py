import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.services import DocumentService
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting document loading script")
    
    case_files_dir = settings.CASE_FILES_DIR
    if not os.path.exists(case_files_dir):
        logger.error(f"Case files directory not found: {case_files_dir}")
        logger.info("Creating directory...")
        os.makedirs(case_files_dir, exist_ok=True)
    
    case_files = [f for f in os.listdir(case_files_dir) if f.endswith('.txt')]
    if not case_files:
        logger.warning(f"No case files found in {case_files_dir}")
        logger.info("Please add case files to the directory before running this script.")
        return
    
    logger.info(f"Found {len(case_files)} case files: {', '.join(case_files)}")
    
    confirm = input("Do you want to proceed with loading these files? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Operation cancelled by user")
        return
    
    clear = input("Do you want to clear existing documents first? (y/n): ")
    
    document_service = DocumentService()
    
    if clear.lower() == 'y':
        logger.info("Clearing existing documents...")
        result = document_service.clear_documents()
        if not result["success"]:
            logger.error(f"Failed to clear documents: {result.get('error', 'Unknown error')}")
            return
        logger.info("Existing documents cleared successfully")
    
    logger.info("Loading documents...")
    result = document_service.load_all_documents()
    
    if result["success"]:
        logger.info(f"Successfully loaded {result.get('chunk_count', 0)} document chunks")
        logger.info("Document loading complete!")
    else:
        logger.error(f"Failed to load documents: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()