# AI Book Assistant - API Documentation

Complete API reference for the AI Book Assistant web application.

## 🔐 Authentication

All API endpoints (except `/health`) require Firebase authentication. Include the Firebase ID token in the `Authorization` header:

```http
Authorization: Bearer <firebase-id-token>
Content-Type: application/json
```

## 📊 Base URL

```
http://localhost:5000
```

## 🛠️ API Endpoints

### Health Check

#### GET /health
Check if the application is running and configured.

**Response:**
```json
{
    "status": "healthy",
    "service": "AI Book Assistant",
    "firebase_configured": true
}
```

---

### User Session

#### GET /api/session
Get current user's session information and PDF status.

**Authentication:** Required

**Response:**
```json
{
    "success": true,
    "has_pdf": true,
    "pdf_name": "document.pdf",
    "text_length": 15420,
    "truncated": false
}
```

---

### PDF Operations

#### POST /upload
Upload and process a PDF file for AI analysis.

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Request Body:**
- `file` (File) - PDF file to upload (max 16MB)

**Response:**
```json
{
    "success": true,
    "message": "PDF uploaded successfully! Extracted 15420 characters from document.pdf",
    "filename": "document.pdf",
    "text_length": 15420,
    "truncated_stored": false
}
```

**Errors:**
```json
{
    "success": false,
    "error": "Invalid file type. Please upload a PDF file."
}
```

---

#### POST /clear
Clear all user data including uploaded PDFs and generated audio.

**Authentication:** Required

**Response:**
```json
{
    "success": true,
    "message": "All data cleared successfully."
}
```

---

### AI Analysis Endpoints

#### POST /ask
Ask questions about the uploaded PDF content.

**Authentication:** Required

**Request Body:**
```json
{
    "question": "What is the main topic of this document?"
}
```

**Response:**
```json
{
    "success": true,
    "question": "What is the main topic of this document?",
    "answer": "Based on the PDF content, the main topic appears to be..."
}
```

---

#### GET /summarize
Generate a comprehensive summary of the uploaded PDF.

**Authentication:** Required

**Response:**
```json
{
    "success": true,
    "summary": "This document discusses the importance of artificial intelligence...",
    "pdf_name": "document.pdf"
}
```

---

#### POST /translate
Translate PDF content to a target language.

**Authentication:** Required

**Request Body:**
```json
{
    "language": "Spanish"
}
```

**Response:**
```json
{
    "success": true,
    "translation": "Este documento discute la importancia de la inteligencia artificial...",
    "target_language": "Spanish"
}
```

---

#### GET /insights
Extract key insights, themes, and important points from the PDF.

**Authentication:** Required

**Response:**
```json
{
    "success": true,
    "insights": "## Main Themes\n\n- Artificial Intelligence\n- Machine Learning\n\n## Key Insights\n\n- The document emphasizes...",
    "pdf_name": "document.pdf"
}
```

---

#### GET /sentiment
Analyze the sentiment, tone, and writing style of the PDF.

**Authentication:** Required

**Response:**
```json
{
    "success": true,
    "analysis": "## Overall Sentiment: Positive\n\nThe document maintains an optimistic and forward-looking tone...",
    "pdf_name": "document.pdf"
}
```

---

#### POST /speak
Convert text to speech using Google TTS.

**Authentication:** Required

**Request Body:**
```json
{
    "text": "This is the summary text to convert to speech"
}
```

**Response:**
```json
{
    "success": true,
    "audio_file": "/static/audio/speech_abc123.mp3"
}
```

---

## 🚨 Error Responses

All endpoints return consistent error format:

```json
{
    "success": false,
    "error": "Error description"
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input, missing required fields)
- `401` - Unauthorized (invalid or missing Firebase token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (invalid endpoint)
- `413` - Payload Too Large (file exceeds 16MB)
- `500` - Internal Server Error
- `503` - Service Unavailable (API key issues, quota exceeded)

### Error Types

#### PDF Processing Errors
- `"Invalid file type. Please upload a PDF file."` - Non-PDF file uploaded
- `"File too large. Maximum upload size is 16MB."` - File exceeds size limit
- `"PDF appears to be empty or corrupted."` - Invalid PDF format
- `"This PDF is password-protected."` - Encrypted PDF
- `"Could not extract sufficient text from this PDF."` - Scanned PDF without OCR

#### AI Processing Errors
- `"No PDF uploaded. Please upload a PDF first."` - No document available
- `"OpenAI API key not set."` - Missing API key
- `"OpenAI quota exceeded."` - API usage limit reached
- `"Failed to generate summary."` - AI processing error

## 🔧 Rate Limits

### OpenAI API
- **GPT-3.5-turbo:** ~500,000 tokens per $5
- **Rate Limits:** ~3,000 requests per minute
- **Recommendation:** Implement client-side rate limiting

### File Upload
- **Size Limit:** 16MB per file
- **Types:** PDF only
- **Storage:** User-specific, cleared on logout

## 📝 Usage Examples

### JavaScript/Fetch

```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('/upload', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${firebaseToken}`,
    },
    body: formData
});

const result = await response.json();
if (result.success) {
    console.log('Upload successful:', result.message);
} else {
    console.error('Upload failed:', result.error);
}

// Generate Summary
const summaryResponse = await fetch('/summarize', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${firebaseToken}`,
    }
});

const summaryResult = await summaryResponse.json();
if (summaryResult.success) {
    console.log('Summary:', summaryResult.summary);
}
```

### Python/Requests

```python
import requests

# Upload PDF
files = {'file': open('document.pdf', 'rb')}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:5000/upload',
    files=files,
    headers=headers
)

result = response.json()
print(result['message'])
```

## 🔍 Testing

Use the provided test script:

```bash
python utils/test_api.py
```

This will test:
- API key validity
- OpenAI connectivity
- Basic functionality

## 🚀 Deployment

### Environment Setup
1. Set `OPENAI_API_KEY` environment variable
2. Configure Firebase settings (optional)
3. Set `FLASK_ENV=production`

### Production Server
```bash
gunicorn app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🔒 Security Considerations

- Always validate Firebase tokens
- Sanitize all user inputs
- Implement rate limiting on client-side
- Use HTTPS in production
- Validate file types and sizes
- Never expose API keys in frontend code

## 📞 Support

For API issues:
1. Check the [troubleshooting guide](TROUBLESHOOTING.md)
2. Verify Firebase configuration
3. Check OpenAI API key and quota
4. Review server logs in `logs/` directory

---

*Last updated: April 2026*
