# AI Book Assistant

A modern web application that uses AI to analyze PDF documents, providing summaries, Q&A, translations, and more.

## 🌟 Features

- 📄 **PDF Upload & Processing** - Extract text from PDFs with multiple methods
- 🤖 **AI-Powered Analysis** - Summarization, Q&A, key insights, sentiment analysis
- 🌐 **Multi-Language Translation** - Translate content to 12+ languages
- 🔊 **Text-to-Speech** - Listen to summaries and content
- 🔐 **Secure Authentication** - Firebase-based user management
- 🎨 **Modern UI** - Glassmorphism design with dark/light themes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- (Optional) Firebase account for user authentication

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-book-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open browser to: `http://localhost:5000`

## 📁 Project Structure

```
ai-book-assistant/
├── 📄 app.py                    # Main application entry point
├── 📄 requirements.txt            # Python dependencies
├── 📄 .env                      # Environment variables (API keys)
├── 📄 .gitignore               # Git ignore rules
│
├── 📁 backend/                  # Flask backend application
│   ├── 📄 __init__.py
│   ├── 📄 app.py              # Main Flask app with all routes
│   ├── 📄 auth_firebase.py    # Firebase authentication
│   └── 📄 firebase_service.py # Firebase services
│
├── 📁 frontend/                 # Frontend assets
│   ├── 📁 templates/           # HTML templates
│   │   ├── 📄 index.html      # Main application page
│   │   ├── 📄 login.html      # User login page
│   │   └── 📄 register.html   # User registration page
│   └── 📁 static/              # Static files
│       ├── 📁 css/
│       │   └── 📄 style.css      # Main stylesheet
│       ├── 📁 js/
│       │   ├── 📄 app.js         # Main JavaScript application
│       │   └── 📄 firebase-init.js # Firebase initialization
│       └── 📁 audio/            # Generated audio files
│
├── 📁 utils/                   # Utility scripts
│   ├── 📄 setup.py           # Initial setup script
│   └── 📄 test_api.py         # API testing script
│
├── 📁 docs/                    # Documentation
│   ├── 📄 API.md             # API documentation
│   ├── 📄 DEPLOYMENT.md      # Deployment guide
│   └── 📄 TROUBLESHOOTING.md # Troubleshooting guide
│
├── 📁 uploads/                 # User uploaded PDFs
└── 📁 logs/                    # Application logs
```

## 🔑 Environment Variables

Create a `.env` file with the following variables:

```bash
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Firebase Configuration (optional - for user authentication)
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/service-account.json
FIREBASE_WEB_API_KEY=your-web-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-sender-id
FIREBASE_APP_ID=your-app-id
```

## 🛠️ API Endpoints

### Authentication Required
All API endpoints (except health check) require Firebase authentication.

### PDF Operations
- `POST /upload` - Upload and process PDF files
- `GET /api/session` - Get current user session info
- `POST /clear` - Clear user data and uploads

### AI Analysis Endpoints
- `POST /ask` - Ask questions about uploaded PDF
- `GET /summarize` - Generate PDF summary
- `POST /translate` - Translate PDF content
- `GET /insights` - Extract key insights from PDF
- `GET /sentiment` - Analyze sentiment and tone
- `POST /speak` - Convert text to speech

### System Endpoints
- `GET /health` - Application health check
- `GET /` - Main application page
- `GET /login` - User login page
- `GET /register` - User registration page

## 🧪 Development

### Running in Development
```bash
python app.py
```

The application will start on `http://localhost:5000` with debug mode enabled.

### Testing API
```bash
python utils/test_api.py
```

## 📚 Documentation

- [API Documentation](docs/API.md) - Detailed API reference
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 🔧 Configuration

### PDF Processing
- Multiple extraction methods: PyMuPDF, PyPDF2, pdfplumber
- Optional OCR support with Tesseract
- Maximum file size: 16MB
- Supported formats: PDF

### AI Features
- Models: OpenAI GPT-3.5-turbo
- Translation: 12+ languages supported
- Text-to-speech: Google TTS (gTTS)
- Sentiment analysis: Tone, style, audience analysis

## 🎨 UI Features

- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark/Light Themes** - Toggle between themes
- **Glassmorphism** - Modern frosted glass effects
- **Smooth Animations** - Background gradients and transitions
- **Progressive Enhancement** - Works without JavaScript

## 🔐 Security

- Firebase Authentication
- CORS protection
- File type validation
- Size limits enforcement
- Input sanitization

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)
- Review the [API documentation](docs/API.md)

---

**Built with ❤️ using OpenAI, Flask, and Firebase**
