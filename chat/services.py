from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Friendship, Message, Thread

User = get_user_model()
MAX_BODY = 2000


def clean_body(raw: str) -> str:
    text = (raw or "").replace("\x00", "").strip()
    if not text:
        raise ValueError("empty")
    if len(text) > MAX_BODY:
        text = text[:MAX_BODY]
    return text


def are_friends(user_id: int, other_id: int) -> bool:
    return Friendship.objects.filter(
        status=Friendship.ACCEPTED
    ).filter(
        Q(from_user_id=user_id, to_user_id=other_id)
        | Q(from_user_id=other_id, to_user_id=user_id)
    ).exists()


def request_friend(from_user, to_username: str) -> Friendship:
    to_user = User.objects.filter(username=to_username).first()
    if not to_user:
        raise ValueError("用户不存在")
    if to_user.pk == from_user.pk:
        raise ValueError("不能添加自己")
    if are_friends(from_user.pk, to_user.pk):
        raise ValueError("已经是好友")
    existing = Friendship.objects.filter(
        Q(from_user=from_user, to_user=to_user) | Q(from_user=to_user, to_user=from_user)
    ).first()
    if existing:
        if existing.status == Friendship.ACCEPTED:
            raise ValueError("已经是好友")
        if existing.to_user_id == from_user.pk:
            existing.status = Friendship.ACCEPTED
            existing.save(update_fields=["status"])
            Thread.get_or_create_for(from_user.pk, to_user.pk)
            return existing
        raise ValueError("已发送申请，等待对方确认")
    return Friendship.objects.create(
        from_user=from_user, to_user=to_user, status=Friendship.PENDING
    )


def accept_friend(user, friendship_id: int) -> Friendship:
    row = Friendship.objects.filter(
        pk=friendship_id, to_user=user, status=Friendship.PENDING
    ).first()
    if not row:
        raise ValueError("申请不存在")
    row.status = Friendship.ACCEPTED
    row.save(update_fields=["status"])
    Thread.get_or_create_for(row.from_user_id, row.to_user_id)
    return row


def persist_text_message(thread: Thread, sender, raw_body: str) -> Message:
    """Write message to DB first. Caller broadcasts after this returns."""
    if sender.pk not in {thread.user_a_id, thread.user_b_id}:
        raise PermissionError("not a member")
    other_id = thread.other_user_id(sender.pk)
    if not are_friends(sender.pk, other_id):
        raise PermissionError("not friends")
    body = clean_body(raw_body)
    msg = Message.objects.create(thread=thread, sender=sender, body=body)
    Thread.objects.filter(pk=thread.pk).update(updated_at=msg.created_at)
    return msg
