# Rushil Shah's personal projects

## Vini — RAG personal chatbot

Vini is this chatbot. Rushil Shah built it as a retrieval-augmented generation assistant that
answers questions about him.

Architecture: **FastAPI** (Python) for the core logic, **Cohere** `embed-v4.0` for text
embeddings, **MongoDB Atlas Vector Search** as the vector store, and **Grok** as the LLM. Notes
about Rushil are chunked, embedded, and upserted into MongoDB; at query time the user's question is
embedded and matched against those vectors with cosine similarity, and the closest chunks are fed
to the LLM as grounding context alongside an always-on profile. Answers stream back token by token
over Server-Sent Events, and per-session conversation history is kept in MongoDB so follow-up
questions stay in context.

Rushil wrote it up here:
https://medium.com/@rushil1999.dev/vini-a-retrieval-augmented-generation-personal-chatbot-7b90635b595e

## Glide — real-time streaming LLM chat backend

Glide is a real-time AI chatbot backend using HTTP streaming to deliver continuous token-by-token
responses from an LLM. Rushil focused on efficient data flow and server optimization, reducing
latency and improving scalability under concurrent user load, with Redis caching in front.

Glide runs inference on **Groq**, chosen for its low time-to-first-token, which is what makes the
streaming feel instant. Note the distinction from Vini: Glide uses Groq (the inference provider),
while Vini uses Grok (xAI's model).

Stack: FastAPI, Redis, Groq, SSE / HTTP streaming. Code:
https://github.com/rushil1999/glide-backend

## Picture-To-Product — CNN image classification

An image classification project using a Convolutional Neural Network to classify products from
photographs, built during Rushil's master's at San Jose State University. Beyond training the
model, he constructed the data pipeline and API integration that passes classified product data
through to the product search service — the goal was letting users search by image instead of
keywords. Stack: Python, CNNs, hyperparameter tuning, Node.js, React.

## User Authentication Module — open-source React components

Rushil developed and released open-source React components that let developers drop Login, Signup,
and Protected-URL functionality into any project, cutting that setup work by 20-25%. He used the
`useContext` hook to solve the problem of retaining authentication state between parent and child
components. Code: https://github.com/rushil1999/user-authentication

## Buffalo After Sunset — crime data analysis

A machine learning analysis of crime data from Buffalo, New York, using classification and
regression on a dataset of crimes recorded across the city over several years. The aim was to
surface patterns for residents and city authorities. Stack: traditional ML, classification,
regression. Code: https://github.com/rushil1999/255-Buffalo-After-Sunset
