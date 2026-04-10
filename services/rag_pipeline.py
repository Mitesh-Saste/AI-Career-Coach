import os
import time
from typing import List, Dict, Optional
from services.resume_parser import extract_text_from_pdf
from services.chunker import chunk_text
from services.embeddings import EmbeddingGenerator
from google import genai
from google.genai import types

class RAGPipeline:
    def __init__(self, vector_index_path: str = "vector_index"):
        """Initialize RAG pipeline with Google Gemini client and embedding generator.
        
        Args:
            vector_index_path: Directory for FAISS index storage
        """
        self.vector_index_path = vector_index_path
        self.embedding_generator = EmbeddingGenerator(index_path=vector_index_path)
        self.resume_text = ""
        
        # Initialize Google Gemini client with new SDK
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        
    def process_resume(self, pdf_path: str) -> str:
        """Process resume: extract text, chunk, embed, and store in FAISS.
        
        Args:
            pdf_path: Path to the PDF resume file
            
        Returns:
            Extracted resume text
        """
        # Extract text from PDF
        self.resume_text = extract_text_from_pdf(pdf_path)
        
        if not self.resume_text:
            raise ValueError("No text could be extracted from the PDF")
        
        # Chunk the text
        chunks = chunk_text(self.resume_text)
        
        if not chunks:
            raise ValueError("No chunks could be created from the resume text")
        
        # Create FAISS index with embeddings
        self.embedding_generator.create_index(chunks)
        
        return self.resume_text
    
    def query(self, user_query: str, top_k: int = 3, max_tokens: int = 1000) -> Dict[str, any]:
        """Process user query using RAG pipeline and return AI response.
        
        Args:
            user_query: User's question about their career/resume
            top_k: Number of relevant chunks to retrieve
            max_tokens: Maximum tokens for Gemini response (note: Gemini handles this automatically)
            
        Returns:
            Dictionary containing AI response and metadata
        """
        if not user_query.strip():
            raise ValueError("Query cannot be empty")
        
        # Search for relevant chunks
        search_results = self.embedding_generator.search(user_query, top_k=top_k)
        
        # Extract chunks and scores
        retrieved_chunks = [result[0] for result in search_results]
        similarity_scores = [result[1] for result in search_results]
        
        # Build context from retrieved chunks
        context = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No relevant context found."
        
        # Get resume summary (first 500 characters)
        resume_summary = self.get_resume_summary()
        
        # Build the prompt template
        prompt = self._build_prompt(user_query, context, resume_summary)
        
        # Call Google Gemini with optimized generation config using new SDK
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
        try:
            resp = None
            last_error = None
            for model in models_to_try:
                for attempt in range(2):
                    try:
                        resp = self.client.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                max_output_tokens=3000,
                                temperature=0.6,
                                top_p=0.9,
                                top_k=40
                            ),
                        )
                        break
                    except Exception as e:
                        last_error = e
                        if "503" in str(e) and attempt < 1:
                            time.sleep(2)
                            continue
                        if "429" in str(e):
                            raise  # quota exhausted, no point retrying other attempts
                        break
                if resp is not None:
                    break
            if resp is None:
                raise last_error
            
            ai_response = resp.text
            
            # Debug: Check if response was truncated
            if hasattr(resp, 'candidates') and resp.candidates:
                candidate = resp.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    print(f"Gemini finish reason: {candidate.finish_reason}")
                    if candidate.finish_reason != 'STOP':
                        print(f"Warning: Response may be truncated. Finish reason: {candidate.finish_reason}")
                        # If truncated, add a note to the response
                        if candidate.finish_reason == 'MAX_TOKENS':
                            ai_response += "\n\n[Response was truncated due to length. Please ask a more specific question for a complete answer.]"
            
            return {
                "answer": ai_response,
                "retrieved_chunks": retrieved_chunks,
                "similarity_scores": similarity_scores,
                "context_used": len(retrieved_chunks),
                "tokens_used": None  # Gemini doesn't provide token usage in the same way
            }
            
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                import re
                delay = re.search(r'retry in (\d+)', err)
                wait = f" Please retry in {delay.group(1)} seconds." if delay else ""
                raise Exception(f"API quota exceeded for all available models.{wait}")
            raise Exception(f"Error calling Google Gemini API: {err}")
    
    def _build_prompt(self, user_query: str, context: str, resume_summary: str) -> str:
        """Build the prompt template for Google Gemini.
        
        Args:
            user_query: User's question
            context: Retrieved resume context
            resume_summary: Summary of the resume
            
        Returns:
            Formatted prompt string
        """
        prompt_template = """You are an AI Career Coach. The user has uploaded this resume. Use the retrieved resume context to answer their question. If the answer is not in the resume, provide general career advice.

RESUME SUMMARY:
{resume_summary}

RETRIEVED RESUME CONTEXT:
{context}

USER QUESTION:
{user_query}

INSTRUCTIONS:
- Provide specific, actionable career advice
- Reference specific details from the resume when relevant
- If the resume doesn't contain enough information, provide general guidance
- Be encouraging and professional
- Focus on practical next steps
- Provide the full detailed answer without skipping or stopping early
- Do not truncate the response - provide complete information
- Include specific examples and recommendations
- Structure your response with clear sections when appropriate
- Use formatting (bullet points, numbered lists) for clarity
- Aim for comprehensive, thorough responses

RESPONSE:"""
        
        return prompt_template.format(
            resume_summary=resume_summary,
            context=context,
            user_query=user_query
        )
    
    def get_resume_summary(self, max_length: int = 500) -> str:
        """Get a summary of the resume text.
        
        Args:
            max_length: Maximum length of summary
            
        Returns:
            Resume summary string
        """
        if not self.resume_text:
            # Try to load from saved data
            if self.embedding_generator.load_index():
                # Resume text should be loaded with the index
                pass
        
        if not self.resume_text:
            return "No resume text available."
        
        summary = self.resume_text[:max_length]
        if len(self.resume_text) > max_length:
            summary += "..."
        
        return summary
    
    def get_pipeline_stats(self) -> Dict[str, any]:
        """Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with pipeline statistics
        """
        index_stats = self.embedding_generator.get_index_stats()
        
        return {
            "resume_loaded": bool(self.resume_text),
            "resume_length": len(self.resume_text) if self.resume_text else 0,
            "resume_text": self.resume_text,
            "index_stats": index_stats,
            "model_name": self.embedding_generator.model_name
        }
    
    def clear_pipeline(self) -> None:
        """Clear all data from the pipeline."""
        self.resume_text = ""
        self.embedding_generator.clear_index()
    
    def load_existing_index(self) -> bool:
        """Load existing FAISS index if available.
        
        Returns:
            True if index was loaded successfully
        """
        return self.embedding_generator.load_index()
