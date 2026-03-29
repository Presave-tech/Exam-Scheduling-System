# Automated Exam Scheduling System

A full-stack web application that generates conflict-free exam timetables using the **Greedy Graph Coloring Algorithm**.

---

## 🛠 Team Setup & Installation

Follow these steps to get the project running on your local machine:

### 1. Prerequisites
- **Python 3.10+** installed.
- **XAMPP** (for the MySQL database).
- **Git** (for cloning the repository).

### 2. Initial Setup
```powershell
# Clone the repository
git clone <YOUR_GITHUB_REPO_URL>
cd daa_pbl

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup (XAMPP)
1. Open the **XAMPP Control Panel**.
2. Start **Apache** and **MySQL**.
3. Go to [localhost/phpmyadmin](http://localhost/phpmyadmin).
4. Create a new database named **`exam_db`**.
   - *Note: The system uses default XAMPP credentials (user: `root`, no password).*

### 4. Running the Application
```powershell
python run.py
```
Visit **http://127.0.0.1:5000** in your browser. The tables will be created automatically on the first run.

---

## 🚀 How to Use

## 🗂️ Project Structure

```
daa_pbl/
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── models.py         # SQLAlchemy ORM models
│   ├── graph.py          # Conflict graph + Greedy Coloring algorithm ← CORE
│   ├── scheduler.py      # Scheduling pipeline orchestrator
│   └── routes.py         # All Flask route handlers
├── templates/
│   ├── base.html         # Base layout (sidebar + topbar)
│   ├── index.html        # Dashboard
│   ├── subjects.html     # Add/list subjects
│   ├── students.html     # Add/list students
│   ├── enrollments.html  # Enroll students in subjects
│   └── timetable.html    # View generated timetable
├── static/
│   ├── css/style.css     # Custom premium CSS
│   └── js/main.js        # Frontend logic
├── instance/
│   └── exam.db           # SQLite database (auto-created)
├── run.py                # Entry point
├── config.py             # App configuration
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip

### Steps

```bash
# 1. Navigate to the project folder
cd daa_pbl

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python run.py
```

The app will start at: **http://127.0.0.1:5000**

---

## 🚀 How to Use

1. **Add Data** — Manually add Subjects → Students → Enrollments using the sidebar pages.
2. **Generate Timetable** — Click the "Generate Timetable" button on the Dashboard or Timetable page.
3. **View Results** — The Timetable page shows the algorithm log + full schedule.
4. **Export** — Download as CSV or use Print/PDF button.

---

## 🧮 Algorithm Explanation

### Problem Modelling
- Every **subject** = a **vertex** in an undirected graph
- An **edge** exists between two subjects if they share **at least one common student**
- Goal: assign **time slots (colors)** so no two adjacent vertices share a color

### Greedy Graph Coloring — Welsh-Powell Heuristic

```
Input:  Graph G = (V, E)
Output: Color map {vertex → color}

1. Sort vertices by degree (descending)        ← Welsh-Powell ordering
2. For each vertex v in order:
       used = {color[u] for u in Adj(v) if u already colored}
       color[v] = smallest integer NOT in used  ← greedy choice
3. Return color map
```

**Time Complexity:** `O(V² + E)` — for each of V vertices we inspect its neighbors.  
**Space Complexity:** `O(V + E)` — adjacency list + color map.

### Why Welsh-Powell?
Sorting by degree means **highly-connected (high-conflict) subjects** are scheduled first, leading to a near-optimal number of time slots.

---

## 🗄️ Database Schema

| Table | Key Columns |
|-------|-------------|
| `subjects` | id, code, name, credits |
| `students` | id, roll_no, name, email |
| `enrollments` | id, student_id → subjects.id, subject_id → subjects.id |
| `timetable_entries` | id, subject_id, slot_number, slot_label, color |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask 3.0, Flask-SQLAlchemy |
| Frontend | Bootstrap 5, Vanilla JS, CSS3 |
| Database | SQLite (via SQLAlchemy ORM) |
| Algorithm | Greedy Graph Coloring (Welsh-Powell) |

---

## 📋 Phase 1 Features (Current)
- [x] Add/delete subjects, students, enrollments
- [x] Greedy graph coloring algorithm with step log
- [x] Timetable generation & display
- [x] Conflict detection API (`/api/conflicts`)
- [x] Load sample data for testing
- [x] Export timetable as CSV
- [x] Print / browser PDF
- [x] Responsive Bootstrap UI with dark sidebar

## 🔜 Phase 2 (Planned)
- [ ] Interactive conflict graph visualization (vis.js)
- [ ] PDF export via server-side rendering
- [ ] Time slot configuration panel
- [ ] Multi-department support
- [ ] Algorithm comparison (Greedy vs Backtracking)

---

## 👨‍💻 Author
DAA Project — B.Tech CSE  
Greedy Graph Coloring for Exam Timetable Scheduling
