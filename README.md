# HR Appraisal Assessment System
A comprehensive employee assessment platform built with FastAPI and Streamlit that provides role-based appraisal tests with AI-powered feedback using Google's Gemini AI and vector database technology.

## 🚀 Features
- **Role-Based Assessments**: Customizable tests for different job roles
- **AI-Powered Feedback**: Detailed performance analysis using Google Gemini AI
- **Vector Database**: Efficient question storage and retrieval using ChromaDB
- **Multiple Interfaces**: Both REST API and Streamlit web interface
- **Docker Support**: Containerized deployment ready
- **Real-time Scoring**: Instant results with detailed feedback
- **Scalable Architecture**: Built with FastAPI for high performance

## 🛠 Tech Stack
- **Backend**: FastAPI, Python 3.11
- **Frontend**: Streamlit
- **AI/ML**: Google Gemini AI (via LangChain)
- **Database**: ChromaDB (Vector Database)
- **Deployment**: Docker, Gunicorn
- **Authentication**: Google API Key

## 📋 Prerequisites

- Python 3.11+
- Google API Key (for Gemini AI)
- Docker (optional, for containerized deployment)

## 🔧 Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kartavya-AI/Employee-Appraisal
   cd Employee-Appraisal
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   PORT=8080
   ```

5. **Create knowledge base**
   Create a `knowledge_base.json` file with your assessment questions:
   ```json
   {
     "Project Manager": [
       {
         "question": "What is the primary purpose of a Gantt chart?",
         "options": ["Budget tracking", "Project scheduling", "Risk assessment", "Team communication"],
         "answer": "Project scheduling"
       }
     ]
   }
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t hr-assessment .
   ```

2. **Run the container**
   ```bash
   docker run -p 8080:8080 -e GOOGLE_API_KEY=your_api_key hr-assessment
   ```

## 🚀 Usage

### Running the FastAPI Server

```bash
python api.py
```

The API will be available at `http://localhost:8080`

### Running the Streamlit Interface

```bash
streamlit run app.py
```

The Streamlit app will be available at `http://localhost:8501`

## 📚 API Documentation

### Base URL
```
http://localhost:8080
```

### Endpoints

#### Health Check
```http
GET /health
```
Returns system status and available roles.

#### Get Available Roles
```http
GET /roles
```
Returns list of all available job roles.

#### Start Assessment
```http
POST /assessment/start
```
**Request Body:**
```json
{
  "role": "Software Developer",
  "num_questions": 10
}
```

**Response:**
```json
{
  "role": "Software Developer",
  "questions": [
    {
      "question": "What is polymorphism?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option B"
    }
  ],
  "total_questions": 10
}
```

#### Submit Assessment
```http
POST /assessment/submit
```
**Request Body:**
```json
{
  "role": "Software Developer",
  "answers": ["Option B", "Option A"],
  "questions": [
    {
      "question": "What is polymorphism?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option B"
    }
  ]
}
```

**Response:**
```json
{
  "role": "Software Developer",
  "score": 8,
  "total_questions": 10,
  "percentage": 80.0,
  "feedback": "Detailed AI-generated feedback..."
}
```

#### Get Role Statistics
```http
GET /stats/role/{role}
```
Returns statistics for a specific role.

## 📊 Knowledge Base Structure

The `knowledge_base.json` file should follow this structure:

```json
{
  "Role Name": [
    {
      "question": "Question text here",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "answer": "Correct option text"
    }
  ]
}
```

### Example Roles
- Software Developer
- Project Manager
- Data Scientist
- HR Manager
- Marketing Specialist
- Sales Representative

## 🔍 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI       │    │   ChromaDB      │
│   Frontend      │◄──►│    Backend       │◄──►│   Vector DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Google Gemini  │
                       │   AI (LangChain) │
                       └──────────────────┘
```

## 🐳 Docker Configuration

The Dockerfile includes:
- Python 3.11 slim base image
- SQLite3 installation
- Non-root user setup
- Gunicorn with Uvicorn workers
- Port 8080 exposure

## 🔒 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini AI API key | Yes |
| `PORT` | Server port (default: 8080) | No |
| `PYTHONUNBUFFERED` | Python output buffering | No |
| `PYTHONDONTWRITEBYTECODE` | Prevent .pyc files | No |

## 📝 Features in Detail

### AI-Powered Feedback
- Uses Google's Gemini AI model
- Provides detailed performance analysis
- Offers personalized improvement suggestions
- Categorizes performance levels

### Vector Database Integration
- ChromaDB for efficient question storage
- Semantic search capabilities
- Automatic database rebuilding when knowledge base changes
- Persistent storage support

### Multi-Interface Support
- REST API for integration with other systems
- Streamlit web interface for direct user access
- CORS enabled for cross-origin requests

## 🧪 Testing

To test the API endpoints:

```bash
# Health check
curl -X GET "http://localhost:8080/health"

# Get available roles
curl -X GET "http://localhost:8080/roles"

# Start assessment
curl -X POST "http://localhost:8080/assessment/start" \
  -H "Content-Type: application/json" \
  -d '{"role": "Software Developer", "num_questions": 5}'
```

## 🚨 Troubleshooting

### Common Issues

1. **Google API Key Error**
   - Ensure `GOOGLE_API_KEY` is set in environment variables
   - Verify the API key is valid and has proper permissions

2. **ChromaDB Issues**
   - Delete the `chroma_db` directory to force database recreation
   - Check file permissions for the database directory

3. **Knowledge Base Not Found**
   - Ensure `knowledge_base.json` exists in the root directory
   - Verify JSON format is valid

4. **Port Already in Use**
   - Change the PORT environment variable
   - Kill existing processes using the port

### Logging
The application includes comprehensive logging. Check console output for detailed error messages.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## 🔄 Version History

- **v1.0.0**: Initial release with FastAPI backend and Streamlit frontend
- Features: Role-based assessments, AI feedback, Docker support

---

*Built with ❤️ using FastAPI, Streamlit, and Google Gemini AI*
