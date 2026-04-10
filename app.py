from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()
from werkzeug.utils import secure_filename
from services.rag_pipeline import RAGPipeline
from services import mock_interview_routes
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS
CORS(app, origins=['*'])

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

# Global RAG pipeline instance
rag_pipeline = None

def init_rag_pipeline():
    """Initialize RAG pipeline and load existing index if available."""
    global rag_pipeline
    try:
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline()
        
        # Try to load existing index
        try:
            if rag_pipeline.load_existing_index():
                logger.info("Loaded existing vector index")
                stats = rag_pipeline.get_pipeline_stats()
                logger.info(f"Index stats: {stats}")
            else:
                logger.info("No existing vector index found")
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            
    except Exception as e:
        logger.error(f"Error initializing RAG pipeline: {e}")
        logger.error("Creating minimal RAG pipeline without pre-loading...")
        try:
            rag_pipeline = RAGPipeline()
        except Exception as e2:
            logger.error(f"Failed to create RAG pipeline: {e2}")
            rag_pipeline = None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Register Mock Interview Blueprint
app.register_blueprint(mock_interview_routes.mock_interview_bp)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon."""
    return '', 204

@app.route('/')
def index():
    """Render resume upload page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload and processing."""
    global rag_pipeline
    
    try:
        # Check if RAG pipeline is initialized
        if rag_pipeline is None:
            logger.error("RAG pipeline not initialized, attempting to reinitialize...")
            init_rag_pipeline()
            if rag_pipeline is None:
                return jsonify({'error': 'RAG pipeline initialization failed. Please check your API key and try again.'}), 500
        
        # Validate file upload
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path(app.config['UPLOAD_FOLDER'])
        upload_dir.mkdir(exist_ok=True)
        
        # Save file with secure filename
        filename = secure_filename(file.filename)
        
        # Add timestamp to avoid filename conflicts
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        filepath = upload_dir / filename
        file.save(str(filepath))
        
        logger.info(f"File saved: {filepath}")
        
        # Process resume with RAG pipeline
        try:
            resume_text = rag_pipeline.process_resume(str(filepath))
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            return jsonify({'error': f'Error processing resume: {str(e)}'}), 500
        
        # Get pipeline stats
        try:
            stats = rag_pipeline.get_pipeline_stats()
            logger.info(f"Resume processed successfully. Stats: {stats}")
        except Exception as e:
            logger.warning(f"Could not get pipeline stats: {e}")
            stats = {'index_stats': {'total_chunks': 0}}
        
        # Create preview (first 300 characters)
        preview = resume_text[:300] + '...' if len(resume_text) > 300 else resume_text
        
        return jsonify({
            'success': True,
            'message': 'Resume uploaded and processed successfully',
            'preview': preview,
            'filename': filename,
            'stats': {
                'resume_length': len(resume_text),
                'chunks_created': stats.get('index_stats', {}).get('total_chunks', 0)
            }
        })
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error processing resume: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/chat')
def chat():
    """Render chatbot page."""
    try:
        # Check if we have a processed resume
        if rag_pipeline is None:
            return render_template('chatbot.html', error="RAG pipeline not initialized")
        
        stats = rag_pipeline.get_pipeline_stats()
        if not stats['resume_loaded'] or stats['index_stats']['total_chunks'] == 0:
            return render_template('chatbot.html', warning="No resume has been uploaded yet. Please upload a resume first.")
        
        return render_template('chatbot.html', stats=stats)
    
    except Exception as e:
        logger.error(f"Error rendering chat page: {e}")
        return render_template('chatbot.html', error="Internal server error")

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle chat requests with RAG-enhanced responses."""
    global rag_pipeline
    
    try:
        # Check if RAG pipeline is initialized
        if rag_pipeline is None:
            return jsonify({'error': 'RAG pipeline not initialized'}), 500
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Check if we have a processed resume
        stats = rag_pipeline.get_pipeline_stats()
        if not stats['resume_loaded'] or stats['index_stats']['total_chunks'] == 0:
            return jsonify({
                'error': 'No resume has been processed yet. Please upload a resume first.'
            }), 400
        
        # Get optional parameters
        top_k = data.get('top_k', 3)
        max_tokens = data.get('max_tokens', 1000)
        
        # Validate parameters
        if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
            top_k = 3
        
        if not isinstance(max_tokens, int) or max_tokens < 50 or max_tokens > 2000:
            max_tokens = 1000
        
        logger.info(f"Processing question: {user_question[:100]}...")
        
        # Process query through RAG pipeline
        result = rag_pipeline.query(
            user_query=user_question,
            top_k=top_k,
            max_tokens=max_tokens
        )
        
        logger.info(f"Question processed successfully. Tokens used: {result.get('tokens_used', 'N/A')}")
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'metadata': {
                'retrieved_chunks': len(result['retrieved_chunks']),
                'similarity_scores': result['similarity_scores'],
                'tokens_used': result['tokens_used'],
                'context_used': result['context_used']
            },
            'debug': {
                'chunks_preview': [chunk[:100] + '...' for chunk in result['retrieved_chunks'][:2]]
            } if app.debug else {}
        })
    
    except ValueError as e:
        logger.error(f"Validation error in ask: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/status')
def status():
    """Get system status and statistics."""
    try:
        if rag_pipeline is None:
            return jsonify({
                'status': 'error',
                'message': 'RAG pipeline not initialized'
            }), 500
        
        stats = rag_pipeline.get_pipeline_stats()
        
        return jsonify({
            'status': 'healthy',
            'pipeline_stats': stats,
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'max_file_size': app.config['MAX_CONTENT_LENGTH']
        })
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/clear', methods=['POST'])
def clear_data():
    """Clear all pipeline data (for development/testing)."""
    global rag_pipeline
    
    try:
        if rag_pipeline is None:
            return jsonify({'error': 'RAG pipeline not initialized'}), 500
        
        rag_pipeline.clear_pipeline()
        logger.info("Pipeline data cleared")
        
        return jsonify({
            'success': True,
            'message': 'All pipeline data cleared successfully'
        })
    
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize RAG pipeline at startup
    logger.info("Starting AI Career Coach application...")
    init_rag_pipeline()
    
    # Mock Interview Service will be initialized on-demand when routes are accessed
    logger.info("Mock Interview Service will be initialized on-demand")
    
    # Check if required environment variables are set
    if not os.environ.get('GOOGLE_API_KEY'):
        logger.warning("GOOGLE_API_KEY not set. The application may not work properly.")
    
    # Run the application
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"Starting server in {'debug' if debug_mode else 'production'} mode")
    logger.info("Available endpoints:")
    logger.info("  - GET  /                    (Resume upload page)")
    logger.info("  - POST /upload              (Upload resume)")
    logger.info("  - GET  /chat                (Chat interface)")
    logger.info("  - POST /ask                 (Ask question)")
    logger.info("  - GET  /interview/page      (Mock interview page)")
    logger.info("  - POST /interview/start     (Start interview)")
    logger.info("  - GET  /interview/question/<id>  (Get question)")
    logger.info("  - POST /interview/answer/<id>    (Submit answer)")
    logger.info("  - GET  /interview/summary/<id>   (Get summary)")
    logger.info("  - GET  /interview/roles     (Get supported roles)")
    
    app.run(
        debug=debug_mode,
        host='127.0.0.1',
        port=int(os.environ.get('PORT', 5000))
    )
