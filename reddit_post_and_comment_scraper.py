import streamlit as st
import praw
import pandas as pd
import time

# Initialize Reddit API
reddit = praw.Reddit(
    client_id="fX_9j6sKjm-wKW_CGN3BKQ",
    client_secret="HIF_Mlm1ET3fqaswKN21Iy4kvXq9Wg",
    user_agent="MyCrawlerBot/1.0 (by u/Ok_Inspector98)",
)

# Session state to track stop request
if "stop_fetching" not in st.session_state:
    st.session_state.stop_fetching = False

def fetch_posts(subreddit_name, query, limit, comment_limit):
    """Fetch posts based on a search query and their top comments."""
    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.search(query, limit=limit)
    post_data = []
    
    progress_bar = st.progress(0)

    for count, post in enumerate(posts, 1):
        if st.session_state.stop_fetching:  
            st.warning("Fetching stopped by user.")
            break  # Exit the loop if the user clicks stop
        
        try:
            # Fetch top-level comments
            post.comments.replace_more(limit=2)
            comments = [c.body for c in post.comments.list()[:comment_limit] if hasattr(c, "body")]
            
            post_data.append({
                "title": post.title,
                "upvotes": post.score,
                "num_comments": post.num_comments,
                "comments": comments
            })
            
            progress_bar.progress(count / limit)  # Update progress bar
            time.sleep(1)  # Avoid hitting API rate limits
        
        except Exception as e:
            st.warning(f"Error processing post: {post.title} | {e}")
    
    progress_bar.empty()
    if not st.session_state.stop_fetching:
        st.success("Fetching complete!")
    
    return post_data

def rank_posts(post_data):
    """Rank posts based on upvotes and comments."""
    for post in post_data:
        post["score"] = post["upvotes"] * 2 + post["num_comments"]
    
    return sorted(post_data, key=lambda x: x["score"], reverse=True)

# Streamlit UI
st.title("🔎 Reddit Post Search Scraper")

# User Inputs
subreddit_input = st.text_input("Enter subreddit name", "Bolehland")
query_input = st.text_input("Enter search query", "muslim")
post_limit = st.number_input("Number of posts to pull", min_value=1, max_value=1000, value=10)
comment_limit = st.number_input("Number of comments per post", min_value=1, max_value=1000, value=5)

# Buttons
col1, col2 = st.columns(2)
with col1:
    fetch_button = st.button("Pull Posts")
with col2:
    stop_button = st.button("Stop Pulling")

if stop_button:
    st.session_state.stop_fetching = True  # Set stop flag to True
    st.warning("Stopping pull...")

if fetch_button:
    st.session_state.stop_fetching = False  # Reset stop flag
    st.info(f"Fetching {post_limit} posts from r/{subreddit_input} for '{query_input}'...")
    
    posts = fetch_posts(subreddit_input, query_input, post_limit, comment_limit)
    
    if posts:
        ranked_posts = rank_posts(posts)
        df = pd.DataFrame(ranked_posts)
        
        # Display DataFrame
        st.dataframe(df)
    else:
        st.error("No posts found. Try again later.")
