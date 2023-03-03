import streamlit as st
import openai
st.title("IA DE LA COMMUNAUTE DES REFERENTS")
st.sidebar.header("Instructions")
st.sidebar.info('Saisissez votre question et appuyez sur ENTREE')
model_engine = "text-davinci-003"
openai.api_key = "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"


def ChatGPT(user_query):
    completion = openai.Completion.create(
                                  engine = model_engine,
                                  prompt = user_query,
                                  max_tokens = 1024,
                                  n = 1,
                                  temperature = 0.5,
                                      )
    response = completion.choices[0].text
    return response
    
    
   
user_query = st.text_input("Posez votre question dans la base de connaissance CGI-Référents-2023", "")
if user_query != ":q" or user_query != "":        response = ChatGPT(user_query)
st.write(f"{response}")
