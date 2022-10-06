import streamlit as st
import pandas as pd

from surprise.prediction_algorithms import SVD
from surprise import Reader, Dataset

# Goal: have person be able to select songs from list(top 10k most listened to songs)
# Add these selections to a list
# Feed this list to the model
# Get the outputs of the model(top 5 recommended songs)
# Convert these music numbers back to artist/song via the df
# Display these songs
# extra credit: integrate spotipy to play song demos

top_songs = pd.read_csv("./data/song_table10k.csv")
top_songs.drop(columns=['Unnamed: 0'], inplace=True)

original_data = pd.read_csv('./data/rated_listens_10k.csv')
original_data.drop(columns=['Unnamed: 0'], inplace=True)


# Use session state to save lists
if 'rating_list_use' not in st.session_state:
    st.session_state['rating_list_use'] = []

if 'rating_list_show' not in st.session_state:
    st.session_state['rating_list_show'] = []

if 's_id_list' not in st.session_state:
    st.session_state['s_id_list'] = []

if 'top5_s_id' not in st.session_state:
    st.session_state['top5_s_id'] = []



# Instructions
st.write("# MITCHMUSIC")
st.write("### Instructions")
st.write("#### Select a song and then give it a rating between 1-10.")
st.write("#### Add multiple songs to your list to help improve recommendations.")
st.write("#### Once you have some songs rated, hit the \"RECOMMEND SONGS\" button.")
st.write("#### The computer will calculate your potential top songs.")
st.write("#### Your top 10 song recommendations will appear, sorted by the predicted score.")

userID = 'ishoulddothisbeforethenightbefore'




artist = st.selectbox(label='ARTIST NAME', options=top_songs['artist_name'].unique())

temp_song_df = top_songs.loc[top_songs['artist_name']==artist]

song = st.selectbox(label='SONG NAME', options=temp_song_df['track_name'])

song_id = temp_song_df.loc[temp_song_df['track_name'] == song, 'song_no'].iloc[0]

rating = st.slider(label='RATING', min_value=1, max_value=10)

if st.button(label='ADD SONG TO SONG LIST'):
    input_row_use = {'user_name':userID, 'song_no':song_id, 'rating':rating}
    st.session_state['rating_list_use'].append(input_row_use)
    input_row_show = {'artist':artist, 'song':song, 'rating':rating}
    st.session_state['rating_list_show'].append(input_row_show)
    st.session_state['s_id_list'].append(song_id)


if st.button(label='RESET'):
    st.session_state['rating_list_use'] = []
    st.session_state['rating_list_show'] = []
    st.session_state['s_id_list'] = []
    st.session_state['recommended_song_df'] = pd.DataFrame()


st.write('Current song list:')
st.write(st.session_state['rating_list_show'])


if st.button(label='RECOMMEND SONGS'):
    # st.write(st.session_state['rating_list_use'])
    st.write('Recommender progress:')

    df_temp = pd.DataFrame.from_dict(st.session_state['rating_list_use'])
    # st.write(df_temp)

    new_ratings_df = pd.concat([original_data, df_temp], axis=0)
    # st.write('Concat success')

    # new_ratings_df = original_data.concat(st.session_state['rating_list_use'])
    # st.write(new_ratings_df.tail())

    st.write('Dataset building')
    reader = Reader(rating_scale=(1,10))
    new_data = Dataset.load_from_df(new_ratings_df, reader)
    

    # train a model using new df w/ optimal hyperparameters
    st.write('Recalculating SVD')
    model = SVD(n_factors= 150, reg_all=0.1)
    model.fit(new_data.build_full_trainset())
    st.write('Model Trained')

    recommended_song_list = []
    for s_id in original_data['song_no'].unique():
        if s_id not in st.session_state['s_id_list']:
            recommended_song_list.append( (s_id, model.predict(userID, s_id)[3]))
    # st.write('recommended list created')

    # order the predictions from highest to lowest rated
    recommended_ranked_song_list = []
    recommended_ranked_song_list = sorted(recommended_song_list, key=lambda x:x[1], reverse=True)
    # st.write('recommended list sorted')

    # get top songs
    # list of tuples(song_no, rating)

    top5 = recommended_ranked_song_list[:10]
    st.session_state['top5_s_id'] = list(zip(*top5))[0]
    top5_prob = list(zip(*top5))[1]

    # modify df, show top songs
    top_song_df = top_songs[top_songs['song_no'].isin(st.session_state['top5_s_id'])]

    top_song_df['likely_rating'] = top_song_df['song_no'].map(dict(top5))

    top_song_df.sort_values(by=['likely_rating'], ascending=False, inplace=True)
    top_song_df.set_index('likely_rating', inplace=True)
    top_song_df.drop(columns=['song_no'], inplace=True)

    st.write('RECOMMENDED SONGS:')
    st.write(top_song_df)

