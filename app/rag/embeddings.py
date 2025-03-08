import os
import glob
import openai
from typing import List, Dict, Any
import tiktoken
from app.core.config import settings


class EmbeddingProcessor:
    def __init__(self):

        self.client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

        self.model = settings.EMBEDDING_MODEL
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def load_case_files(self) -> List[Dict[str, Any]]:
        """Load all case files from the case_files directory."""
        case_files = []
        file_pattern = os.path.join(settings.CASE_FILES_DIR, "*.txt")
        
        for file_path in glob.glob(file_pattern):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                file_name = os.path.basename(file_path)
                case_files.append({
                    "id": file_name,
                    "content": content,
                    "metadata": {
                        "source": file_path,
                        "file_name": file_name
                    }
                })
        
        return case_files
    
    def chunk_text(self, text: str) -> List[str]:
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        i = 0
        while i < len(tokens):
            chunk_end = min(i + self.chunk_size, len(tokens))
            chunk = self.tokenizer.decode(tokens[i:chunk_end])
            chunks.append(chunk)
            
            i += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                input=texts, 
                model=self.model
            )
            
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            raise
    
    def process_case_files(self) -> List[Dict[str, Any]]:
        case_files = self.load_case_files()
        all_chunks = []
        
        for case_file in case_files:
            chunks = self.chunk_text(case_file["content"])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{case_file['id']}_chunk_{i}"
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        **case_file["metadata"],
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
        
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            texts = [chunk["text"] for chunk in batch]
            embeddings = self.create_embeddings(texts)
            
            for j, embedding in enumerate(embeddings):
                all_chunks[i + j]["embedding"] = embedding
        
        return all_chunks