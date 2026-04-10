# AI Career Coach - Complete Development Prompts

This document contains all the prompts used to build the AI Career Coach application from start to finish, including troubleshooting and enhancements.

## 🏗️ Phase 1: Initial Project Scaffold

### Prompt 1 — Create the Full Project Scaffold

Create a complete production‑ready project scaffold for a Flask-based RAG application called "AI Career Coach".

The app must contain:
- a resume upload page (index.html)
- a chatbot page (chatbot.html)
- a backend RAG pipeline that:
    - extracts PDF text using PyPDF2
    - chunks text into smaller groups using LangChain
    - generates embeddings using SentenceTransformers ("all-MiniLM-L6-v2")
    - stores and retrieves vectors using FAISS local index
- a chatbot system using OpenAI GPT‑4o‑mini chat completion API
- a prompt template that includes:
    - the resume summary
    - the retrieved context
    - the user's question

Create a folder structure:
services/chunker.py  
services/embeddings.py  
services/rag_pipeline.py  
services/resume_parser.py  
uploads/  
vector_index/  
templates/  
static/  

Also generate:
- app.py with full Flask routing
- requirements.txt with all necessary libraries
- basic CSS file
Make everything production‑ready and cleanly modularized.

## 🔧 Phase 2: Core Service Components

### Prompt 2 — Generate resume_parser.py

Generate the complete code for services/resume_parser.py.
This file should:

- Load PDF files using PyPDF2
- Extract clean text
- Remove extra whitespace
- Return one long string

Optimize extraction for complex resume layouts.

### Prompt 3 — Generate chunker.py

Generate the complete code for services/chunker.py.
The module must:

- Accept raw text
- Split text into chunks of 200–300 tokens using RecursiveCharacterTextSplitter
- Return a list of chunk strings

Make sure chunking is clean and preserves meaning.

### Prompt 4 — Generate Embedding + FAISS Index Code

Generate the complete code for services/embeddings.py.
This module must:

- Load SentenceTransformer ("all-MiniLM-L6-v2")
- Convert text chunks into embeddings
- Create or update a FAISS index
- Save and load the FAISS index from disk
- Provide a search() function returning top-k results

Make it optimized for large PDFs.

### Prompt 5 — Generate the Full RAG Pipeline

Generate services/rag_pipeline.py.
This file must:

- Accept user queries
- Convert the query into an embedding
- Search the FAISS index for relevant chunks
- Build a prompt template:
    "You are an AI Career Coach. The user has uploaded this resume. Use the retrieved resume context to answer. If the answer is not in the resume, answer generally."
- Call OpenAI GPT‑4o‑mini using the ChatCompletion API
- Return the model's final answer

## 🌐 Phase 3: Web Application

### Prompt 6 — Generate app.py (Flask Backend)

Generate a complete app.py file with:

ROUTES:
1. "/" - upload resume UI  
2. "/upload" POST - save file, process resume, generate vector index  
3. "/chat" - chatbot UI  
4. "/ask" POST - accept user question → run RAG pipeline → return response

Ensure:
- CORS enabled
- error handling
- vector index loads at startup
- resume saved under uploads/

### Prompt 7 — Generate HTML Templates

Generate templates/index.html and templates/chatbot.html.

index.html:
- Resume upload form
- Clean UI with instructions

chatbot.html:
- Chat window
- Input box
- AJAX POST to /ask
- Display conversation nicely

Keep UI minimal but professional.

### Prompt 8 — Generate CSS

Generate a modern responsive styles.css stored under static/styles.css.
Minimal glassmorphism design.

### Prompt 9 — Generate requirements.txt

Generate a complete requirements.txt with all required versions including:
flask
langchain
langchain-community
openai
pypdf2
sentence-transformers
faiss-cpu
python-dotenv

## 🔄 Phase 4: API Migration (OpenAI → Google Gemini)

### Prompt 10 — Switch to Google Gemini API

Update the entire application to use the Google Gemini API instead of OpenAI.
Replace all OpenAI ChatCompletion and Embedding API calls with the latest Gemini client.
Ensure that the RAG pipeline, chatbot routes, and prompt formatting all fully support Gemini.
Use the official Google Generative AI Python SDK.

### Prompt 11 — Model Selection

Update the application to use "gemini-2.5-flash" instead of the default Gemini Pro model.
Ensure all generate_text() calls use this model consistently.
Keep token settings optimized for long-form responses.

### Prompt 12 — Local Hosting Configuration

Modify the Flask server configuration so it runs only on localhost.
Remove any 0.0.0.0 bindings and ensure the app runs strictly on local machine access only.

## 🐛 Phase 5: Troubleshooting & Fixes

### Prompt 13 — Environment Setup

Generate a secure random SECRET_KEY and add it to the .env file.
Load this key inside the Flask application using python-dotenv.
Ensure the application gracefully fails if the key is missing.

### Prompt 14 — Dependency Issues

Fix all dependency installation issues.
Update the requirements.txt with stable versions for Flask, FAISS, SentenceTransformers, and Torch.
Add fallback installation notes and SSL bypass instructions if required.

### Prompt 15 — RAG Pipeline Initialization Error

Investigate why the RAG pipeline initialization is failing.
Check API integration, embedding loading, vector index initialization, and error-handling flow.
Provide robust error logs and fail-safe behavior.

### Prompt 16 — SSL Certificate Fix

Implement a robust SSL workaround so the application can proceed even when SSL verification fails.
Add fallback embedding generation using TF-IDF whenever SentenceTransformers download is blocked.
Ensure the application continues functioning in fully offline mode.

### Prompt 17 — Method Attribution Error

Fix the EmbeddingGenerator class so fallback embedding methods exist and are correctly referenced.
Ensure generate_embeddings() gracefully switches between transformer and fallback modes.

## 🎨 Phase 6: Response Enhancement

### Prompt 18 — Response Length Issues

Increase generation token limits from 500 to at least 2000 tokens.
Update the Gemini generation configuration to support long, fully detailed outputs.
Add streaming or chunking configuration if needed.

### Prompt 19 — Response Formatting

Implement markdown-to-HTML rendering in the chatbot interface.
Convert lists, headings, bold text, and code blocks into styled HTML.
Update CSS to support formatted blocks and readability.

## 📚 Phase 7: Documentation

### Prompt 20 — README Update

Update README.md to reflect:
- Gemini migration
- RAG improvements
- fallback embedding support
- updated installation steps
- complete architecture diagram
- running instructions and troubleshooting guide

### Prompt 21 — Prompts Documentation

Analyze all prompts used in the full development cycle.
Rewrite and structure them professionally in a single PROMPTS.md file.
Ensure clarity, sequencing, and executive-friendly explanation.

