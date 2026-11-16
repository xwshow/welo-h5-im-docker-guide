from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import AddFriendForm, LoginForm, RegisterForm
from .models import Friendship, Message, Thread
from .services import accept_friend, request_friend


class UserLoginView(LoginView):
    template_name = "chat/login.html"
    authentication_form = LoginForm


class UserLogoutView(LogoutView):
    next_page = "/login/"


def register(request):
    if request.user.is_authenticated:
        return redirect("inbox")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("inbox")
    return render(request, "chat/register.html", {"form": form})


@login_required
def inbox(request):
    threads = (
        Thread.objects.filter(Q(user_a=request.user) | Q(user_b=request.user))
        .select_related("user_a", "user_b")
        .order_by("-updated_at")
    )
    rows = []
    for thread in threads:
        other = thread.user_b if thread.user_a_id == request.user.pk else thread.user_a
        last = thread.messages.order_by("-id").first()
        rows.append({"thread": thread, "other": other, "last": last})
    return render(request, "chat/inbox.html", {"rows": rows})


@login_required
def friends(request):
    form = AddFriendForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            request_friend(request.user, form.cleaned_data["username"].strip())
            messages.success(request, "已发送好友申请 / 已自动成为好友")
            return redirect("friends")
        except ValueError as exc:
            messages.error(request, str(exc))
    pending = Friendship.objects.filter(
        to_user=request.user, status=Friendship.PENDING
    ).select_related("from_user")
    accepted = Friendship.objects.filter(status=Friendship.ACCEPTED).filter(
        Q(from_user=request.user) | Q(to_user=request.user)
    ).select_related("from_user", "to_user")
    friend_users = []
    for row in accepted:
        friend_users.append(row.to_user if row.from_user_id == request.user.pk else row.from_user)
    return render(
        request,
        "chat/friends.html",
        {"form": form, "pending": pending, "friends": friend_users},
    )


@login_required
@require_POST
def friend_accept(request, friendship_id: int):
    try:
        accept_friend(request.user, friendship_id)
        messages.success(request, "已添加好友")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("friends")


@login_required
def thread_page(request, thread_id: int):
    thread = get_object_or_404(Thread, pk=thread_id)
    if request.user.pk not in {thread.user_a_id, thread.user_b_id}:
        raise Http404()
    other = thread.user_b if thread.user_a_id == request.user.pk else thread.user_a
    recent = list(thread.messages.select_related("sender").order_by("-id")[:50])
    recent.reverse()
    return render(
        request,
        "chat/thread.html",
        {"thread": thread, "other": other, "messages": recent},
    )


@login_required
@require_GET
def thread_history(request, thread_id: int):
    thread = get_object_or_404(Thread, pk=thread_id)
    if request.user.pk not in {thread.user_a_id, thread.user_b_id}:
        raise Http404()
    before = request.GET.get("before")
    qs = thread.messages.select_related("sender").order_by("-id")
    if before and before.isdigit():
        qs = qs.filter(id__lt=int(before))
    rows = list(qs[:50])
    rows.reverse()
    return JsonResponse(
        {
            "messages": [
                {
                    "id": m.pk,
                    "body": m.body,
                    "sender_id": m.sender_id,
                    "sender": m.sender.username,
                    "created_at": m.created_at.isoformat(),
                }
                for m in rows
            ]
        }
    )


@login_required
@require_POST
def open_thread(request, user_id: int):
    if user_id == request.user.pk:
        raise Http404()
    from .services import are_friends

    if not are_friends(request.user.pk, user_id):
        messages.error(request, "需要先成为好友")
        return redirect("friends")
    thread = Thread.get_or_create_for(request.user.pk, user_id)
    return redirect("thread", thread_id=thread.pk)
