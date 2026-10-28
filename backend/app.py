"""
AI Book Assistant - Flask backend
PDF Q&A, summarization, TTS; Firebase Auth + Firestore per-user storage.
"""

import logging
import os
import sys
import uuid

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(BACKEND_DIR, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Load API key from environment variable
from dotenv import load_dotenv
load_dotenv()

if not os.getenv('OPENROUTER_API_KEY'):
    raise ValueError("OPENROUTER_API_KEY environment variable is not set. Please check your .env file.")

# OpenRouter Model Configuration
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.2-3b-instruct:free')
# Available free models: meta-llama/llama-3.2-3b-instruct:free, meta-llama/llama-3.2-1b-instruct:free
# Paid models: anthropic/claude-3-haiku, openai/gpt-3.5-turbo, openai/gpt-4o-mini
# See all models at: https://openrouter.ai/models

# Fallback mode when OpenRouter is unavailable
OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'

from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
from openai import OpenAI
import PyPDF2
from gtts import gTTS

from auth_firebase import require_firebase_user
from firebase_service import (
    is_firebase_configured,
    save_user_book,
    load_user_book,
    clear_user_book,
    get_user_document_history,
    load_historical_document,
    delete_historical_document,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_book_assistant.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, 'templates')
STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
AUDIO_FOLDER = os.path.join(STATIC_DIR, 'audio')

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static',
)
CORS(
    app,
    resources={
        r'/*': {
            'origins': '*',
            'allow_headers': ['Authorization', 'Content-Type'],
            'methods': ['GET', 'POST', 'OPTIONS'],
        }
    },
)

MAX_TTS_CHARS = 4500

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


@app.context_processor
def inject_firebase_web_config():
    return {
        'firebase_config': {
            'apiKey': os.getenv('FIREBASE_WEB_API_KEY', ''),
            'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN', ''),
            'projectId': os.getenv('FIREBASE_PROJECT_ID', ''),
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', ''),
            'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID', ''),
            'appId': os.getenv('FIREBASE_APP_ID', ''),
        }
    }


def _openrouter_api_key():
    key = (os.getenv('OPENROUTER_API_KEY') or '').strip()
    if not key or key == 'your_openrouter_api_key_here':
        return None
    return key


_cached_openrouter_client = None


def require_openrouter_client():
    global _cached_openrouter_client
    key = _openrouter_api_key()
    if not key:
        raise ValueError(
            'OpenRouter API key not set. Add OPENROUTER_API_KEY to your .env file and restart the server.'
        )
    if _cached_openrouter_client is None:
        _cached_openrouter_client = OpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1"
        )
    return _cached_openrouter_client


def clean_markdown(text):
    """Remove markdown formatting and return plain text."""
    import re
    # Remove bold/italic markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def extract_text_from_pdf(pdf_path):
    """Extract text with multiple methods: PyMuPDF, PyPDF2, pdfplumber. OCR is optional."""
    text = ""
    method_used = "none"
    
    # Method 1: Try PyMuPDF (fitz) first - most reliable
    try:
        import fitz
        doc = fitz.open(pdf_path)
        parts = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                parts.append(page_text)
        doc.close()
        text = '\n'.join(parts)
        method_used = "PyMuPDF"
        logger.info('PyMuPDF extraction successful: %s characters', len(text.strip()))
    except ImportError:
        logger.info('PyMuPDF not available, trying PyPDF2...')
    except Exception as e:
        logger.warning('PyMuPDF failed: %s', e)
    
    # Method 2: Try PyPDF2 if PyMuPDF failed or extracted little text
    if len(text.strip()) < 50:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                parts = []
                for page in reader.pages:
                    page_text = page.extract_text() or ''
                    if page_text.strip():
                        parts.append(page_text)
            pypdf2_text = '\n'.join(parts)
            if len(pypdf2_text.strip()) > len(text.strip()):
                text = pypdf2_text
                method_used = "PyPDF2"
                logger.info('PyPDF2 extraction successful: %s characters', len(text.strip()))
        except Exception as e:
            logger.warning('PyPDF2 failed: %s', e)

    # Method 3: Try pdfplumber if still little text
    if len(text.strip()) < 50:
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                parts = []
                for page in pdf.pages:
                    page_text = page.extract_text() or ''
                    if page_text.strip():
                        parts.append(page_text)
            pdfplumber_text = '\n'.join(parts)
            if len(pdfplumber_text.strip()) > len(text.strip()):
                text = pdfplumber_text
                method_used = "pdfplumber"
                logger.info('pdfplumber extraction successful: %s characters', len(text.strip()))
        except ImportError:
            logger.info('pdfplumber not available')
        except Exception as e:
            logger.warning('pdfplumber failed: %s', e)

    # Method 4: Try OCR if still little text (optional - only if Tesseract is available)
    if len(text.strip()) < 50:
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            
            logger.info('Attempting OCR extraction for scanned PDF')
            
            # Check if Tesseract is available
            try:
                pytesseract.get_tesseract_version()
                logger.info('Tesseract OCR is available, attempting OCR...')
                
                # Convert PDF to images with better settings
                images = convert_from_path(
                    pdf_path, 
                    dpi=300,  # Higher DPI for better OCR
                    first_page=1, 
                    last_page=10,  # Process more pages for better results
                    grayscale=True,
                    use_pdftocairo=True
                )
                
                ocr_parts = []
                for i, image in enumerate(images):
                    try:
                        # Preprocess image for better OCR
                        image = image.convert('L')  # Convert to grayscale
                        # Enhance contrast
                        from PIL import ImageEnhance
                        enhancer = ImageEnhance.Contrast(image)
                        image = enhancer.enhance(2.0)
                        
                        ocr_text = pytesseract.image_to_string(
                            image, 
                            config='--psm 6 --oem 3'  # Better page segmentation and OCR engine mode
                        )
                        
                        if ocr_text and len(ocr_text.strip()) > 10:
                            ocr_parts.append(f"--- Page {i+1} ---\n{ocr_text.strip()}")
                            logger.info('OCR successful for page %d: %s characters', i+1, len(ocr_text.strip()))
                    except Exception as e:
                        logger.warning('OCR failed for page %d: %s', i+1, e)
                        continue
                
                if ocr_parts:
                    ocr_text = '\n\n'.join(ocr_parts)
                    if len(ocr_text.strip()) > len(text.strip()):
                        text = ocr_text
                        method_used = "OCR"
                        logger.info('OCR extraction successful: %s characters from %d pages', len(text.strip()), len(images))
                
            except Exception as te:
                logger.info('Tesseract OCR not available - skipping OCR step: %s', te)
                # Continue without OCR - don't raise an exception
            
        except ImportError as ie:
            logger.info('OCR dependencies not available: %s', ie)
        except Exception as e:
            logger.warning('OCR extraction failed: %s', e)

    # Final validation - more lenient requirements
    if not text or len(text.strip()) < 3:
        error_msg = (
            f'Could not extract text from PDF. Tried methods: {method_used}. '
            'This appears to be a scanned PDF, image-only PDF, or corrupted file. '
            'Solutions: 1) Upload a PDF with selectable text, 2) Install Tesseract OCR for scanned PDF support, '
            '3) Try a different PDF file.'
        )
        logger.error(error_msg)
        raise Exception(error_msg)

    logger.info('Text extraction completed using %s: %s characters', method_used, len(text.strip()))
    return text.strip()


def generate_summary(text):
    try:
        if not text or len(text.strip()) < 10:
            return 'No text available to summarize.'

        # Check if offline mode is enabled
        if OFFLINE_MODE:
            return f"[Offline Mode] Summary unavailable - OpenRouter API unavailable. Text length: {len(text)} characters. Please check your OpenRouter API key."

        text_to_summarize = text[:15000] if len(text) > 15000 else text

        oc = require_openrouter_client()
        response = oc.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an AI assistant that summarizes books and documents. Provide clear, concise summaries that capture the main points and key ideas. IMPORTANT: Respond in plain text without any markdown formatting, asterisks, or special characters. Use normal sentences and paragraphs.',
                },
                {
                    'role': 'user',
                    'content': f'Please provide a comprehensive summary of the following text:\n\n{text_to_summarize}',
                },
            ],
            max_tokens=500,
            temperature=0.7,
        )

        return clean_markdown(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e).lower()
        if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str or 'openrouter' in error_str:
            return f"[Offline Mode] Summary unavailable - OpenRouter API issue. Text length: {len(text)} characters. Please check your OpenRouter API key and billing."
        logger.error('Error generating summary: %s', e)
        raise Exception(f'Failed to generate summary: {str(e)}') from e


def ask_question(question, context):
    try:
        if not question or len(question.strip()) < 1:
            raise Exception('Question cannot be empty')

        if not context or len(context.strip()) < 10:
            raise Exception('No PDF content available. Please upload a PDF first.')

        # Check if offline mode is enabled
        if OFFLINE_MODE:
            return f"[Offline Mode] Question answering unavailable - OpenRouter API unavailable. Your question: '{question}'. Please check your OpenRouter API key."

        context_to_use = context[:15000] if len(context) > 15000 else context

        oc = require_openrouter_client()
        response = oc.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an AI assistant that answers questions based ONLY on the provided text from a PDF book. If the answer cannot be found in the text, state that clearly. Always cite relevant parts of the text when possible. IMPORTANT: Respond in plain text without any markdown formatting, asterisks, or special characters. Use normal sentences and paragraphs.',
                },
                {
                    'role': 'user',
                    'content': f'Based ONLY on the following text from the PDF, answer the question:\n\nText:\n{context_to_use}\n\nQuestion: {question}\n\nAnswer:',
                },
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        return clean_markdown(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e).lower()
        if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str or 'openrouter' in error_str:
            return f"[Offline Mode] Question answering unavailable - OpenRouter API issue. Your question: '{question}'. Please check your OpenRouter API key and billing."
        logger.error('Error answering question: %s', e)
        raise Exception(f'Failed to answer question: {str(e)}') from e


def translate_text(text, target_language='English'):
    try:
        if not text or len(text.strip()) < 10:
            return 'No text available to translate.'

        text_to_translate = text[:8000] if len(text) > 8000 else text

        oc = require_openrouter_client()
        response = oc.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': f'You are a professional translator. Translate the following text to {target_language}. Maintain the original meaning, tone, and context. Only provide the translated text without explanations. IMPORTANT: Respond in plain text without any markdown formatting, asterisks, or special characters. Use normal sentences and paragraphs.',
                },
                {
                    'role': 'user',
                    'content': f'Translate this text to {target_language}:\n\n{text_to_translate}',
                },
            ],
            max_tokens=2000,
            temperature=0.3,
        )

        return clean_markdown(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e).lower()
        if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str:
            raise Exception('OpenAI API quota exceeded. Please add billing to your OpenAI account at https://platform.openai.com/account/billing or try again later.') from e
        logger.error('Error translating text: %s', e)
        raise Exception(f'Failed to translate text: {str(e)}') from e


def extract_key_insights(text):
    try:
        if not text or len(text.strip()) < 10:
            return 'No text available for analysis.'

        text_to_analyze = text[:12000] if len(text) > 12000 else text

        oc = require_openrouter_client()
        response = oc.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an AI analyst that extracts key insights, main themes, and important points from books and documents. Provide a structured analysis with bullet points covering: 1) Main Themes, 2) Key Insights, 3) Important Concepts, 4) Notable Quotes or Takeaways. IMPORTANT: Respond in plain text without any markdown formatting, asterisks, or special characters. Use normal sentences and paragraphs.',
                },
                {
                    'role': 'user',
                    'content': f'Extract key insights and provide a comprehensive analysis of the following text:\n\n{text_to_analyze}',
                },
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        return clean_markdown(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e).lower()
        if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str:
            raise Exception('OpenAI API quota exceeded. Please add billing to your OpenAI account at https://platform.openai.com/account/billing or try again later.') from e
        logger.error('Error extracting insights: %s', e)
        raise Exception(f'Failed to extract insights: {str(e)}') from e


def analyze_sentiment(text):
    try:
        if not text or len(text.strip()) < 10:
            return 'No text available for sentiment analysis.'

        text_to_analyze = text[:8000] if len(text) > 8000 else text

        oc = require_openrouter_client()
        response = oc.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are an AI sentiment analyst. Analyze the sentiment and tone of the provided text. Provide insights on: 1) Overall sentiment (positive, negative, neutral), 2) Emotional tone, 3) Writing style, 4) Target audience perspective. IMPORTANT: Respond in plain text without any markdown formatting, asterisks, or special characters. Use normal sentences and paragraphs.',
                },
                {
                    'role': 'user',
                    'content': f'Analyze the sentiment and tone of this text:\n\n{text_to_analyze}',
                },
            ],
            max_tokens=800,
            temperature=0.5,
        )

        return clean_markdown(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e).lower()
        if 'quota' in error_str or '429' in error_str or 'insufficient_quota' in error_str:
            raise Exception('OpenAI API quota exceeded. Please add billing to your OpenAI account at https://platform.openai.com/account/billing or try again later.') from e
        logger.error('Error analyzing sentiment: %s', e)
        raise Exception(f'Failed to analyze sentiment: {str(e)}') from e


def text_to_speech(text):
    try:
        if not text or len(text.strip()) < 1:
            raise Exception('No text available for text-to-speech')

        speak_text = text.strip()
        if len(speak_text) > MAX_TTS_CHARS:
            speak_text = speak_text[:MAX_TTS_CHARS].rsplit(' ', 1)[0] + '...'

        filename = f'speech_{uuid.uuid4().hex}.mp3'
        filepath = os.path.join(AUDIO_FOLDER, filename)

        tts = gTTS(text=speak_text, lang='en', slow=False)
        tts.save(filepath)

        return filename
    except Exception as e:
        logger.error('Error converting text to speech: %s', e)
        raise Exception(f'Failed to convert text to speech: {str(e)}') from e


def _remove_upload_if_exists(stored_filename):
    if not stored_filename:
        return
    path = os.path.join(UPLOAD_FOLDER, stored_filename)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as e:
            logger.warning('Could not remove old upload %s: %s', path, e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/health')
def health():
    return jsonify(
        {
            'status': 'healthy',
            'service': 'AI Book Assistant',
            'firebase_configured': is_firebase_configured(),
        }
    )


@app.route('/api/session', methods=['GET', 'OPTIONS'])
@require_firebase_user
def api_session():
    book = load_user_book(g.firebase_uid)
    t = book.get('extracted_text') or ''
    has = len(t.strip()) >= 10
    return jsonify(
        {
            'success': True,
            'has_pdf': has,
            'pdf_name': book.get('pdf_name') or '',
            'text_length': len(t),
            'truncated': bool(book.get('truncated')),
        }
    )


@app.route('/upload', methods=['POST', 'OPTIONS'])
@require_firebase_user
def upload_pdf():
    try:
        logger.info('Upload request received from user: %s', g.firebase_uid)
        
        if 'file' not in request.files:
            logger.warning('No file in request')
            return jsonify({'success': False, 'error': 'No file uploaded. Please select a PDF file.'}), 400

        file = request.files['file']

        if file.filename == '':
            logger.warning('Empty filename provided')
            return jsonify({'success': False, 'error': 'No file selected. Please choose a PDF file.'}), 400

        if not file.filename.lower().endswith('.pdf'):
            logger.warning('Invalid file type: %s', file.filename)
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload a PDF file.'}), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 16 * 1024 * 1024:
            logger.warning('File too large: %d bytes', file_size)
            return jsonify({'success': False, 'error': 'File too large. Maximum upload size is 16MB.'}), 413

        if file_size < 1024:  # Less than 1KB
            logger.warning('File too small: %d bytes', file_size)
            return jsonify({'success': False, 'error': 'File appears to be empty or corrupted. Please select a valid PDF file.'}), 400

        # Clean up previous upload
        prev = load_user_book(g.firebase_uid)
        _remove_upload_if_exists(prev.get('stored_filename'))

        # Save file
        stored_filename = f'{g.firebase_uid}_{uuid.uuid4().hex}_{file.filename}'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        
        try:
            file.save(filepath)
            logger.info('File saved successfully: %s (%d bytes)', filepath, os.path.getsize(filepath))
        except Exception as save_error:
            logger.error('Failed to save file: %s', save_error)
            return jsonify({'success': False, 'error': 'Failed to save file. Please try again.'}), 500

        # Validate PDF file
        try:
            import PyPDF2
            with open(filepath, 'rb') as test_file:
                test_reader = PyPDF2.PdfReader(test_file)
                if len(test_reader.pages) == 0:
                    os.remove(filepath)
                    return jsonify({'success': False, 'error': 'PDF appears to be empty or corrupted. Please try a different file.'}), 400
        except Exception as pdf_error:
            logger.error('PDF validation failed: %s', pdf_error)
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({'success': False, 'error': 'Invalid PDF file. Please upload a valid PDF document.'}), 400

        # Extract text
        try:
            logger.info('Starting text extraction from: %s', filepath)
            extracted = extract_text_from_pdf(filepath)
            logger.info('Text extraction completed: %s characters', len(extracted))
        except Exception as extract_error:
            logger.error('Text extraction failed: %s', extract_error)
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            # Provide more specific error messages
            error_msg = str(extract_error)
            if 'password' in error_msg.lower() or 'encrypted' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'This PDF is password-protected. Please upload an unprotected PDF.'
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failed to extract text from PDF: {error_msg}'
                }), 400

        if not extracted or len(extracted.strip()) < 3:
            logger.error('Extracted text is too short: %s characters', len(extracted or ''))
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({
                'success': False,
                'error': (
                    'Could not extract sufficient text from this PDF. This appears to be a scanned PDF or image-only PDF. '
                    'Please upload a PDF with selectable text. If you need OCR support, install Tesseract OCR and restart the server.'
                ),
            }), 400

        # Save to user data
        try:
            meta = save_user_book(
                g.firebase_uid,
                g.firebase_email,
                file.filename,
                extracted,
                stored_filename,
            )
            logger.info('User book saved successfully for: %s', g.firebase_uid)
        except Exception as save_error:
            logger.error('Failed to save user book: %s', save_error)
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({'success': False, 'error': 'Failed to save data. Please try again.'}), 500

        # Prepare success response
        text_length = len(extracted)
        msg = f'PDF uploaded successfully! Extracted {text_length} characters from {file.filename}'
        if meta.get('truncated'):
            msg += ' (text was truncated for cloud storage limits; Q&A uses stored portion).'

        logger.info('Upload completed successfully for user: %s', g.firebase_uid)
        return jsonify({
            'success': True,
            'message': msg,
            'filename': file.filename,
            'text_length': text_length,
            'truncated_stored': meta.get('truncated', False),
        })

    except Exception as e:
        logger.error('Unexpected upload error: %s', e, exc_info=True)
        return jsonify({'success': False, 'error': 'An unexpected error occurred. Please try again.'}), 500


@app.route('/ask', methods=['POST', 'OPTIONS'])
@require_firebase_user
def ask():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request. Please provide JSON data.'}), 400

        question = data.get('question', '').strip()
        if not question:
            return jsonify({'success': False, 'error': 'Question cannot be empty. Please enter a question.'}), 400

        book = load_user_book(g.firebase_uid)
        extracted_text = book.get('extracted_text') or ''
        if len(extracted_text.strip()) < 10:
            return jsonify({'success': False, 'error': 'No PDF uploaded. Please upload a PDF first.'}), 400

        answer = ask_question(question, extracted_text)

        return jsonify({'success': True, 'question': question, 'answer': answer})

    except ValueError as e:
        logger.warning('Ask config error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        logger.error('Ask error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/summarize', methods=['GET', 'OPTIONS'])
@require_firebase_user
def summarize():
    try:
        book = load_user_book(g.firebase_uid)
        extracted_text = book.get('extracted_text') or ''
        pdf_name = book.get('pdf_name') or ''

        if len(extracted_text.strip()) < 10:
            return jsonify({'success': False, 'error': 'No PDF uploaded. Please upload a PDF first.'}), 400

        summary = generate_summary(extracted_text)

        return jsonify({'success': True, 'summary': summary, 'pdf_name': pdf_name})

    except ValueError as e:
        logger.warning('Summarize config error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        error_msg = str(e)
        logger.error('Summarize error: %s', e)

        if 'insufficient_quota' in error_msg:
            return jsonify(
                {
                    'success': False,
                    'error': 'OpenAI quota exceeded. Please add billing info at https://platform.openai.com/account/billing or use a different API key.',
                }
            ), 500

        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/speak', methods=['POST', 'OPTIONS'])
@require_firebase_user
def speak():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request. Please provide JSON data.'}), 400

        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'error': 'No text provided for text-to-speech.'}), 400

        filename = text_to_speech(text)

        return jsonify({'success': True, 'audio_file': f'/static/audio/{filename}'})

    except Exception as e:
        logger.error('Speak error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/translate', methods=['POST', 'OPTIONS'])
@require_firebase_user
def translate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request. Please provide JSON data.'}), 400

        target_language = data.get('language', 'English').strip()
        if not target_language:
            return jsonify({'success': False, 'error': 'Target language is required.'}), 400

        book = load_user_book(g.firebase_uid)
        extracted_text = book.get('extracted_text') or ''
        if len(extracted_text.strip()) < 10:
            return jsonify({'success': False, 'error': 'No PDF uploaded. Please upload a PDF first.'}), 400

        translation = translate_text(extracted_text, target_language)

        return jsonify({'success': True, 'translation': translation, 'target_language': target_language})

    except ValueError as e:
        logger.warning('Translate config error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        logger.error('Translate error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/insights', methods=['GET', 'OPTIONS'])
@require_firebase_user
def insights():
    try:
        book = load_user_book(g.firebase_uid)
        extracted_text = book.get('extracted_text') or ''
        pdf_name = book.get('pdf_name') or ''

        if len(extracted_text.strip()) < 10:
            return jsonify({'success': False, 'error': 'No PDF uploaded. Please upload a PDF first.'}), 400

        insights = extract_key_insights(extracted_text)

        return jsonify({'success': True, 'insights': insights, 'pdf_name': pdf_name})

    except ValueError as e:
        logger.warning('Insights config error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        logger.error('Insights error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sentiment', methods=['GET', 'OPTIONS'])
@require_firebase_user
def sentiment():
    try:
        book = load_user_book(g.firebase_uid)
        extracted_text = book.get('extracted_text') or ''
        pdf_name = book.get('pdf_name') or ''

        if len(extracted_text.strip()) < 10:
            return jsonify({'success': False, 'error': 'No PDF uploaded. Please upload a PDF first.'}), 400

        analysis = analyze_sentiment(extracted_text)

        return jsonify({'success': True, 'analysis': analysis, 'pdf_name': pdf_name})

    except ValueError as e:
        logger.warning('Sentiment config error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 503
    except Exception as e:
        logger.error('Sentiment error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/clear', methods=['POST', 'OPTIONS'])
@require_firebase_user
def clear_data():
    stored = clear_user_book(g.firebase_uid)
    _remove_upload_if_exists(stored)

    try:
        for fn in os.listdir(AUDIO_FOLDER):
            fp = os.path.join(AUDIO_FOLDER, fn)
            if os.path.isfile(fp):
                os.remove(fp)
    except Exception as e:
        logger.warning('Error cleaning audio files: %s', e)

    return jsonify({'success': True, 'message': 'All data cleared successfully.'})


@app.route('/history', methods=['GET', 'OPTIONS'])
@require_firebase_user
def get_history():
    """Get user's document history."""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = get_user_document_history(g.firebase_uid, limit)
        
        # Format dates for frontend
        for doc in history:
            if doc.get('uploadedAt'):
                doc['uploadedAt'] = doc['uploadedAt'].isoformat()
        
        return jsonify({'success': True, 'history': history})
    
    except Exception as e:
        logger.error('History error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history/load/<book_id>', methods=['GET', 'OPTIONS'])
@require_firebase_user
def load_from_history(book_id):
    """Load a specific historical document as the current document."""
    try:
        # Load the historical document
        historical_doc = load_historical_document(g.firebase_uid, book_id)
        
        if not historical_doc.get('extracted_text'):
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # Save it as the current document
        save_user_book(
            g.firebase_uid,
            g.firebase_email,
            historical_doc['pdf_name'],
            historical_doc['extracted_text'],
            historical_doc['stored_filename']
        )
        
        return jsonify({
            'success': True,
            'message': f'Document "{historical_doc["pdf_name"]}" loaded successfully',
            'pdf_name': historical_doc['pdf_name'],
            'text_length': len(historical_doc['extracted_text']),
            'truncated': historical_doc['truncated']
        })
    
    except Exception as e:
        logger.error('Load history error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history/delete/<book_id>', methods=['DELETE', 'OPTIONS'])
@require_firebase_user
def delete_from_history(book_id):
    """Delete a historical document."""
    try:
        stored_filename = delete_historical_document(g.firebase_uid, book_id)
        
        # Remove the actual file if it exists
        if stored_filename:
            _remove_upload_if_exists(stored_filename)
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
    
    except Exception as e:
        logger.error('Delete history error: %s', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'success': False, 'error': 'File too large. Maximum upload size is 16MB.'}), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print('=' * 50)
    print('AI Book Assistant - Starting Server...')
    print('=' * 50)
    print(f'Project root: {PROJECT_ROOT}')
    print(f'Upload folder: {UPLOAD_FOLDER}')
    print(f'Audio folder: {AUDIO_FOLDER}')
    print(f'Firebase configured: {is_firebase_configured()}')
    print('=' * 50)

    if not _openrouter_api_key():
        print('WARNING: OpenRouter API key not set in .env file!')
        print('=' * 50)

    if not is_firebase_configured():
        print('WARNING: Firebase not configured — set FIREBASE_SERVICE_ACCOUNT_PATH and web keys in .env')
        print('=' * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
