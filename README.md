# ✈️ TripMate AI
### AI-Powered Interactive Educational Field-Trip Platform

**Turning educational field trips into interactive, AI-powered learning adventures.**

## 👩‍💻 Team Members

- **Priya Naulakha**
- **Mani Agrawal**

---

## 🌍 About the Project

**TripMate AI** transforms traditional educational field trips into interactive, engaging, and curiosity-driven learning experiences. By combining Artificial Intelligence, gamification, and experiential learning, it enables students to explore real-world destinations while learning beyond the classroom.

Rather than simply visiting historical or educational places, students can interact with an AI Learning Companion, participate in photo-based treasure hunts, solve quizzes, complete learning missions, and track their progress.

The platform bridges the gap between theoretical classroom knowledge and practical real-world exploration.

---

## 🌟 Key Features

### 🤖 1. AI Learning Companion
- AI-powered chatbot that answers students' questions about destinations.
- Provides educational explanations, historical information, and interesting facts.
- Enables interactive, conversation-based learning.
- Powered by Google Gemini API.

### 🗺️ 2. Destination Exploration
- Explore historical and educational destinations.
- Interactive maps with location markers.
- Discover historical facts, timelines, and subject-related information.
- Access curated educational content about destinations.

### 📸 3. AI-Powered Treasure Hunt
- Interactive, photo-based learning missions.
- Students capture and upload photographs to complete challenges.
- AI evaluates submitted photographs and provides feedback.
- Earn Experience Points (XP) for successfully completing missions.

### 🎯 4. Quiz Arena
- Interactive quizzes to test students' knowledge.
- Multiple question types.
- Track quiz scores and individual performance.

### 👥 5. Student Groups
- Group-based educational activities.
- Collaborative learning and team participation.
- Team leaderboards to encourage healthy competition.

### 🏆 6. Gamification & Achievements
- Earn XP by completing quizzes and missions.
- Unlock achievement badges.
- Individual and team leaderboards.
- Track learning progress and achievements.

### 👩‍🏫 7. Teacher Dashboard
- Create and manage educational trips.
- Organize students and groups.
- Manage learning activities.
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
| Interactive Maps | Leaflet.js, OpenStreetMap |
| Data Visualization | Chart.js |

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

Follow these steps to run TripMate AI locally.

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

Activate the environment on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `backend` directory.

Add the following environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
SECRET_KEY=your_secret_key
```

**Important:**
- Obtain your Gemini API key from [Google AI Studio](https://aistudio.google.com/).
- Replace the placeholder values with your actual credentials.
- Never upload or share your `.env` file.
- The `.env` file is excluded from Git using `.gitignore`.
- Some AI features may use fallback responses if a valid Gemini API key is unavailable.

### 5. Run the Application

From the project root directory, execute:

```bash
python -m uvicorn backend.main:app --reload
```

### 6. Access the Application

Once the server starts, open the following URLs:

| Service | URL |
|---|---|
| Website | http://127.0.0.1:8000 |
| API Documentation | http://127.0.0.1:8000/docs |
| Health Check | http://127.0.0.1:8000/api/health |

---

## 🔑 Demo Credentials

Use the following credentials to explore the application:

| Role | Email | Password |
|---|---|---|
| Teacher | teacher@demo.com | demo12345 |
| Student | aarav@demo.com | demo12345 |
| Student | diya@demo.com | demo12345 |

**Demo Invitation Code:** `TAJ123`

---

## 🚀 Deployment

TripMate AI is deployed using [Render](https://render.com/).

The FastAPI backend serves the frontend, allowing the application to run as a single web service without requiring a separate frontend deployment.

**Build Command:**

```bash
pip install -r backend/requirements.txt
```

**Start Command:**

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Configure the required environment variables in the Render dashboard before deployment.

**Storage Note:** The application currently uses SQLite and local file uploads. Persistent storage should be configured for long-term database and uploaded-media retention in production.

---

## 🎯 Project Objective

TripMate AI aims to transform conventional educational field trips into meaningful learning experiences by connecting classroom concepts with real-world exploration.

Through AI-powered assistance, interactive challenges, collaborative activities, and gamification, the platform encourages students to learn through curiosity, participation, and discovery.

---

## 🔮 Future Enhancements

- Personalized AI-driven learning recommendations.
- Real-time collaborative learning challenges.
- Expansion of educational destinations and learning modules.
- Advanced student performance analytics.
- Cloud-based database and persistent media storage.
- Enhanced AI-based image verification and evaluation.

---

## 🤝 Contributing

Contributions, suggestions, and feedback are welcome!

To contribute:

1. Fork the repository.
2. Create a new branch for your changes.
3. Implement your improvements.
4. Commit and push your changes.
5. Submit a Pull Request.

---

## 📄 License

This project is currently developed as an educational project. Licensing details can be added when an appropriate open-source license is selected.

---

<div align="center">

### ✨ Explore. Discover. Learn.

**Made with ❤️ to make learning beyond the classroom more interactive, collaborative, and meaningful.**

</div>
