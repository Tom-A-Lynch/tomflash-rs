# Long Term Memory Engine
# Objective: Stored memory. This would simulate world knowledge / general knowledge, and any significant interactions on the platform. In post maker, anytime we decide to make a post, we can score them for significance and store that as well. Based on short term memory, we retrieve any info from long term memory that is relevant and pass that to the post making context too. 

# Inputs:
# Vector embeddings of posts / replies, either in standard or graph format
# Maybe based on time

# Outputs:
# Text memory w/ significance score 

from typing import List, Dict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from openai import OpenAI

Base = declarative_base()

class LongTermMemory(Base):
    __tablename__ = "long_term_memories"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    embedding = Column(String, nullable=False)  # Store as JSON string
    significance_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def create_embedding(text: str, openai_api_key: str) -> List[float]:
    """
    Create an embedding for the given text using OpenAI's API.
    
    Args:
        text (str): Text to create an embedding for
        openai_api_key (str): OpenAI API key
    
    Returns:
        List[float]: Embedding vector
    """
    client = OpenAI(api_key=openai_api_key)
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def store_memory(db: Session, content: str, embedding: List[float], significance_score: float):
    """
    Store a new memory in the long-term memory database.
    
    Args:
        db (Session): Database session
        content (str): Memory content
        embedding (List[float]): Embedding vector
        significance_score (float): Significance score of the memory
    """
    new_memory = LongTermMemory(
        content=content,
        embedding=str(embedding),  # Convert to string for storage
        significance_score=significance_score
    )
    db.add(new_memory)
    db.commit()

def retrieve_relevant_memories(db: Session, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """
    Retrieve relevant memories based on the query embedding.
    
    Args:
        db (Session): Database session
        query_embedding (List[float]): Query embedding vector
        top_k (int): Number of top memories to retrieve
    
    Returns:
        List[Dict]: List of relevant memories with their content and significance score
    """
    all_memories = db.query(LongTermMemory).all()
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    similarities = [
        (memory, cosine_similarity(query_embedding, eval(memory.embedding)))
        for memory in all_memories
    ]
    
    sorted_memories = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
    
    return [
        {"content": memory.content, "significance_score": memory.significance_score}
        for memory, _ in sorted_memories
    ]