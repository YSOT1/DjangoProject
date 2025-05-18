import re
from typing import Dict, List, Tuple
import logging
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

logger = logging.getLogger(__name__)

class ChatbotService:
    """Service class for handling AI chatbot responses using a local model."""
    
    # Initialize the model and tokenizer
    try:
        # Using a small, efficient model that can run locally
        model_name = "microsoft/DialoGPT-small"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        chat_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)
        logger.info("Successfully loaded local chatbot model")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        model = None
        tokenizer = None
        chat_pipeline = None

    # System message to define the chatbot's role and capabilities
    SYSTEM_MESSAGE = """You are a medical assistant chatbot for a medical cabinet platform. Your role is to:
1. Help patients with platform-related questions (appointments, doctors, ratings)
2. Provide general health advice and information
3. Guide patients about insurance and payment processes
4. Identify potential medical emergencies and advise seeking immediate medical attention

Important guidelines:
- Always maintain a professional and empathetic tone
- For medical advice, provide general information only
- Never make definitive diagnoses
- Always recommend consulting a healthcare professional for specific medical concerns
- For emergencies, immediately advise calling emergency services (911)
- Keep responses concise and clear
- If unsure, ask for clarification"""

    # Platform-related keywords and responses
    PLATFORM_RESPONSES = {
        'appointment': "To book an appointment, go to the 'Find Doctors' section, select a doctor, and click 'Book Appointment'. You can also manage your appointments from your dashboard.",
        'doctor': "You can find and book appointments with doctors through the 'Find Doctors' section. Each doctor's profile includes their specialty, rating, and availability.",
        'rating': "You can rate doctors after your consultation. Go to your medical record, find the consultation, and click 'Rate Doctor'.",
        'medical record': "Your medical record contains your health history, consultations, and test results. You can access it from your dashboard.",
        'insurance': "You can manage your insurance policies and reimbursement requests in the 'Insurance' section of your dashboard.",
        'payment': "Payments can be made through the 'Payments' section. We accept various payment methods including credit cards and insurance.",
    }

    # Health-related keywords and responses
    HEALTH_RESPONSES = {
        'fever': "If you have a fever above 38°C (100.4°F), rest, stay hydrated, and consider taking fever reducers. If it persists for more than 3 days, please consult a doctor.",
        'headache': "For headaches, try resting in a quiet, dark room and stay hydrated. If severe or persistent, please consult a doctor.",
        'cough': "Stay hydrated and consider over-the-counter cough medicine. If you have difficulty breathing or the cough persists, please see a doctor.",
        'pain': "The severity and location of pain are important. If severe or persistent, please consult a doctor immediately.",
        'emergency': "For medical emergencies, please call emergency services (911) immediately or go to the nearest emergency room.",
        'cold': "For a common cold, rest, stay hydrated, and consider over-the-counter cold medicine. If symptoms worsen or persist, consult a doctor.",
        'flu': "If you suspect you have the flu, rest, stay hydrated, and consider antiviral medication if prescribed. Seek medical attention if symptoms are severe.",
        'allergy': "For allergies, try to identify and avoid triggers. Over-the-counter antihistamines may help. Consult a doctor for severe reactions.",
        'stress': "To manage stress, try regular exercise, meditation, and maintaining a healthy sleep schedule. Consider speaking with a mental health professional if needed.",
        'sleep': "For better sleep, maintain a regular schedule, create a comfortable environment, and avoid screens before bed. Consult a doctor if you have persistent sleep issues.",
        'diet': "A balanced diet should include fruits, vegetables, whole grains, lean proteins, and healthy fats. Consult a nutritionist for personalized advice.",
        'exercise': "Regular exercise is important for health. Aim for 150 minutes of moderate activity per week. Consult a doctor before starting a new exercise routine.",
    }

    # General responses
    GENERAL_RESPONSES = {
        'hello': "Hello! I'm your medical assistant. How can I help you today?",
        'hi': "Hi! I'm your medical assistant. How can I help you today?",
        'hey': "Hey! I'm your medical assistant. How can I help you today?",
        'greetings': "Greetings! I'm your medical assistant. How can I help you today?",
        'help': "I can help you with:\n1. Platform-related questions\n2. General health advice\n3. Insurance and payment information\nWhat would you like to know?",
        'thanks': "You're welcome! Is there anything else I can help you with?",
        'bye': "Take care! Feel free to return if you have more questions.",
    }

    @classmethod
    def get_response(cls, message: str) -> str:
        """Get an AI-generated response for the given message."""
        try:
            # First check for simple greetings and common interactions
            message_lower = message.lower().strip()
            
            # Check for greetings
            if any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'greetings']):
                return "Hello! I'm your medical assistant. How can I help you today?"
                
            # Check for thanks
            if any(thanks in message_lower for thanks in ['thanks', 'thank you', 'thank']):
                return "You're welcome! Is there anything else I can help you with?"
                
            # Check for goodbye
            if any(bye in message_lower for bye in ['bye', 'goodbye', 'see you']):
                return "Take care! Feel free to return if you have more questions."
                
            # Check for help request
            if 'help' in message_lower:
                return ("I can help you with:\n"
                       "1. Platform-related questions (appointments, doctors, ratings)\n"
                       "2. General health advice\n"
                       "3. Insurance and payment information\n"
                       "What would you like to know?")

            # Check for unclear or very short messages
            if len(message_lower) < 3 or message_lower in ['what', 'huh', '?']:
                return "I'm not sure I understand. Could you please rephrase your question or ask about one of these topics:\n1. Platform-related questions\n2. General health advice\n3. Insurance and payment information"

            # If not a simple interaction, try the AI model
            if cls.chat_pipeline is None:
                return cls._get_fallback_response(message)

            # Prepare the input text with more context
            input_text = f"{cls.SYSTEM_MESSAGE}\n\nUser: {message}\nAssistant:"
            
            # Generate response with adjusted parameters
            response = cls.chat_pipeline(
                input_text,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                truncation=True,
                pad_token_id=cls.tokenizer.eos_token_id
            )
            
            # Extract and clean the response
            generated_text = response[0]['generated_text']
            # Remove the input text from the response
            response_text = generated_text[len(input_text):].strip()
            
            # If the response is empty or too short, use fallback
            if not response_text or len(response_text) < 10:
                return cls._get_fallback_response(message)
                
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return cls._get_fallback_response(message)

    @classmethod
    def _get_fallback_response(cls, message: str) -> str:
        """Fallback response system when the AI model is unavailable."""
        message = message.lower().strip()
        
        # Basic responses for common queries
        responses = {
            'hello': "Hello! I'm your medical assistant. How can I help you today?",
            'hi': "Hi! I'm your medical assistant. How can I help you today?",
            'help': "I can help you with:\n1. Platform-related questions\n2. General health advice\n3. Insurance and payment information\nWhat would you like to know?",
            'appointment': "To book an appointment, go to the 'Find Doctors' section, select a doctor, and click 'Book Appointment'.",
            'doctor': "You can find and book appointments with doctors through the 'Find Doctors' section.",
            'emergency': "For medical emergencies, please call emergency services (911) immediately or go to the nearest emergency room.",
            'insurance': "You can manage your insurance policies and reimbursement requests in the 'Insurance' section of your dashboard.",
            'payment': "Payments can be made through the 'Payments' section. We accept various payment methods including credit cards and insurance.",
            'fever': "If you have a fever above 38°C (100.4°F), rest, stay hydrated, and consider taking fever reducers. If it persists for more than 3 days, please consult a doctor.",
            'headache': "For headaches, try resting in a quiet, dark room and stay hydrated. If severe or persistent, please consult a doctor.",
            'cough': "Stay hydrated and consider over-the-counter cough medicine. If you have difficulty breathing or the cough persists, please see a doctor.",
            'pain': "The severity and location of pain are important. If severe or persistent, please consult a doctor immediately.",
            'cold': "For a common cold, rest, stay hydrated, and consider over-the-counter cold medicine. If symptoms worsen or persist, consult a doctor.",
            'flu': "If you suspect you have the flu, rest, stay hydrated, and consider antiviral medication if prescribed. Seek medical attention if symptoms are severe.",
            'stress': "To manage stress, try regular exercise, meditation, and maintaining a healthy sleep schedule. Consider speaking with a mental health professional if needed.",
            'sleep': "For better sleep, maintain a regular schedule, create a comfortable environment, and avoid screens before bed. Consult a doctor if you have persistent sleep issues.",
            'diet': "A balanced diet should include fruits, vegetables, whole grains, lean proteins, and healthy fats. Consult a nutritionist for personalized advice.",
            'exercise': "Regular exercise is important for health. Aim for 150 minutes of moderate activity per week. Consult a doctor before starting a new exercise routine."
        }
        
        # Check for matching keywords
        for keyword, response in responses.items():
            if keyword in message:
                return response
        
        # Default response
        return ("I can help you with:\n"
                "1. Platform-related questions (appointments, doctors, ratings)\n"
                "2. General health advice\n"
                "3. Insurance and payment information\n"
                "Please try rephrasing your question or ask about one of these topics.")

    @classmethod
    def is_emergency(cls, message: str) -> bool:
        """Check if the message indicates a medical emergency."""
        # Emergency keywords that indicate immediate medical attention is needed
        emergency_keywords = [
            'emergency', 'urgent', 'severe pain', 'chest pain',
            'difficulty breathing', 'unconscious', 'seizure',
            'heart attack', 'stroke', 'severe bleeding',
            'broken bone', 'head injury', 'severe burn',
            'choking', 'not breathing', 'severe allergic reaction',
            'severe trauma', 'severe injury', 'severe wound'
        ]
        
        message = message.lower()
        return any(keyword in message for keyword in emergency_keywords) 