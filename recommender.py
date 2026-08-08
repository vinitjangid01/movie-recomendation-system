import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

_df = None
_similarity = None
_vectorizer = None

def load_data():
    global _df
    if _df is not None:
        return _df
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "movies.csv")
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True)
    df["tags"] = (
        df["genres"].str.lower().str.replace(",", " ") + " " +
        df["language"].str.lower() + " " +
        df["director"].str.lower() + " " +
        df["cast"].str.lower() + " " +
        df["overview"].str.lower()
    )
    df = df.reset_index(drop=True)
    _df = df
    return df

def build_model(df):
    global _similarity, _vectorizer
    if _similarity is not None:
        return _similarity
    _vectorizer = TfidfVectorizer(max_features=8000, stop_words="english")
    vectors = _vectorizer.fit_transform(df["tags"])
    _similarity = cosine_similarity(vectors)
    return _similarity

def get_genres(df):
    all_genres = set()
    for g in df["genres"].dropna():
        for genre in g.split(","):
            genre = genre.strip()
            if genre:
                all_genres.add(genre)
    return sorted(all_genres)

def get_languages(df):
    return sorted(df["language"].dropna().unique().tolist())

def filter_movies(df, genre=None, language=None, search_query=None):
    filtered = df.copy()
    if language and language != "All":
        filtered = filtered[filtered["language"].str.lower() == language.lower()]
    if genre and genre != "All":
        filtered = filtered[filtered["genres"].str.contains(genre, case=False, na=False)]
    if search_query:
        filtered = filtered[filtered["title"].str.contains(search_query, case=False, na=False)]
    return filtered

def recommend(movie_title, df, similarity, top_n=9, genre_filter=None, lang_filter=None):
    movie_title_lower = movie_title.strip().lower()
    titles_lower = df["title"].str.lower()
    matches = titles_lower[titles_lower.str.contains(movie_title_lower, na=False, regex=False)]
    if matches.empty:
        return []
    idx = matches.index[0]
    scores = list(enumerate(similarity[idx]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    results = []
    for i, score in scores:
        if i == idx or score < 0.01:
            continue
        row = df.iloc[i]
        if lang_filter and lang_filter != "All" and row["language"].lower() != lang_filter.lower():
            continue
        if genre_filter and genre_filter != "All" and genre_filter.lower() not in row["genres"].lower():
            continue
        results.append({
            "title": row["title"],
            "genres": row["genres"],
            "language": row["language"],
            "director": row["director"],
            "cast": row["cast"],
            "year": row.get("year", ""),
            "rating": row.get("rating", ""),
            "overview": row.get("overview", ""),
            "score": round(float(score) * 100, 1)
        })
        if len(results) >= top_n:
            break
    return results

def get_movie_details(title, df):
    matches = df[df["title"].str.lower() == title.strip().lower()]
    if matches.empty:
        matches = df[df["title"].str.contains(title.strip(), case=False, na=False, regex=False)]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return {
        "title": row["title"],
        "genres": row["genres"],
        "language": row["language"],
        "director": row["director"],
        "cast": row["cast"],
        "year": row.get("year", "N/A"),
        "rating": row.get("rating", "N/A"),
        "overview": row.get("overview", "No overview available.")
    }
