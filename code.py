
import streamlit as st
import pandas as pd

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.book_indices = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, index):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.book_indices.append(index)

    def search(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self._collect_indices(node)

    def _collect_indices(self, node):
        indices = []
        if node.is_end:
            indices.extend(node.book_indices)
        for child in node.children.values():
            indices.extend(self._collect_indices(child))
        return indices

class TrieBasedRecommender:
    def __init__(self, books_df):
        self.books_df = books_df
        self.trie = Trie()
        for idx, book in books_df.iterrows():
            # Index titles, authors, genres
            searchable_text = f"{book['title']} {book['authors']} {book['genre']}"
            for word in searchable_text.lower().split():
                self.trie.insert(word, idx)

    def recommend_books(self, search_query='', author='All', genre='All', min_rating=1):
        # Handle empty search queries
        if not search_query.strip():
            recommended_indices = list(range(len(self.books_df)))
        else:
            recommended_indices = self.trie.search(search_query.lower())

        # Collect and filter books
        recommended = [
            self.books_df.iloc[idx].to_dict() for idx in recommended_indices
            if (author == "All" or self.books_df.iloc[idx]['authors'] == author) and
               (genre == "All" or self.books_df.iloc[idx]['genre'] == genre) and
               self.books_df.iloc[idx]['average_rating'] >= min_rating
        ]

        # Sort by rating
        recommended.sort(key=lambda x: x['average_rating'], reverse=True)
        return recommended

# Streamlit UI
st.title("📚 Book Recommendation System")
st.sidebar.header("Search & Filters")

# Load data from CSV file
@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

file_path = "books_DB.csv"  # Replace with your uploaded CSV path
books_df = load_data(file_path)

# Verify required columns exist
required_columns = {"title", "authors", "genre", "average_rating"}
if not required_columns.issubset(books_df.columns):
    st.error(f"The CSV file must contain the following columns: {required_columns}")
    st.stop()

# Initialize recommender
recommender = TrieBasedRecommender(books_df)

# Input fields for filtering
search_query = st.sidebar.text_input("Search by Keywords")
selected_author = st.sidebar.selectbox("Author", options=["All"] + sorted(books_df["authors"].unique().tolist()))
selected_genre = st.sidebar.selectbox("Genre", options=["All"] + sorted(books_df["genre"].unique().tolist()))
selected_rating = st.sidebar.select_slider("Minimum Rating", options=[1, 2, 3, 4, 5], value=1)

# Buttons aligned side-by-side
col1, col2 = st.sidebar.columns(2)
with col1:
    apply = st.button("Apply Filters")
with col2:
    reset = st.button("Reset Filters")

# Reset logic
if reset:
    search_query = ""
    selected_author = "All"
    selected_genre = "All"
    selected_rating = 1

# Get recommendations
if apply or search_query or selected_author != "All" or selected_genre != "All" or selected_rating > 1:
    recommended_books = recommender.recommend_books(
        search_query, 
        selected_author, 
        selected_genre, 
        selected_rating
    )
else:
    # Show all books if no filters are applied
    recommended_books = books_df.to_dict(orient='records')

# Grid/List view toggle
view_toggle = st.radio("View as:", options=["Grid", "List"], horizontal=True)

# Display books
if recommended_books:
    if view_toggle == "Grid":
        cols = st.columns(3)
        for idx, book in enumerate(recommended_books):
            with cols[idx % 3]:
                image_url = book.get('image_url', 'https://via.placeholder.com/150') #default placeholder
                st.image(image_url, width=100)
                st.markdown(f"**{book['title']}**")
                st.text(f"Author: {book['authors']}")
                st.text(f"Genre: {book['genre']}")
                st.text(f"Rating: ⭐ {book['average_rating']}")
    else:
        for book in recommended_books:
            image_url = book.get('image_url', 'https://via.placeholder.com/150') #default placeholder
            st.image(image_url, width=100)
            st.markdown(f"### {book['title']}")
            st.text(f"Author: {book['authors']}")
            st.text(f"Genre: {book['genre']}")
            st.text(f"Rating: ⭐ {book['average_rating']}")
            st.markdown("---")
else:
    st.warning("No books matched your filters!")
