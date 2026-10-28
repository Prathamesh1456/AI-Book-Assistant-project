# AI Book Assistant

AI Book Assistant is a Python Flask-based web application that uses Artificial Intelligence to analyze PDF documents and make learning easier and more interactive. It can summarize books, answer questions about document content, translate text, generate insights, and convert text into speech.

## 🌟 Features

- 📄 **PDF Upload and Processing** – Extract text from PDF documents.
- 🤖 **AI-Powered Summarization** – Generate summaries of book content.
- 💬 **Question and Answer** – Ask questions about uploaded PDFs.
- 📝 **MCQ Generation** – Generate multiple-choice questions for learning and practice.
- 🌐 **Multi-Language Translation** – Translate content into multiple languages.
- 🔊 **Text-to-Speech** – Listen to summaries and document content.
- 🔐 **Secure Authentication** – Firebase-based user authentication.
- 🎨 **Modern User Interface** – Responsive design with dark and light themes.

## 🛠️ Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **AI Integration:** OpenRouter API
- **Authentication:** Firebase Authentication
- **Document Processing:** Python PDF-processing libraries
- **Text-to-Speech:** gTTS

## 🚀 Getting Started

### Prerequisites

Install the following software:

- Python 3.8 or later
- Git
- An OpenRouter API key for AI features
- A Firebase project for authentication

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/Prathamesh1456/AI-Book-Assistant-project.git
cd AI-Book-Assistant-project
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure environment variables**

Copy the example environment file.

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure the required API key and Firebase settings.

Never upload your actual `.env` file or Firebase service-account private key to GitHub.

**4. Run the application**

```bash
python app.py
```

**5. Open the application**

Open your browser and visit:

http://127.0.0.1:5000

The application address may differ if you configure a different port.

## 📁 Project Structure

```text
AI-Book-Assistant-project/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── firestore.rules
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── auth_firebase.py
│   └── firebase_service.py
├── frontend/
│   ├── templates/
│   │   ├── index.html
│   │   ├── login.html
│   │   └── register.html
│   └── static/
│       ├── css/
│       │   ├── auth.css
│       │   └── style.css
│       ├── js/
│       │   ├── app.js
│       │   └── firebase-init.js
│       └── audio/
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

## 🔑 Environment Variables

Configure these variables in your local `.env` file as required by your application:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
OFFLINE_MODE=false

FIREBASE_SERVICE_ACCOUNT_PATH=
FIREBASE_WEB_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_STORAGE_BUCKET=
FIREBASE_MESSAGING_SENDER_ID=
FIREBASE_APP_ID=
```

Add your own values locally. Keep real credentials private.

## 🔌 API Endpoints

The application includes endpoints for operations such as:

- PDF upload and processing
- Asking questions about document content
- Summarization
- Translation
- Extracting key insights
- Sentiment analysis
- Text-to-speech
- Authentication and user sessions
- Application health checks

Refer to [`docs/API.md`](docs/API.md) for endpoint details.

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 🔐 Security

- Keep API keys and passwords out of source code.
- Never commit `.env` or Firebase service-account private keys.
- Configure appropriate Firebase authentication and Firestore security rules.
- Validate uploaded files and user input.
- Review Firebase security rules before deployment.

## 📄 License

Add your preferred open-source license if you intend to distribute this project under one.

## 🤝 Contributing

Contributions and suggestions are welcome. You can fork the repository, create a feature branch, make improvements, and submit a pull request.

---

**Built with Python, Flask, AI, and Firebase.**