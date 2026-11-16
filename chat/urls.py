from django.urls import path

from . import views

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("friends/", views.friends, name="friends"),
    path("friends/<int:friendship_id>/accept/", views.friend_accept, name="friend_accept"),
    path("chats/open/<int:user_id>/", views.open_thread, name="open_thread"),
    path("chats/<int:thread_id>/", views.thread_page, name="thread"),
    path("chats/<int:thread_id>/history/", views.thread_history, name="thread_history"),
]
