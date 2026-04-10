from typing import List
import re

def chunk_text(
    text: str, 
    chunk_size: int = 250, 
    chunk_overlap: int = 50
) -> List[str]:
    """Split text into chunks of approximately 200-300 tokens using simple text splitting.
    
    Args:
        text: Raw text to be chunked
        chunk_size: Target chunk size in words (approximates tokens)
        chunk_overlap: Number of overlapping words between chunks
    
    Returns:
        List of text chunks that preserve meaning and context
    """
    # Split text into sentences first
    sentences = _split_into_sentences(text)
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        sentence_words = len(sentence.split())
        
        # If adding this sentence would exceed chunk size, finalize current chunk
        if current_word_count + sentence_words > chunk_size and current_chunk:
            chunk_text = ' '.join(current_chunk)
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
            
            # Start new chunk with overlap
            overlap_words = chunk_overlap
            overlap_sentences = []
            temp_word_count = 0
            
            # Add sentences from the end of current chunk for overlap
            for i in range(len(current_chunk) - 1, -1, -1):
                sentence_word_count = len(current_chunk[i].split())
                if temp_word_count + sentence_word_count <= overlap_words:
                    overlap_sentences.insert(0, current_chunk[i])
                    temp_word_count += sentence_word_count
                else:
                    break
            
            current_chunk = overlap_sentences + [sentence]
            current_word_count = sum(len(s.split()) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_word_count += sentence_words
    
    # Add the last chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if chunk_text.strip():
            chunks.append(chunk_text.strip())
    
    # Filter out very short chunks
    filtered_chunks = [chunk for chunk in chunks if len(chunk.split()) > 10]
    
    return filtered_chunks

def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple regex patterns."""
    # Simple sentence splitting pattern
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    
    # Split by the pattern
    sentences = re.split(sentence_pattern, text)
    
    # Clean up sentences
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            cleaned_sentences.append(sentence)
    
    # If no sentences found (no proper punctuation), split by newlines
    if len(cleaned_sentences) <= 1:
        lines = text.split('\n')
        cleaned_sentences = [line.strip() for line in lines if line.strip()]
    
    return cleaned_sentences
