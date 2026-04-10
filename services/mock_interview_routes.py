"""Mock Interview routes for Flask application."""

from flask import Blueprint, request, jsonify, render_template
import logging
import uuid
from services.mock_interview import MockInterviewService

logger = logging.getLogger(__name__)

# Create blueprint
mock_interview_bp = Blueprint('mock_interview', __name__, url_prefix='/interview')

# Dictionary to store active sessions
active_sessions = {}

def get_or_create_service():
    """Get or create mock interview service instance."""
    try:
        return MockInterviewService()
    except Exception as e:
        logger.error(f"Error creating MockInterviewService: {e}")
        raise

@mock_interview_bp.route('/start', methods=['POST'])
def start_interview():
    """Start a new mock interview session."""
    try:
        service = get_or_create_service()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        resume_context = data.get('resume_context', '').strip()
        num_questions = data.get('num_questions', 5)
        
        if not resume_context:
            return jsonify({'error': 'Resume context is required'}), 400
        
        if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 10:
            num_questions = 5
        
        session_id = str(uuid.uuid4())
        session = service.create_session(
            session_id=session_id,
            resume_context=resume_context,
            num_questions=num_questions
        )
        
        active_sessions[session_id] = service
        
        logger.info(f"Interview session created: {session_id} for role: {session['role']}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'role': session['role'],
            'num_questions': num_questions,
            'message': f'Interview started for {session["role"]}. You will be asked {num_questions} questions.'
        })
    
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        return jsonify({'error': f'Error starting interview: {str(e)}'}), 500

@mock_interview_bp.route('/question/<session_id>', methods=['GET'])
def get_question(session_id):
    """Get the next interview question."""
    try:
        if session_id not in active_sessions:
            service = get_or_create_service()
            active_sessions[session_id] = service
        else:
            service = active_sessions[session_id]
        
        question_data = service.get_next_question(session_id)
        
        if question_data is None:
            return jsonify({
                'success': True,
                'completed': True,
                'message': 'Interview completed. Please get summary.'
            })
        
        return jsonify({
            'success': True,
            'completed': False,
            'question_data': question_data
        })
    
    except ValueError as e:
        logger.error(f"Session not found: {e}")
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        logger.error(f"Error getting question: {e}")
        return jsonify({'error': f'Error getting question: {str(e)}'}), 500

@mock_interview_bp.route('/answer/<session_id>', methods=['POST'])
def submit_answer(session_id):
    """Submit an answer to the current question."""
    try:
        if session_id not in active_sessions:
            service = get_or_create_service()
            active_sessions[session_id] = service
        else:
            service = active_sessions[session_id]
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        answer = data.get('answer', '').strip()
        transcript = data.get('transcript', '').strip()
        
        if not answer:
            return jsonify({'error': 'Answer is required'}), 400
        
        result = service.submit_answer(
            session_id=session_id,
            answer=answer,
            transcript=transcript
        )
        
        logger.info(f"Answer submitted for session: {session_id}")
        
        return jsonify({
            'success': True,
            'feedback': result['feedback'],
            'next_question_available': result['next_question_available']
        })
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'error': f'Error submitting answer: {str(e)}'}), 500

@mock_interview_bp.route('/summary/<session_id>', methods=['GET'])
def get_summary(session_id):
    """Get interview session summary."""
    try:
        if session_id not in active_sessions:
            service = get_or_create_service()
            active_sessions[session_id] = service
        else:
            service = active_sessions[session_id]
        
        summary = service.get_session_summary(session_id)
        
        logger.info(f"Summary retrieved for session: {session_id}")
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except ValueError as e:
        logger.error(f"Session not found: {e}")
        return jsonify({'error': str(e)}), 404
    
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': f'Error getting summary: {str(e)}'}), 500

@mock_interview_bp.route('/roles', methods=['GET'])
def get_roles():
    """Get list of supported interview roles."""
    try:
        service = get_or_create_service()
        roles = service.get_supported_roles()
        
        logger.info(f"Roles retrieved: {roles}")
        
        return jsonify({
            'success': True,
            'roles': roles
        })
    
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Error getting roles: {str(e)}'}), 500

@mock_interview_bp.route('/delete/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete an interview session."""
    try:
        if session_id in active_sessions:
            service = active_sessions[session_id]
            success = service.delete_session(session_id)
            del active_sessions[session_id]
            
            if success:
                logger.info(f"Session deleted: {session_id}")
                return jsonify({
                    'success': True,
                    'message': 'Session deleted successfully'
                })
        
        return jsonify({'error': 'Session not found'}), 404
    
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'error': f'Error deleting session: {str(e)}'}), 500

@mock_interview_bp.route('/page')
def interview_page():
    """Render mock interview page."""
    try:
        return render_template('mock_interview.html')
    except Exception as e:
        logger.error(f"Error rendering interview page: {e}")
        return jsonify({'error': 'Internal server error'}), 500
