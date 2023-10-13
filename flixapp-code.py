import streamlit as st
import pandas as pd
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import random

#-----------------------------------------------------------------------

# movie data
top_movies = pd.read_csv('top_movies.csv')
movies_df = pd.read_csv('data/movies.csv')
ratings_df = pd.read_csv('data/ratings.csv')

#----------------------------------------------------------------------------------------------
# popularity
def top_n_pop_based(n=10):
    
    # top_n is : normalizes data and different weight(2)
    top_n_movies = top_movies[['title','genres']].head(n)
    
    # Rename the 'title' and 'genres' columns
    top_n_movies = top_n_movies.rename(columns={'title': 'Movie', 'genres': 'Genres'})

    return top_n_movies

#----------------------------------------------------------------------------------------------
# item based
#----------------------------------------------------------------------------------------------

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
    print(cosines_df)

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
    top_n_movie = top_n_movie[['title','genres','no_users_rated_both_movies']]
    
    top_n_movie = top_n_movie.rename(columns={'title': 'Movie', 'genres': 'Genres','no_users_rated_both_movies':'Reviews'})
    
    top_n_movie = top_n_movie.sort_values(by='Reviews',ascending=False)
    
    return top_n_movie

#---------------------------------------------------------------------------------------------
# user-based recommender
#---------------------------------------------------------------------------------------------

#mymodel = pickle.load(open('algo-user-based.pickle', 'rb'))


#----------------------------------------------------------------------------------------------
# recommender app
#----------------------------------------------------------------------------------------------

pd.set_option('display.max_colwidth', None)


st.set_page_config(
    page_title="Flix Flow",
    page_icon="unsplash.png",  # Replace with the URL of your theme image
    layout="wide"  # You can also set the layout here
)

st.title("My Flix Flow")


#----------------------Popular on Flix Flow------------------------------------
st.header("Most Popular Movies.", divider='rainbow')

#n = st.number_input("How many movies?", value=None, placeholder="Top n movies...")

# display top 10 movies
top_movies = top_n_pop_based(10)
st.dataframe(top_movies, hide_index=True)

#----------------------------Similar Movies------------------------------------
st.header("Select Your Choice Of Movie", divider='rainbow')

# remove cache-----------------------------------------------------------------
#@st.cache_data
#def my_random(movies_df,n=5,state=142):
    #list of random movies
#    random_movies = random.sample(list(movies_df['title']), 5)
#    return random_movies

#selected_movie = st.selectbox("Please make a choise", my_random(movies_df))

# Get the movieId of the selected movie
#selected_movie_id = movies_df[movies_df['title'] == selected_movie]['movieId'].values[0]
#st.write(selected_movie_id)

#st.write("Because you selcted this movie you may also like these movies...")

#recommendations = top_n_item_based(selected_movie_id, n=10)

#st.dataframe(recommendations)
#-------------------------------------------------------------------------------


# Define the 'my_random' function
@st.cache_data
def my_random(movies_df, n=5, state=142):
    random_movies = random.sample(list(movies_df['title']), n)
    return random_movies


if not st.button("Get Another Movie"):
    # Get the initial random movie
    random_movies = my_random(movies_df)
    selected_movie = st.selectbox("Please make a choice", random_movies)
else:   
    random_movies = my_random(movies_df,state=random.randint(1, 142))
    selected_movie = st.selectbox("Please make a choice", random_movies)

# Get the movieId of the selected movie
selected_movie_id = movies_df[movies_df['title'] == selected_movie]['movieId'].values[0]
#st.write(selected_movie_id, selected_movie)

recommendations = top_n_item_based(selected_movie_id, n=10)

if recommendations.empty:
    st.write("Oops! It looks like there aren't any highly recommended movies available for your selection at the moment. Feel free to explore more options or check back later for fresh recommendations!")
else:
    st.write(f"Great choice!  <span style='color:red; font-weight:bold'>{selected_movie}</span> And... here are some handpicked gems you might enjoy...", unsafe_allow_html=True)
    st.dataframe(recommendations,hide_index=True)
    
#------------------------------------------------------------------------------
#-----------------------------------------------------------------------------