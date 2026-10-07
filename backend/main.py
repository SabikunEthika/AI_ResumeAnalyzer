from fastapi import FastAPI #importing FastAPI

app = FastAPI() #we can think app as our entire backend application.In this line We are creating FastAPI application

@app.get("/") # /->root url (http://localhost:8000/). this line means when someone sends a get request to the root url run the function below 
def home(): #this is the python function that runs when somebody visits /
    return {"message": "AI Resume Analyzer Backend is running!"} #a json message from backend to frontend