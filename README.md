---
title: Resume Helper
emoji: 📄
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Resume Generator & Analyzer

An AI-powered resume analysis and career consultation application built with FastAPI. This application uses machine learning to classify resumes into job categories and provides personalized career advice through an AI chat interface.

## Features

- 🔐 **User Authentication**: Secure login and registration system
- 📄 **PDF Resume Upload**: Upload and extract text from PDF resumes
- 🤖 **ML-Powered Classification**: Automatically categorize resumes into 24 different job categories
- 💬 **AI Career Consultant**: Chat with an AI assistant specialized in resume improvement and career strategy
- 🎨 **Modern UI**: Clean, professional interface for resume analysis and editing
- 📊 **Resume Analysis**: Get detailed insights and suggestions for your resume

## Job Categories

The ML model can classify resumes into the following categories:
- Accountant, Advocate, Agriculture, Apparel, Arts, Aviation
- Automobile, Banking, BPO, Business-Development
- Chef, Consultant, Construction
- Designer, Digital-Media
- Engineering
- Finance, Fitness
- Healthcare, HR
- Information-Technology
- Public-Relations
- Sales, Teacher

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Resume_generator
```

### 2. Create a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root directory:

```bash
touch .env
```

Add your HuggingFace API token to the `.env` file:

```
HUGGINGFACE_API_TOKEN=your_huggingface_token_here
```

> **Note**: Get your free HuggingFace API token from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### 5. Download Required NLTK Data

The application will automatically download required NLTK data on first run. However, if you encounter issues, you can manually download them:

```python
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### 6. Ensure ML Model is Present

Make sure the following ML model file is in the project root:
- `resume_classification_model1.pkl`

If you don't have this file, you'll need to train the model or obtain it from the project maintainer.

### 7. Create Required Directories

```bash
mkdir -p uploads static templates
```

## Running the Application

### Start the Development Server

```bash
uvicorn app:app --reload
```

The application will be available at: **http://localhost:8000**

### Alternative: Run on a Different Port

```bash
uvicorn app:app --reload --port 8080
```

## Usage

### 1. Register an Account
- Navigate to http://localhost:8000
- Click on "Register" or go to http://localhost:8000/register
- Create a new account with a username and password

### 2. Login
- Use your credentials to log in
- You'll be redirected to the home page

### 3. Upload Resume
- Click "Upload Resume" or drag and drop a PDF file
- The system will extract text and classify your resume
- View the analysis results

### 4. Chat with AI Consultant
- After uploading a resume, use the chat interface
- Ask questions about improving your resume
- Get personalized career advice and suggestions

### 5. Logout
- Click the logout button when finished

## Project Structure

```
Resume_generator/
├── app.py                              # Main FastAPI application
├── Models.py                           # Pydantic models for validation
├── requirements.txt                    # Python dependencies
├── .env                               # Environment variables (not in git)
├── Login_Db.json                      # User database (auto-generated)
├── resume_classification_model1.pkl   # ML model for classification
├── templates/                         # HTML templates
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── result.html
│   └── result_new.html
├── static/                            # Static files (CSS, JS, images)
└── uploads/                           # Uploaded resume files
```

## API Endpoints

- `GET /` - Redirect to login
- `GET /register` - Registration page
- `POST /register` - Handle registration
- `GET /login` - Login page
- `POST /login` - Handle login
- `GET /home` - Home page (authenticated)
- `GET /logout` - Logout user
- `POST /upload-pdf` - Upload and analyze resume
- `POST /chat` - Chat with AI consultant

## Technologies Used

- **Backend**: FastAPI, Python
- **ML/AI**: scikit-learn, NLTK, LangChain, HuggingFace
- **PDF Processing**: pypdf
- **Frontend**: HTML, CSS, JavaScript (Jinja2 templates)
- **Authentication**: Session-based with cookies

## Troubleshooting

### NLTK Download Issues

If you encounter SSL certificate errors when downloading NLTK data, the app includes a workaround. If issues persist:

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Model Loading Errors

Ensure the pickle file `resume_classification_model1.pkl` is in the project root and was created with a compatible Python version.

### Port Already in Use

If port 8000 is already in use:

```bash
uvicorn app:app --reload --port 8080
```

### HuggingFace API Issues

- Verify your API token is correct in the `.env` file
- Check your internet connection
- Ensure you have access to the Meta-Llama-3-8B-Instruct model

## Security Notes

⚠️ **Important**: 
- Never commit your `.env` file to Git
- Change default passwords in production
- Use HTTPS in production
- Implement proper password hashing (currently uses plain text - should be updated)
- Add rate limiting for production use

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is available for educational and personal use.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: This application is designed for educational purposes. For production use, implement proper security measures including password hashing, HTTPS, rate limiting, and input validation.
