import tkinter as tk
from tkinter import messagebox, scrolledtext
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Import necessary packages
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize lemmatizer and stop words
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Load your datasets
data1 = pd.read_csv(r"C:\Users\HP\Desktop\mentalhealth.csv")
data1.drop('Question_ID', axis=1, inplace=True)
data2 = pd.read_csv(r'C:\Users\HP\Desktop\train.csv')
data2.rename(columns={'Context': 'Questions', 'Response': 'Answers'}, inplace=True)
data3 = pd.read_csv(r'C:\Users\HP\Downloads\intents(2).csv')
data3.rename(columns={'pattern': 'Questions', 'response': 'Answers'}, inplace=True)
data4 = pd.read_csv(r'C:\Users\HP\Desktop\merged_file_9.csv')
data4.rename(columns={'pattern': 'Questions', 'response': 'Answers'}, inplace=True)

# Merge datasets
merged_df = pd.concat([data1, data2, data3], ignore_index=True)
corpus = merged_df['Questions'].tolist()
replies = merged_df['Answers'].tolist()

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]
    reconstructed = ' '.join(tokens)
    return reconstructed

# Preprocess data
corpus_tokens = []
for sentence in corpus:
    tokens = word_tokenize(sentence.lower())
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]
    reconstructed_text = ' '.join(tokens)
    corpus_tokens.append(reconstructed_text)

# Vectorize data
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus_tokens)

# Function to get the most similar question index
def get_most_similar_question(user_question):
    preprocessed_user_question=preprocess_text(user_question)
    user_tfidf = vectorizer.transform([preprocessed_user_question])
    cosine_similarities = cosine_similarity(user_tfidf, X)
    similar_question_index = cosine_similarities.argmax()
    return similar_question_index

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('chatbot.db')
cursor = conn.cursor()

# Create a table for users if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Commit changes to the database
conn.commit()

# Function to display the chatbot screen
def chatbot_screen(username):
    # Create the main chatbot window
    chatbot_window = tk.Tk()
    chatbot_window.title(f"Chatbot - Logged in as {username}")
    
    # Set background color and window size
    chatbot_window.configure(bg="lightblue")
    chatbot_window.geometry('600x500')
    
    # Create chat display (scrolled text widget)
    chat_display = scrolledtext.ScrolledText(chatbot_window, wrap=tk.WORD, width=60, height=20, font=("Comic Sans MS", 10))
    chat_display.pack(padx=10, pady=10)
    
    # Initial message from the chatbot
    chat_display.insert(tk.END, "Chatbot: Hey! How can I help you today?\n")
    
    # User input entry widget
    user_input = tk.Entry(chatbot_window, width=60, font=("Comic Sans MS", 10))
    user_input.pack(pady=10, side=tk.LEFT)
    
    # Define a function to handle user input
    def handle_user_input(event=None):
        user_question = user_input.get()
        
        # Clear the entry field
        user_input.delete(0, tk.END)
        
        # Display the user's question in the chat display
        chat_display.insert(tk.END, f"User: {user_question}\n")
        
        # Check for exit conditions
        if user_question.lower() in ['bye', 'exit', 'quit']:
            chat_display.insert(tk.END, "Chatbot: Goodbye! Take care.\n")
            chatbot_window.quit()  # Quit the application
            return
        
        # Get the most similar question index
        similar_question_index = get_most_similar_question(user_question)
        chatbot_response = merged_df['Answers'][similar_question_index]
        
        # Display the chatbot's response in the chat display
        chat_display.insert(tk.END, f"Chatbot: {chatbot_response}\n")
        
        # Scroll to the bottom of the chat display
        chat_display.see(tk.END)
    
    # Bind the function to the Return key
    user_input.bind("<Return>", handle_user_input)
    
    # Send button
    send_button = tk.Button(chatbot_window, text="Send", command=handle_user_input, bg="lightgreen", font=("Comic Sans MS", 10))
    send_button.pack(pady=10, side=tk.LEFT)
    
    # Exit button
    def exit_chat():
        chatbot_window.quit()
    exit_button = tk.Button(chatbot_window, text="Exit", command=exit_chat, bg="lightcoral", font=("Comic Sans MS", 10))
    exit_button.pack(pady=10, side=tk.LEFT)
    
    # Start the main loop
    chatbot_window.mainloop()

# Function to display the login screen
def login_screen():
    def login():
        # Get entered username and password
        username = username_entry.get()
        password = password_entry.get()
        
        # Check the database for the user
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        if user:
            # Login successful, close the login window and open the chatbot screen
            login_window.destroy()
            chatbot_screen(username)
        else:
            # Login failed, show an error message
            messagebox.showerror("Error", "Invalid username or password")
    
    def register():
        # Destroy login window
        login_window.destroy()
        
        # Create the register window
        register_window = tk.Tk()
        register_window.title("Register New User")
        
        # Set background color
        register_window.configure(bg="lightblue")
        
        # Create labels and entry fields for username and password
        tk.Label(register_window, text="Username:", font=("Comic Sans MS", 10)).pack(pady=5)
        new_username_entry = tk.Entry(register_window, font=("Comic Sans MS", 10))
        new_username_entry.pack(pady=5)
        
        tk.Label(register_window, text="Password:", font=("Comic Sans MS", 10)).pack(pady=5)
        new_password_entry = tk.Entry(register_window, show="*", font=("Comic Sans MS", 10))
        new_password_entry.pack(pady=5)
        
        # Function to add new user to the database
        def add_new_user():
            new_username = new_username_entry.get()
            new_password = new_password_entry.get()
            
            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = ?", (new_username,))
            if cursor.fetchone():
                messagebox.showerror("Error", "Username already exists")
                return
            
            # Insert new user into the database
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, new_password))
            conn.commit()
            
            messagebox.showinfo("Success", "Registration successful")
            register_window.destroy()  # Close register window after successful registration
            login_screen()  # Redirect to login screen
        
        # Create register button
        tk.Button(register_window, text="Register", command=add_new_user, bg="lightgreen", font=("Comic Sans MS", 10), bd=2, relief=tk.GROOVE).pack(pady=5)
        
        # Start the register window main loop
        register_window.mainloop()
    
    # Create the login window
    login_window = tk.Tk()
    login_window.title("Login")
    
    # Set background color
    login_window.configure(bg="lightblue")
    
    # Create labels and entry fields for username and password
    tk.Label(login_window, text="Username:", font=("Comic Sans MS", 10)).pack(pady=5)
    username_entry = tk.Entry(login_window, font=("Comic Sans MS", 10))
    username_entry.pack(pady=5)
    
    tk.Label(login_window, text="Password:", font=("Comic Sans MS", 10)).pack(pady=5)
    password_entry = tk.Entry(login_window, show="*", font=("Comic Sans MS", 10))
    password_entry.pack(pady=5)
    
    # Create login and register buttons
    tk.Button(login_window, text="Login", command=login, bg="lightgreen", font=("Comic Sans MS", 10), bd=2, relief=tk.GROOVE).pack(pady=5)
    tk.Button(login_window, text="Register as New User", command=register, bg="lightcoral", font=("Comic Sans MS", 10), bd=2, relief=tk.GROOVE).pack(pady=5)
    
    # Start the login window main loop
    login_window.mainloop()

# Start the application
if name == "main":
    login_screen()