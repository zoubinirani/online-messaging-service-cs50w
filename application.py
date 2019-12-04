import os

from flask import Flask, render_template, session, request, flash
from flask_session import Session
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)

app.secret_key = os.urandom(24)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'

socketio = SocketIO(app)

sess = Session()
sess.init_app(app) #configure session

active_usernames = set()
active_channels = set()
saved_messages = dict()

@app.route("/")
def index():
    try:
        print(session['channel'])
        if session['username'] and session['channel']:
            return channel(session['channel'])
        elif session['username']:
            return welcome()
    except:
        return render_template('index.html')

@app.route("/login", methods=["POST"]) 
def login():
    username = request.form.get("username")

    if username in active_usernames:
        flash("That username is taken. Please select another username.")
        return index()
    
    elif len(username) < 3:
        flash("Pick a username with at least 3 characters.")
        return index()

    else:
        active_usernames.add(username)
        session['username'] = username
        return welcome()

@app.route("/go_logout", methods=["POST"]) 
def go_logout():
    active_usernames.remove(session['username'])
    session.clear()
    return index()


@app.route("/create_channel", methods=["POST"]) 
def create_channel():
    create_channel = request.form.get("channel")
    if create_channel in active_channels:
        flash("That channel has already been created. Please select it from the dropdown menu.")
        return welcome()
    
    elif len(create_channel) < 3:
        flash("Pick a channel with at least 3 characters.")
        return welcome()

    else:
        active_channels.add(create_channel)
        session['channel'] = create_channel
        saved_messages[create_channel] = []
        return channel(create_channel)

@app.route("/welcome")
def welcome():
    return render_template("welcome.html", active_channels=active_channels)

@app.route("/goto_channel", methods=["POST"]) 
def goto_channel():
    requested_channel = request.form.get("channel")
    if requested_channel in active_channels:
        session['channel'] = requested_channel
        return channel(requested_channel)
    else:
        flash("That channel has not been created. Please create it first.")
        return welcome()

@app.route("/channel/<string:channel_id>")
def channel(channel_id):
    return render_template("channel.html", channel_id=channel_id)

@socketio.on("connect")
def on_connect(methods=['GET', 'POST']):
    join_room(session['channel'])
    timenow = "  (" + str(datetime.now()) + ")"
    
    #only save 100 messages server-side. We are adding one message so we have to remove the 100th message.
    if len(saved_messages[session['channel']]) >= 100: 
        saved_messages[session['channel']].pop(0)
    
    for message in saved_messages[session['channel']]:
        #do not broadcast. only for recently joined user
        emit('message', {"username":message[0], "msg":message[1], "timenow": message[2]}) 

    #emit message that you have joined
    emit('message', {"username":session['username'], "msg":" has entered!", "timenow": timenow}, broadcast=True, room=session['channel'])
    saved_messages[session['channel']].append([session['username'], " has entered!", timenow])


@socketio.on("disconnect")
def disconnect(methods=['GET', 'POST']):
    timenow = "  (" + str(datetime.now()) + ")"

    #only save 100 messages server-side. We are adding one message so we have to remove the 100th message.
    if len(saved_messages[session['channel']]) >= 100: 
        saved_messages[session['channel']].pop(0)

    emit('message', {"username":session['username'], "msg":" has left!", "timenow": timenow}, broadcast=True, room=session['channel'])
    saved_messages[session['channel']].append([session['username'], " has left!", timenow])

    leave_room(session['channel'])
    session['channel'] = None

@app.route("/leave_channel", methods=["POST"]) 
def leave_channel():
    return welcome()

@socketio.on("message_recieve")
def message_recieve(message, methods=['GET', 'POST']):
    timenow = " - " + str(datetime.now())
    
    emit('message', {"username":session['username'], "msg":message['message'], "timenow": timenow}, broadcast=True, room=session['channel'])
    
    #only save 100 messages server-side. We are adding one message so we have to remove the 100th message.
    if len(saved_messages[session['channel']]) >= 100: 
        saved_messages[session['channel']].pop(0)
    
    #Save new message
    saved_messages[session['channel']].append([session['username'], message['message'], timenow])



if __name__ == "__main__":
    socketio.run(app)
