# Fluffy Parakeet

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Debugging and Known Issues](#debugging-and-known-issues)
- [Future Enhancements](#future-enhancements)

## Introduction

This Flask Chat Application provides a real-time chat platform with features including public chat rooms, private messaging, post creation, and status updates. The application leverages Flask-SocketIO for real-time communication.

## Features

- **Real-time Public Chat:** Users can participate in a public chat room.
- **Private Messaging:** Users can initiate private chats with other logged-in users.
- **Post Creation:** Users can create posts and comment on others' posts.
- **Status Updates:** Users can set and update their status, which is visible to other users.
- **User Management:** Simple login system using sessions to track users.

## Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/alanmaizon/fluffyparakeet.git
    cd flask-chat-app
    ```

2. **Create and Activate a Virtual Environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    Ensure the `requirements.txt` includes the necessary packages:

    ```
    Flask==2.0.2
    Flask-SocketIO==5.1.1
    ```

4. **Run the Application:**

    ```bash
    python app.py
    ```

    The application will be available at `http://127.0.0.1:5000/`.

## Usage

1. **Login:**
   - Navigate to `http://127.0.0.1:5000/`.
   - Enter a username to log in.

2. **Public Chat:**
   - Participate in the public chat room by sending messages that are visible to all logged-in users.

3. **Private Messaging:**
   - Start a private chat by clicking on a username in the user list.

4. **Create Posts:**
   - Use the "Create New Post" button to create and submit new posts.

5. **Update Status:**
   - Set your status to inform others of your current activity or mood.

## Testing

### Manual Testing

- **Public Chat:**
  - Log in as two different users in separate browser sessions.
  - Verify that messages sent in the public chat are visible to both users in real time.

- **Private Messaging:**
  - Initiate a private chat between two users.
  - Ensure that messages sent within the private chat are only visible to the two users involved.

- **Post Creation:**
  - Create a post and verify that it appears in the posts list.
  - Comment on a post and ensure that the comment is saved and displayed correctly.

- **Status Updates:**
  - Update the status of a user and verify that the new status is displayed in the user list.

### Automated Testing (Optional)

You can add automated tests using a testing framework like `unittest` or `pytest`. Below is a basic test case setup using `unittest`:

```python
import unittest
from app import app

class FlaskChatAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to use the chat', response.data)

    def test_login(self):
        response = self.app.post('/login', data=dict(username='testuser'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome, here are all the birds currently logged in', response.data)

    def test_private_chat_access(self):
        with self.app.session_transaction() as sess:
            sess['username'] = 'testuser'
        response = self.app.get('/chat/anotheruser')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Private Chat with anotheruser', response.data)

if __name__ == '__main__':
    unittest.main()
```

Run the tests with:

```bash
python -m unittest discover
```

## Debugging and Known Issues

### Debug Report

- **Issue:** Messages were not being sent in private chat rooms.
  - **Solution:** Ensure the correct room name is being used when emitting and receiving messages. Each private chat room is uniquely identified by the combined usernames of the participants.

- **Issue:** Users were unable to leave the private chat room properly.
  - **Solution:** Added a "Close Chat" button that emits a `leave_room` event and redirects the user to the home page.

- **Logging:**
  - Use Flask's built-in logging features to monitor server activity.
  - You can enable detailed error logs by setting `debug=True` when running the app.

### Known Issues

- **Emoji Support:** If emoji rendering is inconsistent across different platforms or browsers, consider using an emoji picker library to standardize input.
- **Session Management:** Users need to manually log out. Implementing a session timeout could improve usability.

## Future Enhancements

- **User Authentication:** Implement a full authentication system with password support using Flask-Login.
- **Persistent Chat:** Store chat messages in a database to allow users to view chat history.
- **Enhanced UI:** Improve the UI with more responsive design elements and better mobile support.
- **File Sharing:** Allow users to share files or images within chat rooms.
- **Notifications:** Implement notifications for incoming messages or when users join/leave chat rooms.
