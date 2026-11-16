from django.conf import settings
from django.db import models
from django.db.models import Q


class Friendship(models.Model):
    """Accepted friend edge. One row per unordered pair (user_low_id, user_high_id)."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    STATUS_CHOICES = [
        (PENDING, "pending"),
        (ACCEPTED, "accepted"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="uniq_friend_pair_direction"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.from_user_id}->{self.to_user_id}:{self.status}"


class Thread(models.Model):
    """One private conversation between exactly two users."""

    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads_as_a",
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads_as_b",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user_a", "user_b"], name="uniq_thread_pair"),
            models.CheckConstraint(
                condition=Q(user_a_id__lt=models.F("user_b_id")),
                name="thread_user_a_lt_user_b",
            ),
        ]

    @classmethod
    def pair_ids(cls, uid1: int, uid2: int) -> tuple[int, int]:
        return (uid1, uid2) if uid1 < uid2 else (uid2, uid1)

    @classmethod
    def get_or_create_for(cls, uid1: int, uid2: int) -> "Thread":
        a, b = cls.pair_ids(uid1, uid2)
        thread, _ = cls.objects.get_or_create(user_a_id=a, user_b_id=b)
        return thread

    def other_user_id(self, user_id: int) -> int:
        return self.user_b_id if self.user_a_id == user_id else self.user_a_id

    def group_name(self) -> str:
        return f"thread_{self.pk}"


class Message(models.Model):
    """One chat row. Persist first, then broadcast — never the reverse."""

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_sent",
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"msg:{self.pk}"
