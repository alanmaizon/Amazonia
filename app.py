from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import json

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'Replace me with a real secret key for production use'
socketio = SocketIO(app)

# Register the enumerate function as a Jinja2 filter
@app.template_filter('enumerate')
def do_enumerate(iterable):
    return enumerate(iterable)

# A dictionary to store logged-in users and their status
user_datastore = {}

# A dictionary to store posts
posts = {}
post_id_counter = 1

# In-memory data store for previous chat messages
chat_log = {}

# Home route to load previous messages for the public room
@app.route('/')
def home():
    if 'username' in session and session['username'] not in user_datastore:
        return redirect(url_for('logout'))
    
    # Retrieve previous messages for the public room
    previous_messages = chat_log.get('public', [])
    previous_messages_json = json.dumps(previous_messages)
    
    return render_template('home.html', logged_in_users=user_datastore, previous_messages=previous_messages_json)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        user_datastore[username] = 'online'
        return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    username = session.pop('username', None)
    user_datastore.pop(username, None)
    return redirect(url_for('home'))


@app.route('/status', methods=['POST'])
def set_status():
    if 'username' not in session:
        return redirect(url_for('login'))
    status = request.form['status']
    username = session['username']
    user_datastore[username] = status
    return redirect(url_for('home'))


@app.route('/posts', methods=['GET'])
def view_posts():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('posts.html', posts=posts)


@app.route('/posts/new', methods=['POST'])
def create_post():
    global post_id_counter
    if 'username' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    post_id = post_id_counter
    posts[post_id] = {
        "username": session['username'],
        "content": content,
        "comments": []
    }
    post_id_counter += 1
    return redirect(url_for('view_posts'))


@app.route('/posts/<int:post_id>', methods=['GET'])
def view_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.get(post_id)
    if not post:
        return redirect(url_for('view_posts'))
    return render_template('post_detail.html', post=post, post_id=post_id)


@app.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.get(post_id)
    if not post or post['username'] != session['username']:
        return redirect(url_for('view_posts'))
    if request.method == 'POST':
        post['content'] = request.form['content']
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('edit_post.html', post=post, post_id=post_id)


@app.route('/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.get(post_id)
    if not post or post['username'] != session['username']:
        return redirect(url_for('view_posts'))
    posts.pop(post_id)
    return redirect(url_for('view_posts'))


@app.route('/posts/<int:post_id>/comment/<int:comment_id>/vote', methods=['POST'])
def vote_comment(post_id, comment_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.get(post_id)
    if not post or comment_id >= len(post['comments']):
        return redirect(url_for('view_post', post_id=post_id))
    username = session['username']
    comment = post['comments'][comment_id]
    if username in comment.get('voters', []):
        return redirect(url_for('view_post', post_id=post_id))
    vote_type = request.form['vote']
    if vote_type == 'upvote':
        comment['votes'] += 1
    elif vote_type == 'downvote':
        comment['votes'] -= 1
    if 'voters' not in comment:
        comment['voters'] = []
    comment['voters'].append(username)
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    post = posts.get(post_id)
    if not post:
        return redirect(url_for('view_posts'))
    comment = request.form['comment']
    post['comments'].append({
        "username": session['username'],
        "comment": comment,
        "votes": 0
    })
    return redirect(url_for('view_post', post_id=post_id))


#Chat room
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('chat.html', username=session['username'])

# Handle messages in the public chat room
@socketio.on('send_message')
def handle_send_message(data):
    username = session.get('username')
    message = data['message']
    
    # Store the message in the public chat log
    public_room = 'public'
    if public_room not in chat_log:
        chat_log[public_room] = []
    chat_log[public_room].append({'username': username, 'message': message})
    
    emit('receive_message', {'username': username, 'message': message}, broadcast=True)

# Handle client connection
@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        emit('user_connected', {'username': username}, broadcast=True)

# Handle client disconnection
@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        emit('user_disconnected', {'username': username}, broadcast=True)

@app.route('/chat/<recipient>')
def private_chat(recipient):
    if 'username' not in session:
        return redirect(url_for('home'))
    username = session['username']
    room = f"{min(username, recipient)}_{max(username, recipient)}"  # Unique room identifier

    # Convert previous messages to JSON to be sent to the client
    previous_messages = chat_log.get(room, [])
    previous_messages_json = json.dumps(previous_messages)
    
    return render_template('private_chat.html', username=username, recipient=recipient, room=room, previous_messages=previous_messages_json)

# Handle messages in private chat rooms
@socketio.on('send_private_message')
def handle_send_private_message(data):
    username = session.get('username')
    room = data['room']
    message = data['message']
    
    # Store the message in the chat log
    if room not in chat_log:
        chat_log[room] = []
    chat_log[room].append({'username': username, 'message': message})
    
    emit('receive_private_message', {'username': username, 'message': message}, room=room)

# Handle joining a private room
@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    join_room(room)
    emit('user_joined_room', {'username': session['username']}, room=room)

# Handle leaving a private room
@socketio.on('leave_room')
def handle_leave_room(data):
    room = data['room']
    leave_room(room)
    emit('user_left_room', {'username': session['username']}, room=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)
