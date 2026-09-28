import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import ExperienceForm, ProjectForm
from main.models import Experience, Project
from main.permissions import editor_or_superuser_required, superuser_required


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("main:login")

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
    }
    return render(request, "register.html", context)


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:show_main")
        response.set_cookie(
            "last_login",
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        return response

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response


def show_main(request):
    last_login = request.COOKIES.get(
        "last_login",
        "No previous login session found",
    )
    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "npm": "2506546333",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "Information Systems student at Fasilkom UI with a growing "
            "interest in technology and its impact on society. Working "
            "collaboratively, thinking critically, and approaching problems "
            "with attention to detail."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def get_experiences_json(request):
    experiences = Experience.objects.order_by("-started_at", "title")
    experiences_json = serializers.serialize("json", experiences)
    return HttpResponse(experiences_json, content_type="application/json")


def show_experience(request):
    json_response = get_experiences_json(request)
    serialized_experiences = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    experiences = [
        serialized_experience.object
        for serialized_experience in serialized_experiences
    ]

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "experience_list": experiences,
    }
    return render(request, "experience.html", context)


@superuser_required
def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience added successfully!")
        return redirect("main:show_experience")

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
        "form_title": "Add Experience",
        "submit_label": "Add Experience",
    }
    return render(request, "experience_form.html", context)


@editor_or_superuser_required("main.change_experience")
def update_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    form = ExperienceForm(request.POST or None, instance=experience)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience updated successfully!")
        return redirect("main:show_experience")

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
        "form_title": "Update Experience",
        "submit_label": "Save Changes",
    }
    return render(request, "experience_form.html", context)


@superuser_required
@require_POST
def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    experience.delete()
    messages.success(request, "Experience deleted successfully!")
    return redirect("main:show_experience")


def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.order_by("display_order", "title")

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize(
        "json",
        projects,
        use_natural_foreign_keys=True,
    )
    return HttpResponse(projects_json, content_type="application/json")


def show_projects(request):
    json_response = get_projects_json(request)
    serialized_projects = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    projects = [serialized_project.object for serialized_project in serialized_projects]

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "project_list": projects,
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "projects.html", context)


@superuser_required
def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added successfully!")
        return redirect("main:show_projects")

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
        "form_title": "Add New Project",
        "submit_label": "Add Project",
    }
    return render(request, "projects_form.html", context)


@editor_or_superuser_required("main.change_project")
def update_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated successfully!")
        return redirect("main:show_projects")

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "form": form,
        "form_title": "Update Project",
        "submit_label": "Save Changes",
    }
    return render(request, "projects_form.html", context)


@superuser_required
@require_POST
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project deleted successfully!")
    return redirect("main:show_projects")


@login_required(login_url="/login/")
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST":
        if request.user in project.starred_by.all():
            project.starred_by.remove(request.user)
        else:
            project.starred_by.add(request.user)

    return redirect("main:show_projects")
