import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from google import genai
from google.genai import types

class MockInterviewService:
    """Service for managing mock interview sessions with AI interviewer."""
    
    # Role-based question templates
    ROLE_QUESTIONS = {
        "Software Engineer": {
            "behavioral": [
                "Tell me about a challenging project you've worked on and how you overcame obstacles.",
                "Describe a situation where you had to debug a complex issue. What was your approach?",
                "How do you handle disagreements with team members about technical decisions?",
                "Tell me about a time you had to learn a new technology quickly.",
                "Describe your experience with code reviews. How do you give and receive feedback?"
            ],
            "technical": [
                "Explain the difference between SQL and NoSQL databases and when you'd use each.",
                "What design patterns are you familiar with? Can you give an example?",
                "How would you optimize a slow database query?",
                "Explain the concept of microservices and their advantages/disadvantages.",
                "What is your experience with version control systems like Git?"
            ],
            "scenario": [
                "How would you handle a production bug that's affecting users?",
                "Describe your approach to writing testable code.",
                "How do you balance technical debt with feature development?"
            ]
        },
        "DevOps Engineer": {
            "behavioral": [
                "Tell me about your most complex infrastructure project.",
                "Describe a time when you had to troubleshoot a critical production issue.",
                "How do you approach automation? What's your philosophy?",
                "Tell me about your experience with incident response.",
                "Describe a time you improved system reliability or performance."
            ],
            "technical": [
                "Explain your experience with containerization (Docker/Kubernetes).",
                "What CI/CD tools have you used? How do you design a pipeline?",
                "How do you approach infrastructure as code?",
                "Describe your monitoring and alerting strategy.",
                "What's your experience with cloud platforms (AWS/GCP/Azure)?"
            ],
            "scenario": [
                "How would you handle a failing deployment in production?",
                "Describe your approach to scaling an application.",
                "How do you ensure high availability and disaster recovery?"
            ]
        },
        "Cloud Engineer": {
            "behavioral": [
                "Tell me about your largest cloud migration project.",
                "Describe a time you optimized cloud costs.",
                "How do you approach cloud security?",
                "Tell me about your experience with multi-cloud environments.",
                "Describe a complex cloud architecture you've designed."
            ],
            "technical": [
                "Explain your experience with cloud services (compute, storage, networking).",
                "How do you approach cloud security and compliance?",
                "Describe your experience with Infrastructure as Code tools.",
                "What's your approach to cloud cost optimization?",
                "Explain your experience with serverless architectures."
            ],
            "scenario": [
                "How would you design a highly available application on the cloud?",
                "Describe your approach to disaster recovery in the cloud.",
                "How would you migrate a legacy application to the cloud?"
            ]
        },
        "Data Engineer": {
            "behavioral": [
                "Tell me about your most complex data pipeline.",
                "Describe a time you optimized data processing performance.",
                "How do you approach data quality and validation?",
                "Tell me about your experience with big data technologies.",
                "Describe a time you had to handle data at scale."
            ],
            "technical": [
                "Explain your experience with ETL/ELT processes.",
                "What data technologies have you worked with (Spark, Hadoop, etc.)?",
                "How do you approach data modeling and schema design?",
                "Describe your experience with data warehousing.",
                "What's your experience with real-time data processing?"
            ],
            "scenario": [
                "How would you design a data pipeline for real-time analytics?",
                "Describe your approach to handling data quality issues.",
                "How would you optimize a slow data transformation?"
            ]
        },
        "Backend Developer": {
            "behavioral": [
                "Tell me about your experience building scalable backend systems.",
                "Describe a time you had to refactor legacy code.",
                "How do you approach API design?",
                "Tell me about your experience with databases.",
                "Describe a time you optimized backend performance."
            ],
            "technical": [
                "Explain your experience with REST APIs and GraphQL.",
                "What's your approach to database design and optimization?",
                "Describe your experience with caching strategies.",
                "How do you handle authentication and authorization?",
                "Explain your experience with message queues and async processing."
            ],
            "scenario": [
                "How would you design a backend for a high-traffic application?",
                "Describe your approach to handling database migrations.",
                "How would you debug a performance issue in production?"
            ]
        }
    }
    
    def __init__(self):
        """Initialize the mock interview service."""
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.sessions = {}  # Store active interview sessions
    
    def create_session(self, session_id: str, resume_context: str = "", num_questions: int = 5) -> Dict:
        """Create a new mock interview session.
        
        Args:
            session_id: Unique session identifier
            resume_context: Resume context for role detection and personalization
            num_questions: Number of questions in the interview
            
        Returns:
            Session metadata
        """
        role = self._detect_role_from_resume(resume_context)
        
        session = {
            "session_id": session_id,
            "role": role,
            "num_questions": num_questions,
            "resume_context": resume_context,
            "current_question_index": 0,
            "questions": [],
            "answers": [],
            "feedback": [],
            "start_time": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.sessions[session_id] = session
        return session
    
    def get_next_question(self, session_id: str) -> Optional[Dict]:
        """Get the next interview question.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Question data or None if interview is complete
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if session["current_question_index"] >= session["num_questions"]:
            session["status"] = "completed"
            return None
        
        # Generate question if not already generated
        if session["current_question_index"] >= len(session["questions"]):
            question = self._generate_question(session)
            session["questions"].append(question)
        
        question = session["questions"][session["current_question_index"]]
        return {
            "question_index": session["current_question_index"] + 1,
            "total_questions": session["num_questions"],
            "question": question,
            "role": session["role"]
        }
    
    def _generate_question(self, session: Dict) -> str:
        """Generate an interview question based on role and context.
        
        Args:
            session: Interview session data
            
        Returns:
            Generated question
        """
        role = session["role"]
        question_index = len(session["questions"])
        
        # Select question type based on index
        if question_index < 2:
            question_type = "behavioral"
        elif question_index < 4:
            question_type = "technical"
        else:
            question_type = "scenario"
        
        # Get question pool for this role and type
        question_pool = self.ROLE_QUESTIONS[role].get(question_type, [])
        
        if not question_pool:
            return "Tell me about your experience with this role."
        
        # Select question (avoid duplicates)
        used_questions = set(session["questions"])
        available = [q for q in question_pool if q not in used_questions]
        
        if not available:
            available = question_pool
        
        question = available[0]
        
        # Personalize with resume context if available
        if session["resume_context"] and question_index == 0:
            question = self._personalize_question(question, session["resume_context"])
        
        return question
    
    def _detect_role_from_resume(self, resume_context: str) -> str:
        """Detect the most likely role from resume content.
        
        Args:
            resume_context: Resume text content
            
        Returns:
            Detected role name
        """
        if not resume_context:
            return "Software Engineer"
        
        resume_lower = resume_context.lower()
        role_keywords = {
            "DevOps Engineer": ["devops", "kubernetes", "docker", "ci/cd", "jenkins", "terraform", "ansible"],
            "Cloud Engineer": ["cloud", "aws", "azure", "gcp", "cloud architect"],
            "Data Engineer": ["data engineer", "etl", "spark", "hadoop", "data pipeline"],
            "Backend Developer": ["backend", "api", "rest", "graphql", "microservice"],
            "Software Engineer": ["software engineer", "developer", "programming"]
        }
        
        scores = {}
        for role, keywords in role_keywords.items():
            score = sum(1 for keyword in keywords if keyword in resume_lower)
            scores[role] = score
        
        return max(scores, key=scores.get)
    
    def _personalize_question(self, question: str, resume_context: str) -> str:
        """Personalize a question based on resume context.
        
        Args:
            question: Base question
            resume_context: Resume context
            
        Returns:
            Personalized question
        """
        if "project" in question.lower() and resume_context:
            return f"{question} (Feel free to reference your resume if relevant.)"
        return question
    
    def submit_answer(self, session_id: str, answer: str, 
                     transcript: Optional[str] = None) -> Dict:
        """Submit an answer to the current question.
        
        Args:
            session_id: Session identifier
            answer: User's answer (text or summary)
            transcript: Optional transcript from speech-to-text
            
        Returns:
            Feedback on the answer
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if session["current_question_index"] >= len(session["questions"]):
            raise ValueError("No active question")
        
        # Store answer
        answer_data = {
            "question_index": session["current_question_index"],
            "question": session["questions"][session["current_question_index"]],
            "answer": answer,
            "transcript": transcript or answer,
            "timestamp": datetime.now().isoformat()
        }
        session["answers"].append(answer_data)
        
        # Generate feedback
        feedback = self._generate_feedback(
            session["questions"][session["current_question_index"]],
            answer,
            session["role"],
            session["resume_context"]
        )
        session["feedback"].append(feedback)
        
        # Move to next question
        session["current_question_index"] += 1
        
        return {
            "feedback": feedback,
            "next_question_available": session["current_question_index"] < session["num_questions"]
        }
    
    def _generate_feedback(self, question: str, answer: str, role: str, 
                          resume_context: str) -> Dict:
        """Generate structured feedback on an answer.
        
        Args:
            question: Interview question
            answer: User's answer
            role: Target role
            resume_context: Resume context
            
        Returns:
            Structured feedback
        """
        try:
            prompt = f"""You are an expert technical interviewer evaluating a candidate's response.

ROLE: {role}
QUESTION: {question}
CANDIDATE'S ANSWER: {answer}

RESUME CONTEXT (if relevant): {resume_context[:500] if resume_context else "Not provided"}

Provide structured feedback in JSON format with the following fields:
{{
    "score": <0-10 numeric score>,
    "content_evaluation": {{
        "relevance": <0-10>,
        "technical_accuracy": <0-10>,
        "use_of_examples": <0-10>,
        "alignment_with_role": <0-10>,
        "summary": "<brief summary of content quality>"
    }},
    "communication_evaluation": {{
        "clarity": <0-10>,
        "confidence": <0-10>,
        "structure": <0-10>,
        "conciseness": <0-10>,
        "summary": "<brief summary of communication quality>"
    }},
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
    "suggested_improvement": "<example of how to improve the answer>"
}}

Provide ONLY valid JSON, no additional text."""
            
            resp = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1000,
                    temperature=0.7
                )
            )
            
            # Parse JSON response
            response_text = resp.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            feedback = json.loads(response_text)
            return feedback
            
        except Exception as e:
            # Return default feedback if generation fails
            return {
                "score": 5.0,
                "content_evaluation": {
                    "relevance": 5,
                    "technical_accuracy": 5,
                    "use_of_examples": 5,
                    "alignment_with_role": 5,
                    "summary": "Unable to evaluate at this time"
                },
                "communication_evaluation": {
                    "clarity": 5,
                    "confidence": 5,
                    "structure": 5,
                    "conciseness": 5,
                    "summary": "Unable to evaluate at this time"
                },
                "strengths": ["Provided a response"],
                "improvements": ["Try to be more specific"],
                "suggested_improvement": "Consider adding more concrete examples",
                "error": str(e)
            }
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get a summary of the completed interview session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session summary with scores and recommendations
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        if not session["feedback"]:
            return {"error": "No feedback available"}
        
        # Calculate overall metrics
        scores = [f.get("score", 5) for f in session["feedback"]]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Aggregate strengths and improvements
        all_strengths = []
        all_improvements = []
        
        for feedback in session["feedback"]:
            all_strengths.extend(feedback.get("strengths", []))
            all_improvements.extend(feedback.get("improvements", []))
        
        # Remove duplicates while preserving order
        unique_strengths = list(dict.fromkeys(all_strengths))[:5]
        unique_improvements = list(dict.fromkeys(all_improvements))[:5]
        
        # Determine readiness
        if overall_score >= 8:
            readiness = "Excellent - Ready for interviews"
        elif overall_score >= 7:
            readiness = "Good - Well prepared"
        elif overall_score >= 6:
            readiness = "Fair - Some preparation needed"
        else:
            readiness = "Needs improvement - More practice recommended"
        
        return {
            "session_id": session_id,
            "role": session["role"],
            "overall_score": round(overall_score, 1),
            "total_questions": session["num_questions"],
            "questions_answered": len(session["answers"]),
            "strengths": unique_strengths,
            "improvements": unique_improvements,
            "readiness": readiness,
            "individual_scores": [round(s, 1) for s in scores],
            "recommendations": self._generate_recommendations(overall_score, unique_improvements),
            "duration": self._calculate_duration(session["start_time"]),
            "end_time": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, score: float, improvements: List[str]) -> List[str]:
        """Generate learning recommendations based on performance.
        
        Args:
            score: Overall interview score
            improvements: Areas for improvement
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if score < 6:
            recommendations.append("Practice more mock interviews to build confidence")
            recommendations.append("Review fundamental concepts for your role")
        
        if score < 7:
            recommendations.append("Work on structuring your answers using the STAR method")
            recommendations.append("Practice explaining technical concepts clearly")
        
        if "examples" in str(improvements).lower():
            recommendations.append("Prepare specific examples from your experience")
        
        if "technical" in str(improvements).lower():
            recommendations.append("Review technical fundamentals and best practices")
        
        if "communication" in str(improvements).lower():
            recommendations.append("Practice speaking clearly and concisely")
        
        if not recommendations:
            recommendations.append("Continue practicing to maintain your skills")
            recommendations.append("Try interviews for different roles to broaden experience")
        
        return recommendations[:3]
    
    def _calculate_duration(self, start_time: str) -> str:
        """Calculate interview duration.
        
        Args:
            start_time: ISO format start time
            
        Returns:
            Duration string
        """
        try:
            start = datetime.fromisoformat(start_time)
            duration = datetime.now() - start
            minutes = int(duration.total_seconds() / 60)
            return f"{minutes} minutes"
        except:
            return "Unknown"
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_supported_roles(self) -> List[str]:
        """Get list of supported interview roles.
        
        Returns:
            List of role names
        """
        return list(self.ROLE_QUESTIONS.keys())
