import os
import numpy as np
from google import genai
from google.genai import types
import faiss
import pickle
from typing import List, Tuple
from pathlib import Path

# Configure Gemini API with new SDK
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set. Please add it to .env or system environment variables.")
client = genai.Client(api_key=api_key)

class EmbeddingGenerator:
    def __init__(self, index_path: str = "vector_index"):
        """Initialize the embedding generator with FAISS index management using Gemini embeddings.
        
        Args:
            index_path: Directory to save/load FAISS index and metadata
        """
        self.model_name = "gemini-embedding-001"
        self.index_path = Path(index_path)
        self.index = None
        self.chunks = []
        self.dimension = None  # Will be set dynamically after first embedding
        
        # Create index directory if it doesn't exist
        self.index_path.mkdir(exist_ok=True)
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text (used for queries).
        
        Args:
            text: Single text to embed
            
        Returns:
            numpy array embedding (float32)
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            result = client.models.embed_content(
                model=self.model_name,
                contents=[text]
            )
            vec = np.array(result.embeddings[0].values, dtype="float32")
            self.dimension = len(vec)
            return vec
            
        except Exception as e:
            raise RuntimeError(f"Error generating embeddings with Gemini: {e}")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts using Gemini Embeddings API.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            numpy array of embeddings (float32)
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        vectors = []
        
        try:
            result = client.models.embed_content(
                model=self.model_name,
                contents=texts
            )
            
            for e in result.embeddings:
                vectors.append(np.array(e.values, dtype="float32"))
            
            # Set dimension from first embedding
            self.dimension = len(vectors[0]) if vectors else 0
            
            # Stack embeddings into a single array
            if vectors:
                return np.vstack(vectors)
            else:
                return np.array([], dtype="float32")
            
        except Exception as e:
            raise RuntimeError(f"Error generating embeddings with Gemini: {e}")
    
    def create_index(self, texts: List[str]) -> None:
        """Create a new FAISS index from text chunks.
        
        Args:
            texts: List of text chunks
        """
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Create FAISS index (IndexFlatIP for cosine similarity with normalized vectors)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Add embeddings to index
        self.index.add(embeddings)
        
        # Store chunks for retrieval
        self.chunks = texts.copy()
        
        # Save to disk
        self.save_index()
    
    def update_index(self, new_texts: List[str]) -> None:
        """Update existing FAISS index with new text chunks.
        
        Args:
            new_texts: New text chunks to add
        """
        if self.index is None:
            self.load_index()
        
        if self.index is None:
            # No existing index, create new one
            self.create_index(new_texts)
            return
        
        # Generate embeddings for new texts
        new_embeddings = self.generate_embeddings(new_texts)
        
        # Add to existing index
        self.index.add(new_embeddings)
        
        # Update chunks list
        self.chunks.extend(new_texts)
        
        # Save updated index
        self.save_index()
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar chunks using the query.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of tuples (chunk_text, similarity_score)
        """
        if self.index is None:
            self.load_index()
        
        if self.index is None or len(self.chunks) == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.generate_single_embedding(query)
        
        # Search in FAISS index
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            min(top_k, len(self.chunks))
        )
        
        # Prepare results with similarity scores
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks) and idx >= 0:
                results.append((self.chunks[idx], float(score)))
        
        return results
    
    def save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            return
        
        # Save FAISS index
        faiss_path = self.index_path / "faiss.index"
        faiss.write_index(self.index, str(faiss_path))
        
        # Save chunks and metadata
        metadata = {
            'chunks': self.chunks,
            'model_name': self.model_name,
            'dimension': self.dimension
        }
        
        metadata_path = self.index_path / "metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
    
    def load_index(self) -> bool:
        """Load FAISS index and metadata from disk.
        
        Returns:
            True if successfully loaded, False otherwise
        """
        faiss_path = self.index_path / "faiss.index"
        metadata_path = self.index_path / "metadata.pkl"
        
        if not faiss_path.exists() or not metadata_path.exists():
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(faiss_path))
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.chunks = metadata['chunks']
            self.model_name = metadata.get('model_name', "gemini-embedding-001")
            self.dimension = metadata['dimension']
            
            return True
            
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def get_index_stats(self) -> dict:
        """Get statistics about the current index.
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            self.load_index()
        
        if self.index is None:
            return {'total_chunks': 0, 'index_size': 0}
        
        return {
            'total_chunks': len(self.chunks),
            'index_size': self.index.ntotal,
            'dimension': self.dimension,
            'model': self.model_name
        }
    
    def clear_index(self) -> None:
        """Clear the current index and remove files from disk."""
        self.index = None
        self.chunks = []
        self.dimension = None
        
        # Remove files
        faiss_path = self.index_path / "faiss.index"
        metadata_path = self.index_path / "metadata.pkl"
        
        for path in [faiss_path, metadata_path]:
            if path.exists():
                path.unlink()
