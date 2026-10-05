import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.http import JsonResponse
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
    query = request.GET.get("q", "").strip()
    experiences = Experience.objects.annotate(
        star_count=Count("starred_by", distinct=True),
    ).order_by("-started_at", "title")

    if query:
        experiences = experiences.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__icontains=query)
        )

    if request.user.is_authenticated:
        starred_experiences = request.user.starred_experiences.filter(
            pk=OuterRef("pk")
        )
        experiences = experiences.annotate(
            is_starred=Exists(starred_experiences),
        )
    else:
        experiences = experiences.annotate(
            is_starred=Value(False, output_field=BooleanField()),
        )

    data = [
        {
            "pk": str(experience.id),
            "fields": {
                "title": experience.title,
                "description": experience.description,
                "category": experience.category,
                "category_label": experience.get_category_display(),
                "thumbnail": experience.thumbnail,
                "started_at": experience.started_at.isoformat(),
                "ended_at": (
                    experience.ended_at.isoformat()
                    if experience.ended_at
                    else None
                ),
                "is_ongoing": experience.is_ongoing,
                "star_count": experience.star_count,
                "is_starred": experience.is_starred,
            },
        }
        for experience in experiences
    ]

    return JsonResponse(data, safe=False)


def show_experience(request):
    experiences = Experience.objects.prefetch_related("starred_by").order_by(
        "-started_at",
        "title",
    )

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "experience_list": list(experiences),
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


@login_required(login_url="/login/")
@require_POST
def toggle_experience_star(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if experience.starred_by.filter(pk=request.user.pk).exists():
        experience.starred_by.remove(request.user)
    else:
        experience.starred_by.add(request.user)

    return redirect("main:show_experience")


def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related("starred_by").order_by(
        "display_order",
        "title",
    )

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    data = []
    for project in projects:
        starred_users = list(project.starred_by.all())
        is_starred = request.user.is_authenticated and any(
            user.pk == request.user.pk for user in starred_users
        )
        data.append(
            {
                "pk": str(project.id),
                "fields": {
                    "title": project.title,
                    "role": project.role,
                    "description": project.description,
                    "thumbnail": project.thumbnail,
                    "primary_link_label": project.primary_link_label,
                    "primary_link_url": project.primary_link_url,
                    "secondary_link_label": project.secondary_link_label,
                    "secondary_link_url": project.secondary_link_url,
                    "third_link_label": project.third_link_label,
                    "third_link_url": project.third_link_url,
                    "note": project.note,
                    "display_order": project.display_order,
                    "star_count": len(starred_users),
                    "is_starred": is_starred,
                },
            }
        )

    return JsonResponse(data, safe=False)


def show_projects(request):
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Muhammad Eshan Bobby Bhaskara",
        "title_query": title_query,
        "form": ProjectForm(),
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


@require_POST
def create_project_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Only the portfolio owner can add projects."},
            status=403,
        )

    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {
                "message": "Project added successfully.",
                "pk": str(project.id),
            },
            status=201,
        )

    return JsonResponse(
        {"errors": form.errors.get_json_data()},
        status=400,
    )


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
@require_POST
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")
