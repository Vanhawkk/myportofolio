import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import (
    DateInput,
    ModelForm,
    NumberInput,
    Textarea,
    TextInput,
    URLInput,
)
from django.utils.html import strip_tags

from main.models import Experience, Project


class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "started_at",
            "ended_at",
            "thumbnail",
        ]
        labels = {
            "title": "Experience title",
            "description": "Description",
            "category": "Category",
            "started_at": "Start date",
            "ended_at": "End date (leave blank if ongoing)",
            "thumbnail": "Thumbnail URL",
        }
        widgets = {
            "title": TextInput(attrs={"placeholder": "Marketing Staff at RISTEK"}),
            "description": Textarea(
                attrs={
                    "placeholder": "Describe the experience and your contribution",
                    "rows": 4,
                }
            ),
            "started_at": DateInput(attrs={"type": "date"}),
            "ended_at": DateInput(attrs={"type": "date"}),
            "thumbnail": URLInput(
                attrs={"placeholder": "https://example.com/image.jpg"}
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError(
                "Experience title cannot contain only HTML tags."
            )
        return title

    def clean_description(self):
        description = strip_tags(self.cleaned_data["description"]).strip()
        if not description:
            raise ValidationError(
                "Experience description cannot contain only HTML tags."
            )
        return description

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get("thumbnail")
        if not thumbnail:
            return thumbnail

        thumbnail = strip_tags(thumbnail).strip()
        URLValidator(schemes=["http", "https"])(thumbnail)
        return thumbnail

    def clean(self):
        cleaned_data = super().clean()
        started_at = cleaned_data.get("started_at")
        ended_at = cleaned_data.get("ended_at")

        if started_at and ended_at and ended_at < started_at:
            self.add_error(
                "ended_at",
                "End date cannot be earlier than start date.",
            )

        return cleaned_data


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "role",
            "description",
            "thumbnail",
            "primary_link_label",
            "primary_link_url",
            "secondary_link_label",
            "secondary_link_url",
            "third_link_label",
            "third_link_url",
            "note",
            "display_order",
        ]
        labels = {
            "title": "Project title",
            "role": "Role",
            "description": "Description",
            "thumbnail": "Thumbnail path or URL",
            "primary_link_label": "Primary link label",
            "primary_link_url": "Primary link URL",
            "secondary_link_label": "Secondary link label",
            "secondary_link_url": "Secondary link URL",
            "third_link_label": "Third link label",
            "third_link_url": "Third link URL",
            "note": "Note",
            "display_order": "Display order",
        }
        widgets = {
            "title": TextInput(attrs={"placeholder": "Portfolio Website"}),
            "role": TextInput(attrs={"placeholder": "Designer & Developer"}),
            "description": Textarea(
                attrs={
                    "placeholder": "Describe the project and your contribution",
                    "rows": 4,
                }
            ),
            "thumbnail": TextInput(
                attrs={
                    "placeholder": "/static/img/project-example.jpg or https://...",
                }
            ),
            "primary_link_label": TextInput(attrs={"placeholder": "GitHub"}),
            "primary_link_url": URLInput(attrs={"placeholder": "https://github.com/..."}),
            "secondary_link_label": TextInput(attrs={"placeholder": "Live Demo"}),
            "secondary_link_url": URLInput(attrs={"placeholder": "https://..."}),
            "third_link_label": TextInput(attrs={"placeholder": "Case Study"}),
            "third_link_url": URLInput(attrs={"placeholder": "https://..."}),
            "note": TextInput(attrs={"placeholder": "Optional note"}),
            "display_order": NumberInput(attrs={"min": 0}),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Project title cannot contain only HTML tags.")
        return title

    def clean_role(self):
        role = strip_tags(self.cleaned_data["role"]).strip()
        if not role:
            raise ValidationError("Project role cannot contain only HTML tags.")
        return role

    def clean_description(self):
        description = strip_tags(self.cleaned_data["description"]).strip()
        if not description:
            raise ValidationError(
                "Project description cannot contain only HTML tags."
            )
        return description

    def clean_thumbnail(self):
        thumbnail = strip_tags(self.cleaned_data["thumbnail"]).strip()

        if thumbnail.startswith("/static/"):
            is_safe_static_path = re.fullmatch(
                r"/static/[A-Za-z0-9_./-]+",
                thumbnail,
            )
            if is_safe_static_path and ".." not in thumbnail.split("/"):
                return thumbnail
            raise ValidationError("Enter a safe static image path.")

        URLValidator(schemes=["http", "https"])(thumbnail)
        return thumbnail

    def clean_primary_link_label(self):
        return strip_tags(self.cleaned_data["primary_link_label"]).strip()

    def clean_secondary_link_label(self):
        return strip_tags(self.cleaned_data["secondary_link_label"]).strip()

    def clean_third_link_label(self):
        return strip_tags(self.cleaned_data["third_link_label"]).strip()

    def clean_note(self):
        return strip_tags(self.cleaned_data["note"]).strip()
