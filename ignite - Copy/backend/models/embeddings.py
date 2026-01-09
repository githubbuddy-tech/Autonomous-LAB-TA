"""Embedding models for RAG"""
import numpy as np
from typing import List, Optional
import hashlib

class CodeEmbedding:
    """Generate embeddings for code"""
    
    @staticmethod
    def simple_embedding(code: str) -> np.ndarray:
        """Simple embedding using hash-based approach"""
        # Create a deterministic hash-based embedding
        hash_val = hashlib.sha256(code.encode()).digest()
        # Convert first 384 bytes to vector (for all-MiniLM-L6-v2 compatibility)
        embedding = np.frombuffer(hash_val, dtype=np.float32)
        
        # Ensure proper shape (384 dimensions)
        if len(embedding) < 384:
            embedding = np.pad(embedding, (0, 384 - len(embedding)), mode='constant')
        elif len(embedding) > 384:
            embedding = embedding[:384]
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
    
    @staticmethod
    def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have same dimensions")
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))