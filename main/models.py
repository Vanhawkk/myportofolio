import uuid

from django.contrib.auth.models import User
from django.db import models


class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ('internship', 'Internship'),
        ('research', 'Research'),
        ('volunteer', 'Volunteer'),
        ('part-time', 'Part-Time'),
        ('full-time', 'Full-Time'),
        ('freelance', 'Freelance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='full-time',
    )
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    starred_by = models.ManyToManyField(
        User,
        related_name="starred_experiences",
        blank=True,
    )

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None
    
class Project(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.CharField(max_length=255)
    primary_link_label = models.CharField(max_length=100, blank=True)
    primary_link_url = models.URLField(blank=True)
    secondary_link_label = models.CharField(max_length=100, blank=True)
    secondary_link_url = models.URLField(blank=True)
    third_link_label = models.CharField(max_length=100, blank=True)
    third_link_url = models.URLField(blank=True)
    note = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    starred_by = models.ManyToManyField(
        User,
        related_name="starred_projects",
        blank=True,
    )

    def __str__(self):
        return self.title
