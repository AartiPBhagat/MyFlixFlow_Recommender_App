import streamlit as st
import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import random

#-----------------------------------------------------------------------
pd.set_option('display.max_colwidth', None)

# Set the theme image using st.set_page_config()
st.set_page_config(
    page_title="My Flix Flow",
    page_icon="unsplash.png",  # Replace with the URL of your theme image
    layout="wide"  # You can also set the layout here
)

st.title("My Flix Flow")

st.header("Most Popular Movies.", divider='rainbow')

# movie data
movies_df = pd.read_csv('data/movies.csv')
ratings_df = pd.read_csv('data/ratings.csv')

#----------------------------------------------------------------------------------------------
#n = st.number_input("How many movies?", value=None, placeholder="Top n movies...")

# popularity
def top_n_pop_based(n):
    
    test_df = ratings_df.groupby('movieId').agg({'rating':'mean','userId':'count'})

    # normalize rating
    test_df['rating_normalized'] = (test_df['rating'] - test_df['rating'].min()) / (test_df['rating'].max() - test_df['rating'].min())

    # normalize count
    test_df['count_normalized'] = (test_df['userId'] - test_df['userId'].min()) / (test_df['userId'].max() - test_df['userId'].min())

    # decide weight of feature
    rating_weight = 0.75
    count_weight = 0.25

    # normalized & weighted rating & count
    test_df['rating_weighted'] = test_df['rating_normalized'] * rating_weight
    test_df['count_weighted'] = test_df['count_normalized'] * count_weight

    # final rating - decides popularity
    test_df['final_rating'] = test_df['rating_weighted'] + test_df['count_weighted']

    # final test_df
    test_df = test_df.sort_values('final_rating',ascending=False).reset_index()

    # get movie title with highest final rating
    top_n = movies_df[['movieId','title','genres']].merge(test_df[['movieId']], how='right')

    # top_n is : normalizes data and different weight(2)
    top_n_movies = top_n[['title','genres']].head(10)
    
    # Rename the 'title' and 'genres' columns
    top_n_movies = top_n_movies.rename(columns={'title': 'Movie', 'genres': 'Genres'})

    return top_n_movies


# display top 10 movies
top_movies = top_n_pop_based(10)
st.dataframe(top_movies, hide_index=True)

#----------------------------------------------------------------------------------------------

# item based

st.header("Select any Random Movie", divider='rainbow')

#list of random movies
random_movies = random.sample(list(movies_df['title']), 5)

selected_movie = st.selectbox("Select a Movie", random_movies)

# Get the movieId of the selected movie
selected_movie_id = movies_df[movies_df['title'] == selected_movie]['movieId'].values[0]
st.write(selected_movie_id)

st.write("Because you selcted this movie you may also like these movies...")

user_movie_matrix = pd.pivot_table(data=ratings_df,
                                  values='rating',
                                  index='userId',
                                  columns='movieId',
                                  fill_value=0)

movie_cosines_matrix = pd.DataFrame(cosine_similarity(user_movie_matrix.T),
                                    columns=user_movie_matrix.columns,
                                    index=user_movie_matrix.columns)
             
def top_n_item_based(movieId, n):
    # Create a DataFrame using the values from 'movies_cosines_matrix' for the 'movieId'
    cosines_df = pd.DataFrame(movie_cosines_matrix[movieId])

    # Remove the row with the index given movieId
    cosines_df = cosines_df[cosines_df.index != movieId]

    # Sort the 'cosines_df' by the column 'movieId' column in descending order.
    cosines_df = cosines_df.sort_values(by=movieId, ascending=False)

    # Find out the number of users rated both The given movieId and the other movie
    no_of_users_rated_both_movies = [sum((user_movie_matrix[movieId] > 0) & (user_movie_matrix[m_Id] > 0)) for m_Id in cosines_df.index]

    # Create a column for the number of users who rated the movieId and the other movie
    cosines_df['no_users_rated_both_movies'] = no_of_users_rated_both_movies

    # Remove recommendations that have less than 10 users who rated both movies.
    cosines_df = cosines_df[cosines_df["no_users_rated_both_movies"] > 10]

    # columns for movie details
    movie_info_columns = ['movieId','title','genres']

    # Get the names for the related movies
    top_n_movie = (cosines_df
                          .head(n)   # this would give us the top n book-recommendations
                          .reset_index()
                          .merge(movies_df.drop_duplicates(subset='movieId'),
                                  on='movieId',
                                  how='left')
                          [movie_info_columns + [movieId,'no_users_rated_both_movies']]
                          )
    top_n_movie = top_n_movie[['movieId','title','genres']].head(n)
    
    return top_n_movie

recommendations = top_n_item_based(selected_movie_id, n=10)

st.dataframe(recommendations)

#---------------------------------------------------------------------------------------------

# user-based recommender



