from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import requests
 
app = Flask(__name__)
 
@app.route("/")
def index():
    return render_template("index.html")
 
def chuck():
    '''Return a Chuck Norris joke'''
    url = "https://api.chucknorris.io/jokes/random"
    response = requests.get(url)
    chuck_joke = response.json()["value"]
    return chuck_joke
 
@app.route("/joke")
def joke():
    joke = chuck() 
    return joke
 
if __name__ == "__main__":
    '''scheduler = BackgroundScheduler()
    scheduler.add_job(chuck, "interval", seconds=15)
    scheduler.start()
    '''
    app.run()