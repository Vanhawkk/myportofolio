from django.urls import path

from main.views import (
    create_experience,
    create_experience_ajax,
    create_project,
    create_project_ajax,
    delete_experience,
    delete_project,
    get_experiences_json,
    get_projects_json,
    login_user,
    logout_user,
    register,
    show_experience,
    show_main,
    show_projects,
    toggle_experience_star,
    toggle_star,
    update_experience,
    update_project,
)


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/add/", create_experience, name="create_experience"),
    path(
        "experience/add-ajax/",
        create_experience_ajax,
        name="create_experience_ajax",
    ),
    path(
        "experience/<uuid:experience_id>/edit/",
        update_experience,
        name="update_experience",
    ),
    path(
        "experience/<uuid:experience_id>/delete/",
        delete_experience,
        name="delete_experience",
    ),
    path(
        "experience/<uuid:experience_id>/star/",
        toggle_experience_star,
        name="toggle_experience_star",
    ),
    path("api/experiences/", get_experiences_json, name="get_experiences_json"),
    path("projects/", show_projects, name="show_projects"),
    path("projects/add/", create_project, name="create_project"),
    path(
        "projects/add-ajax/",
        create_project_ajax,
        name="create_project_ajax",
    ),
    path(
        "projects/<uuid:project_id>/edit/",
        update_project,
        name="update_project",
    ),
    path(
        "projects/<uuid:project_id>/star/",
        toggle_star,
        name="toggle_star",
    ),
    path(
        "projects/<uuid:project_id>/delete/",
        delete_project,
        name="delete_project",
    ),
    path("api/projects/", get_projects_json, name="get_projects_json"),
]
