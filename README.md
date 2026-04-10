# 🎯 AI Career Coach

A production-ready Flask application that analyzes resumes and provides personalized career guidance using **Google Gemini models** and a **RAG (Retrieval-Augmented Generation) pipeline**. Upload your resume, get instant AI-powered career insights, and have interactive conversations with your personal career coach.

---

## ✨ Features

- **📄 Resume Upload** – Drag-and-drop PDF upload with instant processing
- **🧠 Gemini Embeddings** – 3072-dimensional semantic embeddings via `gemini-embedding-001`
- **⚡ FAISS Vector Index** – Lightning-fast similarity search on local index
- **💬 Gemini 2.5 Flash** – High-quality conversational responses with context awareness
- **🎨 Modern UI** – Glassmorphism design with responsive layout
- **📋 Resume Preview** – Structured resume analysis with key information extraction
- **💭 Smart Chat** – Autosizing input, typing indicators, markdown rendering, copy buttons
- **🔒 Client-Side Security** – HTML escaping, DOMPurify sanitization, safe URL handling
- **⚙️ Local Processing** – All data processed locally; FAISS index stored per session
- **🚀 Production Ready** – Error handling, logging, graceful degradation

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** – Core runtime
- **Flask 3.0.0** – Web framework with CORS support
- **google-genai ≥1.66.0** – Latest Google Gen AI SDK (replaces deprecated `google-generativeai`)
- **FAISS 1.8.0** – Vector similarity search
- **numpy 1.26.4** – Numerical computing
- **PyPDF2 3.0.1** – PDF text extraction
- **langchain / langchain-community** – Optional text processing helpers

### Frontend
- **HTML5 + CSS3** – Semantic markup with modern styling
- **Vanilla JavaScript** – No framework dependencies
- **marked.js** – Markdown-to-HTML rendering
- **DOMPurify** – XSS protection and HTML sanitization

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Career Coach Pipeline                     │
└─────────────────────────────────────────────────────────────────┘

1. RESUME UPLOAD
   ├─ User uploads PDF via drag-and-drop
   ├─ Backend extracts text using PyPDF2
   └─ Text cleaned and validated

2. TEXT PROCESSING
   ├─ Resume text chunked (200-300 tokens per chunk)
   ├─ Semantic preservation with overlap
   └─ Chunks stored for retrieval

3. EMBEDDING GENERATION
   ├─ Each chunk embedded using Gemini Embedding Model
   ├─ 3072-dimensional vectors generated
   └─ Embeddings stored in FAISS index

4. VECTOR INDEX
   ├─ FAISS IndexFlatIP created for cosine similarity
   ├─ All embeddings added to index
   └─ Index persisted to disk (vector_index/)

5. USER QUERY
   ├─ User asks a question in chat
   ├─ Query embedded using same Gemini model
   └─ FAISS retrieves top-k similar chunks

6. CONTEXT RETRIEVAL
   ├─ Retrieved chunks ranked by similarity
   ├─ Top chunks combined into context
   └─ Context + query sent to Gemini 2.5 Flash

7. RESPONSE GENERATION
   ├─ Gemini 2.5 Flash processes context + query
   ├─ Generates structured, conversational response
   ├─ Response streamed to frontend
   └─ Markdown rendered and displayed in chat

8. CHAT INTERFACE
   ├─ Messages displayed with avatars
   ├─ Markdown formatting applied
   ├─ Copy buttons for easy sharing
   └─ Typing indicators during generation
```

---

## 📦 Installation & Setup

### Prerequisites
- **Python 3.11+** (required for all dependencies)
- **Google Gemini API key** ([Get it here](https://makersuite.google.com/app/apikey))
- **16MB+ available storage** for uploads
- **Internet connection** for Gemini API calls

### Step-by-Step Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd career-coach
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
```bash
# Copy template
cp .env.example .env  # macOS/Linux
copy .env.example .env  # Windows
```

Edit `.env` file:
```env
# Required: Get your API key from https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_actual_gemini_api_key_here

# Optional: Flask environment
FLASK_ENV=development
```

#### 5. Start Application
```bash
python app.py
```

#### 6. Access Application
Open your browser to **http://127.0.0.1:5000**

---

## 🎯 Usage Guide

### Basic Workflow

1. **Upload Resume**
   - Navigate to home page
   - Drag-and-drop a PDF resume or click to browse
   - Wait for processing (typically 2-5 seconds)

2. **View Preview**
   - Resume analysis displays with key statistics
   - See character count and number of chunks created
   - Verify extraction was successful

3. **Start Chat**
   - Click "Start AI Career Coaching" button
   - Chat interface opens with empty state
   - Suggested prompts appear for quick start

4. **Ask Questions**
   - Type your question in the input box
   - Press Enter or click send button
   - Wait for AI response (typically 3-10 seconds)
   - Response appears with markdown formatting

### Example Questions

- "What are my strongest skills based on my resume?"
- "What job roles are suitable for me?"
- "Convert my experience into strong resume bullet points"
- "What skills am I missing to become a senior developer?"
- "Give me interview questions for a DevOps role"
- "Which companies hire people with my skillset?"
- "What should I learn next in cloud computing?"
- "Rewrite my resume summary to make it more impactful"

---

## 🔌 API Endpoints

### Upload & Preview
- `GET /` – Resume upload page with drag-and-drop
- `POST /upload` – Process resume and generate preview
- `GET /status` – System health check

### Chat Interface
- `GET /chat` – Chat interface page
- `POST /ask` – Process user query through RAG pipeline
- `POST /clear` – Clear pipeline data (development only)

### Response Format
```json
{
  "success": true,
  "message": "Resume processed successfully",
  "preview": "Extracted resume text...",
  "stats": {
    "resume_length": 5432,
    "chunks_created": 18
  }
}
```

---

## 🔧 Configuration

### Environment Variables
```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional
FLASK_ENV=development|production
PORT=5000
MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
```

### Customization Options

**Text Chunking** – Edit `services/chunker.py`
```python
chunk_size = 250  # words per chunk
overlap = 50      # word overlap between chunks
```

**Embedding Model** – Edit `services/embeddings.py`
```python
self.model_name = "gemini-embedding-001"  # 3072 dimensions
```

**Response Length** – Edit `services/rag_pipeline.py`
```python
max_output_tokens=3000  # Gemini response limit
temperature=0.6        # Creativity level (0.0-1.0)
```

**UI Theme** – Edit `static/styles.css`
```css
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--text-primary: #1a1a1a;
```

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. "GOOGLE_API_KEY is not set"
**Problem:** Application fails to start
```
RuntimeError: GOOGLE_API_KEY is not set. Please add it to .env or system environment variables.
```
**Solution:**
- Verify `.env` file exists in project root
- Check API key is correctly set: `GOOGLE_API_KEY=sk_...`
- Restart application after updating `.env`

#### 2. "Error generating embeddings with Gemini"
**Problem:** Resume upload fails during embedding
```
RuntimeError: Error generating embeddings with Gemini: ...
```
**Solution:**
- Verify internet connection is active
- Check API key is valid and has quota remaining
- Ensure PDF is not corrupted
- Try with a smaller PDF file

#### 3. "No text could be extracted from the PDF"
**Problem:** PDF upload succeeds but no text extracted
**Solution:**
- Verify PDF is text-based (not scanned image)
- Try converting PDF to text first
- Check file is not password-protected
- Ensure PDF is under 16MB

#### 4. "FAISS index not found"
**Problem:** Chat page shows error after upload
**Solution:**
- Refresh the page
- Re-upload the resume
- Check `vector_index/` directory exists
- Clear browser cache

#### 5. Response Truncation
**Problem:** AI responses cut off mid-sentence
**Solution:**
- Already fixed in current version (max_output_tokens=3000)
- Ask more specific questions for focused answers
- Check Gemini API quota

### Debug Mode

Enable detailed logging:
```bash
# Set debug mode in .env
FLASK_ENV=development

# Run with verbose output
python app.py
```

Check logs for:
- PDF extraction status
- Embedding generation progress
- FAISS index operations
- Gemini API responses

---

## 📊 Performance & Scalability

| Metric | Value |
|--------|-------|
| **Max File Size** | 16MB |
| **Typical Upload Time** | 2-5 seconds |
| **Typical Query Time** | 3-10 seconds |
| **Memory Usage** | 200-500MB |
| **Embedding Dimension** | 3072 |
| **FAISS Index Type** | IndexFlatIP (cosine similarity) |
| **Concurrent Users** | Multiple (session-isolated) |

---

## 🔒 Security Features

- **File Validation** – PDF-only uploads with size limits
- **Secure Filenames** – Automatic sanitization of uploaded filenames
- **CORS Protection** – Configurable cross-origin policies
- **Input Sanitization** – HTML escaping and XSS prevention
- **URL Validation** – Safe URL handling (mailto, tel, https only)
- **Error Handling** – No sensitive information in error messages
- **Session Security** – Secure session management
- **Local Processing** – All data processed locally (privacy-first)

---

## 🚀 Production Deployment

### Production Checklist
- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Use production WSGI server (gunicorn, uWSGI)
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up SSL/TLS certificates
- [ ] Implement rate limiting
- [ ] Configure proper logging
- [ ] Set up monitoring and health checks
- [ ] Secure file upload directory
- [ ] Configure firewall rules
- [ ] Set up backup for vector indices

### Example Production Setup

#### Using Gunicorn
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# With SSL
gunicorn -w 4 -b 0.0.0.0:8443 \
  --certfile=cert.pem \
  --keyfile=key.pem \
  app:app
```

#### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

---

## 📁 Project Structure

```
career-coach/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git exclusions
├── README.md                       # This file
│
├── services/
│   ├── __init__.py                # Package initialization
│   ├── resume_parser.py           # PDF extraction & parsing
│   ├── chunker.py                 # Text chunking logic
│   ├── embeddings.py              # Gemini embeddings + FAISS
│   └── rag_pipeline.py            # RAG orchestration
│
├── templates/
│   ├── index.html                 # Resume upload page
│   └── chatbot.html               # Chat interface
│
├── static/
│   ├── styles.css                 # Main stylesheet
│   ├── js/
│   │   └── chat.js                # Chat functionality
│   └── images/                    # Assets
│
├── uploads/                       # Uploaded resumes (temp)
│   └── .gitkeep
│
└── vector_index/                  # FAISS indices (per session)
    └── .gitkeep
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📝 License

MIT License – see LICENSE file for details

---

## 🆘 Support & Resources

### Getting Help
1. **Check Troubleshooting Guide** – See section above
2. **Review Application Logs** – Enable debug mode for detailed output
3. **Check API Status** – Verify Gemini API is operational
4. **Open an Issue** – Include:
   - Error messages (full stack trace)
   - System information (OS, Python version)
   - Steps to reproduce
   - Expected vs actual behavior

### Useful Links
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyPDF2 Documentation](https://pypdf2.readthedocs.io/)

---

## 🎓 Learning Resources

### Understanding RAG
- [What is RAG?](https://aws.amazon.com/what-is/retrieval-augmented-generation/)
- [RAG Best Practices](https://docs.llamaindex.ai/en/stable/use_cases/rag/)

### Gemini Models
- [Gemini 2.5 Flash](https://ai.google.dev/models/gemini-2-5-flash)
- [Embedding Models](https://ai.google.dev/models/gemini-embedding-001)

### Vector Databases
- [FAISS Tutorial](https://github.com/facebookresearch/faiss/wiki)
- [Vector Search Basics](https://www.pinecone.io/learn/vector-database/)

---

## 📊 Metrics & Analytics

### Typical Performance
- **Resume Processing:** 2-5 seconds
- **Query Response:** 3-10 seconds
- **Embedding Generation:** <1 second per chunk
- **FAISS Search:** <100ms for top-5 results

### Resource Usage
- **Memory:** 200-500MB (depends on resume size)
- **Disk:** ~50MB for FAISS index (typical)
- **Network:** ~1-2MB per query (API calls)

---

## 🔄 Version History

### v1.0.0 (Current)
- ✅ Google Gen AI SDK integration (`google-genai ≥1.66.0`)
- ✅ Gemini 2.5 Flash for responses
- ✅ Gemini Embedding Model (3072-dim)
- ✅ FAISS vector index
- ✅ Modern UI with chat interface
- ✅ Production-ready error handling

---

## 🙏 Acknowledgments

Built with:
- **Google Gemini** – AI models and embeddings
- **FAISS** – Vector similarity search
- **Flask** – Web framework
- **PyPDF2** – PDF processing

---

**Built with ❤️ for career development and professional growth**

*Powered by Google Gemini 2.5 Flash • Advanced RAG Pipeline • Modern Web UI*
