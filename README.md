CineMatch — Movie Recommendation System:
A desktop-based Movie Recommendation System built using Python and Machine Learning.
This application suggests similar movies based on user input using NLP techniques and cosine similarity.

Overview:
CineMatch is designed to help users discover movies efficiently by analyzing content similarity.
It provides an interactive graphical interface where users can search movies, apply filters, and explore recommendations instantly.

Key Features:
-Smart movie search with autocomplete
-Recommendation engine using cosine similarity Filters by genre and language
-Displays rating, year, and match score
-NLP-based similarity model
-Clean dark-themed GUI built with Tkinter

Tech Stack:

* **Python** — Core programming
* **Pandas** — Data handling
* **Scikit-learn** — ML model (cosine similarity)
* **Tkinter** — GUI development
* **NLP techniques** — Text processing & feature extraction

How to Run:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

Project Structure:

```
MovieRecommendation/
│
├── main.py             # Main GUI application
├── recommender.py      # Recommendation logic
├── movies.csv          # Dataset
├── requirements.txt    # Dependencies
└── README.md
```

What I Learned:

* Building GUI applications using Tkinter
* Implementing recommendation systems
* Applying NLP techniques on real datasets
* Structuring a complete end-to-end project

Author:
Naveen Singhal
