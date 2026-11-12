# ✈️ TripMate AI
### AI-Powered Interactive Educational Field-Trip Platform

👩‍💻 Team Members

Priya Naulakha

Mani Agrawal

🌍 About TripmateAI
**TripMate AI** transforms traditional educational field trips into interactive, engaging, and curiosity-driven learning adventures. It combines Artificial Intelligence, gamification, and experiential learning to help students explore real-world places while learning beyond the classroom.

Instead of simply visiting historical or educational destinations, students can interact with an AI Learning Companion, participate in treasure hunts, solve quizzes, complete missions, and track their learning progress.

---

## 🌟 Key Features

### 🤖 AI Learning Companion
- AI-powered chatbot that answers students' questions about destinations.
- Provides educational explanations and interesting facts.
- Supports interactive learning through conversations.
- Integrates with Google Gemini API.

### 🗺️ Destination Exploration
- Explore educational and historical destinations.
- Interactive maps with location markers.
- Discover historical facts, timelines, and related subjects.
- Access curated educational information about destinations.

### 📸 AI-Powered Treasure Hunt
- Interactive photo-based learning missions.
- Students capture and upload photos to complete challenges.
- AI evaluates submitted photos and provides feedback.
- Earn experience points (XP) for completing missions.

### 🎯 Quiz Arena
- Interactive quizzes to test students' knowledge.
- Multiple question types.
- Track quiz scores and performance.

### 👥 Student Groups
- Group-based learning activities.
- Team collaboration and participation.
- Team leaderboards.

### 🏆 Gamification & Achievements
- Earn XP by completing missions and quizzes.
- Unlock achievement badges.
- View student and team leaderboards.
- Track learning progress.

### 👩‍🏫 Teacher Dashboard
- Create and manage educational trips.
- Manage students and groups.
- Generate learning activities.
- Review student photo submissions.
- Monitor student performance and analytics.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| AI Integration | Google Gemini API |
| Authentication | JWT |
| API Communication | JavaScript Fetch API |
| Maps | Leaflet.js, OpenStreetMap |
| Charts | Chart.js |

---

## 📁 Project Structure

```text
TripMateAI/
│
├── backend/
│   ├── main.py
│   ├── ai.py
│   ├── kb.py
│   ├── models.py
│   ├── routers.py
│   ├── security.py
│   ├── seed.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── README.md
└── .gitignore
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/TripMateAI.git
```

Navigate to the project directory:

```bash
cd TripMateAI
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Create a .env file inside the backend directory.
Open backend/.env and add your own credentials:

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
SECRET_KEY=your_secret_key

Important:

Get your Gemini API key from Google AI Studio.

Replace the placeholder values with your own credentials.

Never upload or share your .env file.

The .env file is excluded from Git using .gitignore.

AI features may use fallback responses if a valid Gemini API key is not configured.

### 5. Run the Application

From the project root directory, execute:

```bash
python -m uvicorn backend.main:app --reload
```

### 6. Open the Application

- **Website:** http://127.0.0.1:8000
- **API Documentation:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/api/health

---

## 🔑 Demo Credentials

| Role | Email | Password |
|---|---|---|
| Teacher | teacher@demo.com | demo12345 |
| Student | aarav@demo.com | demo12345 |
| Student | diya@demo.com | demo12345 |

**Demo Invitation Code:** `TAJ123`

---

## 🚀 Deployment

TripMate AI can be deployed as a single web service using [Render](https://render.com/).

The FastAPI backend serves the frontend, so a separate frontend deployment is not required.

**Build Command**

```bash
pip install -r backend/requirements.txt
```

**Start Command**

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Configure the required environment variables in the Render dashboard before deployment.

**Note:** The current application uses SQLite and local file uploads. Persistent storage should be configured before using the deployed application for long-term data storage.

---

## 🎯 Project Objective

The main objective of TripMate AI is to bridge the gap between classroom education and real-world experiences.

By combining AI-powered assistance, interactive exploration, and gamified activities, the platform aims to make educational field trips more engaging, collaborative, and effective.

---

## 🔮 Future Enhancements

- Personalized AI-based learning recommendations.
- Real-time collaborative challenges.
- More educational destinations and learning modules.
- Advanced student performance analytics.
- Persistent cloud database and media storage.
- Enhanced AI-based image verification.

---

## 🤝 Contributing

Contributions and suggestions are welcome!

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Commit your changes.
5. Submit a Pull Request.

---

## 📄 License

This project is currently developed as an educational project. Licensing details can be added when a suitable open-source license is selected.

---

**Made with ❤️ to make learning beyond classrooms more interactive and meaningful.**
