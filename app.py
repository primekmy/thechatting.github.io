import flet as ft
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_cred.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Message():
    def __init__(self, user_name: str, text: str, message_type: str):
        self.user_name = user_name
        self.text = text
        self.message_type = message_type

class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = "start"
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text, selectable=True),
                ],
                tight=True,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        return user_name[:1].capitalize()

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.colors.AMBER,
            ft.colors.BLUE,
            ft.colors.BROWN,
            ft.colors.CYAN,
            ft.colors.GREEN,
            ft.colors.INDIGO,
            ft.colors.LIME,
            ft.colors.ORANGE,
            ft.colors.PINK,
            ft.colors.PURPLE,
            ft.colors.RED,
            ft.colors.TEAL,
            ft.colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_user(username, email, password):
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

def check_user(username, password):
    hashed_password = hash_password(password)
    user = User.query.filter_by(username=username, password_hash=hashed_password).first()
    return user is not None

def main(page: ft.Page):
    page.horizontal_alignment = "stretch"
    page.title = "Flet Chat"

    def join_chat_click(e):
        if not join_user_name.value:
            join_user_name.error_text = "Name cannot be blank!"
            join_user_name.update()
        else:
            page.session.set("user_name", join_user_name.value)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{join_user_name.value}: ")
            page.pubsub.send_all(Message(user_name=join_user_name.value, text=f"{join_user_name.value} has joined the chat.", message_type="login_message"))
            page.update()

    def send_message_click(e):
        if new_message.value != "":
            page.pubsub.send_all(Message(page.session.get("user_name"), new_message.value, message_type="chat_message"))
            new_message.value = ""
            new_message.focus()
            page.update()

    def login_click(e):
        username = login_user_name.value
        password = login_password.value
        if check_user(username, password):
            page.session.set("user_name", username)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{username}: ")
            page.pubsub.send_all(Message(user_name=username, text=f"{username} has joined the chat.", message_type="login_message"))
            page.update()
        else:
            login_user_name.error_text = "Invalid credentials"
            login_user_name.update()

    def signup_click(e):
        username = signup_user_name.value
        email = signup_email.value
        password = signup_password.value

        if not username or not email or not password:
            signup_user_name.error_text = signup_email.error_text = signup_password.error_text = "All fields are required!"
            signup_user_name.update()
            signup_email.update()
            signup_password.update()
        elif len(password) < 8 or any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~" for char in password):
            signup_password.error_text = "Password must be at least 8 characters long and should not contain special characters."
            signup_password.update()
        else:
            create_user(username, email, password)
            page.session.set("user_name", username)
            page.dialog.open = False
            new_message.prefix = ft.Text(f"{username}: ")
            page.pubsub.send_all(Message(user_name=username, text=f"{username} has joined the chat.", message_type="login_message"))
            page.update()

    def on_message(message: Message):
        if message.message_type == "chat_message":
            m = ChatMessage(message)
        elif message.message_type == "login_message":
            m = ft.Text(message.text, italic=True, color=ft.colors.BLACK45, size=12)
        chat.controls.append(m)
        page.update()

    page.pubsub.subscribe(on_message)

    # A dialog asking for a user display name
    join_user_name = ft.TextField(
        label="Enter your name to join the chat",
        autofocus=True,
        on_submit=join_chat_click,
    )
    page.dialog = ft.AlertDialog(
        open=True,
        modal=True,
        title=ft.Text("Welcome!"),
        content=ft.Column([join_user_name], width=300, height=70, tight=True),
        actions=[ft.ElevatedButton(text="Join chat", on_click=join_chat_click)],
        actions_alignment="end",
    )

    # Login dialog
    login_user_name = ft.TextField(
        label="Username:",
        autofocus=True,
    )
    login_password = ft.TextField(
        label="Password:",
        password=True,
    )
    page.login_dialog = ft.AlertDialog(
        title=ft.Text("Login"),
        content=ft.Column([login_user_name, login_password], width=300, height=120, tight=True),
        actions=[ft.ElevatedButton(text="Login", on_click=login_click)],
        actions_alignment="end",
    )

    # Signup dialog
    signup_user_name = ft.TextField(
        label="Username:",
    )
    signup_email = ft.TextField(
        label="Email:",
    )
    signup_password = ft.TextField(
        label="Password:",
        password=True,
    )
    page.signup_dialog = ft.AlertDialog(
        title=ft.Text("Signup"),
        content=ft.Column([signup_user_name, signup_email, signup_password], width=300, height=150, tight=True),
        actions=[ft.ElevatedButton(text="Signup", on_click=signup_click)],
        actions_alignment="end",
    )

    # Chat messages
    chat = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
    )

    # A new message entry form
    new_message = ft.TextField(
        hint_text="Write a message...",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=True,
        on_submit=send_message_click,
    )

    # Add everything to the page
    page.add(
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        ),
        ft.Row(
            [
                new_message,
                ft.IconButton(
                    icon=ft.icons.SEND_ROUNDED,
                    tooltip="Send message",
                    on_click=send_message_click,
                ),
            ]
        ),
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ft.app(port=8550, target=main, view=ft.WEB_BROWSER)
