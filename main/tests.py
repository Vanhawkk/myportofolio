import json
import re
import uuid

from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Project


class AuthenticationTest(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            username="existing_user",
            password=self.password,
        )

    def test_register_page_is_accessible(self):
        response = self.client.get(reverse("main:register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "register.html")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(
            list(response.context["form"].fields),
            ["username", "password1", "password2"],
        )

    def test_register_with_valid_data(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "new_user",
                "password1": self.password,
                "password2": self.password,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("main:login"))
        new_user = User.objects.get(username="new_user")
        self.assertTrue(new_user.check_password(self.password))
        self.assertContains(
            response,
            "Account created successfully. Please log in.",
        )

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": "new_user",
                "password1": self.password,
                "password2": "DifferentPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_register_rejects_duplicate_username(self):
        response = self.client.post(
            reverse("main:register"),
            {
                "username": self.user.username,
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.filter(username=self.user.username).count(), 1)

    def test_login_page_is_accessible(self):
        response = self.client.get(reverse("main:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(self.user.pk),
        )

    def test_login_sets_last_login_cookie(self):
        response = self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": self.password,
            },
        )

        self.assertIn("last_login", response.cookies)
        self.assertRegex(
            response.cookies["last_login"].value,
            re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),
        )

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            reverse("main:login"),
            {
                "username": self.user.username,
                "password": "WrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_navbar_changes_after_login(self):
        anonymous_response = self.client.get(reverse("main:show_main"))
        self.assertContains(anonymous_response, reverse("main:login"))
        self.assertContains(anonymous_response, reverse("main:register"))

        self.client.force_login(self.user)
        authenticated_response = self.client.get(reverse("main:show_main"))
        self.assertContains(authenticated_response, self.user.username)
        self.assertContains(authenticated_response, reverse("main:logout"))
        self.assertNotContains(authenticated_response, reverse("main:register"))

    def test_logout_clears_authenticated_session(self):
        self.client.force_login(self.user)
        self.client.cookies["last_login"] = "2026-09-23 10:30:00"

        response = self.client.get(reverse("main:logout"))

        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.cookies["last_login"].value, "")
        self.assertEqual(response.cookies["last_login"]["max-age"], 0)

    def test_main_page_displays_last_login_cookie(self):
        last_login = "2026-09-23 10:30:00"
        self.client.cookies["last_login"] = last_login

        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, last_login)

    def test_main_page_displays_default_without_last_login_cookie(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertContains(response, "No previous login session found")


class MainTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="portfolio_owner",
            password="StrongPassword123!",
            email="owner@example.com",
        )
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(
            response,
            f'href="{reverse("main:show_experience")}"',
        )
        self.assertContains(response, 'id="toast-component"')
        self.assertContains(response, "js/toast.js")

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")
        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing")
        self.assertContains(
            response,
            f'href="{reverse("main:show_main")}"',
        )

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))
        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))
        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Done")
        self.assertNotContains(response, "Ongoing")

    def test_create_experience_page_is_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("main:create_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")
        self.assertContains(response, "Add Experience")
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertEqual(
            list(response.context["form"].fields),
            ["title", "description", "category", "thumbnail"],
        )

    def test_create_experience_with_valid_data(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Product Design Intern",
                "description": "Designed and tested product flows.",
                "category": "internship",
                "thumbnail": "https://example.com/internship.jpg",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(
            Experience.objects.filter(title="Product Design Intern").exists()
        )
        self.assertContains(response, "Experience added successfully!")

    def test_create_experience_with_invalid_data(self):
        self.client.force_login(self.superuser)
        experience_count = Experience.objects.count()
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "",
                "description": "Missing a required title.",
                "category": "internship",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")
        self.assertContains(response, "This field is required.")
        self.assertEqual(Experience.objects.count(), experience_count)

    def test_update_experience_page_is_prefilled(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("main:update_experience", args=[self.experience.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")
        self.assertContains(response, "Update Experience")
        self.assertContains(response, f'value="{self.experience.title}"')

    def test_update_experience_with_valid_data(self):
        self.client.force_login(self.superuser)
        experience_count = Experience.objects.count()
        response = self.client.post(
            reverse("main:update_experience", args=[self.experience.id]),
            {
                "title": "Teaching Assistant PBP",
                "description": "Helped students learn Django.",
                "category": "part-time",
                "thumbnail": "https://example.com/teaching.jpg",
            },
            follow=True,
        )

        self.experience.refresh_from_db()
        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertEqual(Experience.objects.count(), experience_count)
        self.assertEqual(self.experience.title, "Teaching Assistant PBP")
        self.assertEqual(self.experience.description, "Helped students learn Django.")
        self.assertContains(response, "Experience updated successfully!")

    def test_update_experience_returns_404_for_unknown_id(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("main:update_experience", args=[uuid.uuid4()])
        )

        self.assertEqual(response.status_code, 404)

    def test_experience_page_shows_thumbnail_and_actions(self):
        self.experience.thumbnail = "https://example.com/experience.jpg"
        self.experience.save()
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("main:show_experience"))
        update_url = reverse("main:update_experience", args=[self.experience.id])

        self.assertContains(response, self.experience.thumbnail)
        self.assertContains(response, f'href="{reverse("main:create_experience")}"')
        self.assertContains(response, f'href="{update_url}"')

    def test_experiences_json_endpoint(self):
        response = self.client.get(reverse("main:get_experiences_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["model"], "main.experience")
        self.assertEqual(data[0]["pk"], str(self.experience.id))
        self.assertEqual(data[0]["fields"]["title"], self.experience.title)
        self.assertEqual(data[0]["fields"]["category"], "part-time")
        self.assertEqual(
            set(data[0]["fields"]),
            {
                "title",
                "description",
                "category",
                "thumbnail",
                "started_at",
                "ended_at",
            },
        )

    def test_experiences_json_endpoint_returns_empty_list(self):
        Experience.objects.all().delete()

        response = self.client.get(reverse("main:get_experiences_json"))

        self.assertEqual(json.loads(response.content), [])

    def test_experience_page_uses_deserialized_objects(self):
        response = self.client.get(reverse("main:show_experience"))
        experience_list = response.context["experience_list"]

        self.assertIsInstance(experience_list, list)
        self.assertEqual(len(experience_list), 1)
        self.assertIsInstance(experience_list[0], Experience)
        self.assertEqual(experience_list[0].id, self.experience.id)

    def test_experience_page_contains_delete_confirmation(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("main:show_experience"))
        delete_url = reverse("main:delete_experience", args=[self.experience.id])

        self.assertContains(response, "Delete Experience?")
        self.assertContains(response, f'action="{delete_url}"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_delete_experience_with_post(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:delete_experience", args=[self.experience.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())
        self.assertContains(response, "Experience deleted successfully!")

    def test_delete_experience_rejects_get(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("main:delete_experience", args=[self.experience.id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_delete_experience_returns_404_for_unknown_id(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:delete_experience", args=[uuid.uuid4()])
        )

        self.assertEqual(response.status_code, 404)


class ExperienceAuthorizationTest(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(username="regular_user")
        self.editor = User.objects.create_user(username="experience_editor")
        self.superuser = User.objects.create_superuser(
            username="portfolio_owner",
            password="StrongPassword123!",
            email="owner@example.com",
        )
        self.experience = Experience.objects.create(
            title="Authorization Test Experience",
            description="Used to verify the experience permission matrix.",
            category="part-time",
        )

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="main",
                codename="change_experience",
            )
        )
        self.editor.groups.add(editor_group)

        self.create_url = reverse("main:create_experience")
        self.update_url = reverse(
            "main:update_experience",
            args=[self.experience.id],
        )
        self.delete_url = reverse(
            "main:delete_experience",
            args=[self.experience.id],
        )
        self.list_url = reverse("main:show_experience")

    def test_experience_list_remains_public(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.experience.title)

    def test_anonymous_user_is_redirected_from_experience_mutations(self):
        responses = [
            self.client.get(self.create_url),
            self.client.get(self.update_url),
            self.client.post(self.delete_url),
        ]

        for response, protected_url in zip(
            responses,
            [self.create_url, self.update_url, self.delete_url],
        ):
            self.assertRedirects(
                response,
                f"{reverse('main:login')}?next={protected_url}",
                fetch_redirect_response=False,
            )

        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_regular_user_receives_forbidden_for_experience_mutations(self):
        self.client.force_login(self.regular_user)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.get(self.update_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_editor_can_update_experience(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            self.update_url,
            {
                "title": "Updated by Editor",
                "description": self.experience.description,
                "category": self.experience.category,
                "thumbnail": "",
            },
        )

        self.assertRedirects(response, self.list_url)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Updated by Editor")

    def test_editor_cannot_create_or_delete_experience(self):
        self.client.force_login(self.editor)

        self.assertEqual(self.client.get(self.create_url).status_code, 403)
        self.assertEqual(self.client.post(self.delete_url).status_code, 403)
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

    def test_anonymous_and_regular_users_do_not_see_experience_controls(self):
        anonymous_response = self.client.get(self.list_url)

        self.assertNotContains(anonymous_response, f'href="{self.create_url}"')
        self.assertNotContains(anonymous_response, f'href="{self.update_url}"')
        self.assertNotContains(anonymous_response, f'action="{self.delete_url}"')

        self.client.force_login(self.regular_user)
        regular_response = self.client.get(self.list_url)

        self.assertNotContains(regular_response, f'href="{self.create_url}"')
        self.assertNotContains(regular_response, f'href="{self.update_url}"')
        self.assertNotContains(regular_response, f'action="{self.delete_url}"')

    def test_editor_sees_only_experience_update_control(self):
        self.client.force_login(self.editor)

        response = self.client.get(self.list_url)

        self.assertNotContains(response, f'href="{self.create_url}"')
        self.assertContains(response, f'href="{self.update_url}"')
        self.assertNotContains(response, f'action="{self.delete_url}"')

    def test_superuser_sees_all_experience_controls(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.list_url)

        self.assertContains(response, f'href="{self.create_url}"')
        self.assertContains(response, f'href="{self.update_url}"')
        self.assertContains(response, f'action="{self.delete_url}"')


class ProjectTest(TestCase):
    def setUp(self):
        self.password = "StrongPassword123!"
        self.regular_user = User.objects.create_user(
            username="regular_user",
            password=self.password,
            email="regular@example.com",
        )
        self.editor = User.objects.create_user(
            username="project_editor",
            password=self.password,
        )
        self.superuser = User.objects.create_superuser(
            username="portfolio_owner",
            password=self.password,
            email="owner@example.com",
        )
        self.project = Project.objects.create(
            title="VETO",
            role="Concept · Design · Direction",
            description="API-first ODOL middleware.",
            thumbnail="/static/img/project-veto.jpg",
            primary_link_label="GitHub",
            primary_link_url="https://github.com/6avier/veto",
            display_order=1,
        )

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="main",
                codename="change_project",
            )
        )
        self.editor.groups.add(editor_group)

    def test_project_model(self):
        self.assertEqual(str(self.project), "VETO")
        self.assertEqual(self.project.display_order, 1)

    def test_projects_url_is_accessible(self):
        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects.html")

    def test_projects_page_contains_ajax_shell(self):
        response = self.client.get(reverse("main:show_projects"))
        self.assertContains(response, 'id="projects-app"')
        self.assertContains(response, 'id="projects-loading"')
        self.assertContains(response, 'id="projects-error"')
        self.assertContains(response, 'id="projects-empty"')
        self.assertContains(response, 'id="projects-grid"')
        self.assertContains(response, "js/projects.js")
        self.assertContains(
            response,
            f'data-projects-endpoint="{reverse("main:get_projects_json")}"',
        )
        self.assertNotContains(response, self.project.title)

    def test_empty_projects_page(self):
        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))
        self.assertContains(response, "No projects have been added or found.")

    def test_main_page_links_to_projects(self):
        response = self.client.get(reverse("main:show_main"))
        self.assertContains(
            response,
            f'href="{reverse("main:show_projects")}"',
        )

    def test_create_project_page_is_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("main:create_project"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertContains(response, "Add New Project")
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_create_project_with_valid_data(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:create_project"),
            {
                "title": "New Portfolio",
                "role": "Designer & Developer",
                "description": "A new portfolio project.",
                "thumbnail": "/static/img/project-comprof.jpg",
                "primary_link_label": "GitHub",
                "primary_link_url": "https://github.com/example/portfolio",
                "display_order": 2,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Project.objects.filter(title="New Portfolio").exists())
        self.assertContains(response, "Project added successfully!")

    def test_create_project_with_invalid_data(self):
        self.client.force_login(self.superuser)
        project_count = Project.objects.count()
        response = self.client.post(
            reverse("main:create_project"),
            {
                "title": "",
                "role": "Developer",
                "description": "Missing a required title.",
                "thumbnail": "/static/img/project-comprof.jpg",
                "display_order": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertContains(response, "This field is required.")
        self.assertEqual(Project.objects.count(), project_count)

    def test_update_project_page_is_prefilled(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("main:update_project", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertContains(response, "Update Project")
        self.assertContains(response, f'value="{self.project.title}"')

    def test_update_project_with_valid_data(self):
        self.client.force_login(self.superuser)
        project_count = Project.objects.count()

        response = self.client.post(
            reverse("main:update_project", args=[self.project.id]),
            {
                "title": "Updated VETO",
                "role": self.project.role,
                "description": self.project.description,
                "thumbnail": self.project.thumbnail,
                "primary_link_label": self.project.primary_link_label,
                "primary_link_url": self.project.primary_link_url,
                "display_order": self.project.display_order,
            },
            follow=True,
        )

        self.project.refresh_from_db()
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(Project.objects.count(), project_count)
        self.assertEqual(self.project.title, "Updated VETO")
        self.assertContains(response, "Project updated successfully!")

    def test_update_project_returns_404_for_unknown_id(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("main:update_project", args=[uuid.uuid4()])
        )

        self.assertEqual(response.status_code, 404)

    def test_projects_json_endpoint(self):
        response = self.client.get(reverse("main:get_projects_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["pk"], str(self.project.id))
        self.assertEqual(data[0]["fields"]["title"], "VETO")
        self.assertEqual(
            set(data[0]["fields"]),
            {
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
                "star_count",
                "is_starred",
            },
        )

    def test_projects_json_includes_request_user_star_state(self):
        self.project.starred_by.add(self.regular_user)

        anonymous_response = self.client.get(reverse("main:get_projects_json"))
        anonymous_fields = json.loads(anonymous_response.content)[0]["fields"]

        self.client.force_login(self.regular_user)
        authenticated_response = self.client.get(
            reverse("main:get_projects_json")
        )
        authenticated_fields = json.loads(authenticated_response.content)[0]["fields"]

        self.assertEqual(anonymous_fields["star_count"], 1)
        self.assertFalse(anonymous_fields["is_starred"])
        self.assertEqual(authenticated_fields["star_count"], 1)
        self.assertTrue(authenticated_fields["is_starred"])

    def test_projects_json_can_filter_by_title(self):
        Project.objects.create(
            title="Unrelated Alpha",
            role="Developer",
            description="Another project.",
            thumbnail="/static/img/project-comprof.jpg",
            display_order=2,
        )

        response = self.client.get(
            reverse("main:get_projects_json"),
            {"title": "veto"},
        )

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["title"], "VETO")

    def test_projects_page_can_filter_by_title(self):
        Project.objects.create(
            title="Unrelated Alpha",
            role="Developer",
            description="Another project.",
            thumbnail="/static/img/project-comprof.jpg",
            display_order=2,
        )

        response = self.client.get(
            reverse("main:show_projects"),
            {"title": "veto"},
        )

        self.assertNotContains(response, self.project.title)
        self.assertNotContains(response, "Unrelated Alpha")
        self.assertContains(response, 'value="veto"')

    def test_projects_page_shows_search_empty_state(self):
        response = self.client.get(
            reverse("main:show_projects"),
            {"title": "missing"},
        )

        self.assertContains(response, "No projects have been added or found.")

    def test_projects_page_contains_delete_confirmation(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, 'data-is-superuser="true"')
        self.assertContains(response, "data-delete-url-template=")
        self.assertContains(response, "data-csrf-token=")

    def test_delete_project_with_post(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:delete_project", args=[self.project.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertContains(response, "Project deleted successfully!")

    def test_delete_project_rejects_get(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("main:delete_project", args=[self.project.id]),
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_delete_project_returns_404_for_unknown_id(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("main:delete_project", args=[uuid.uuid4()]),
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_create_project(self):
        create_url = reverse("main:create_project")

        response = self.client.get(create_url)

        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={create_url}',
            fetch_redirect_response=False,
        )

    def test_regular_user_cannot_access_create_project(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("main:create_project"))

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_from_update_project(self):
        update_url = reverse("main:update_project", args=[self.project.id])

        response = self.client.get(update_url)

        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={update_url}',
            fetch_redirect_response=False,
        )

    def test_regular_user_cannot_update_project(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(
            reverse("main:update_project", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_can_update_project(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("main:update_project", args=[self.project.id]),
            {
                "title": "VETO Edited",
                "role": self.project.role,
                "description": self.project.description,
                "thumbnail": self.project.thumbnail,
                "primary_link_label": self.project.primary_link_label,
                "primary_link_url": self.project.primary_link_url,
                "display_order": self.project.display_order,
            },
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "VETO Edited")

    def test_editor_cannot_create_or_delete_project(self):
        self.client.force_login(self.editor)

        create_response = self.client.get(reverse("main:create_project"))
        delete_response = self.client.post(
            reverse("main:delete_project", args=[self.project.id])
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_anonymous_user_is_redirected_from_delete_project(self):
        delete_url = reverse("main:delete_project", args=[self.project.id])

        response = self.client.post(delete_url)

        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={delete_url}',
            fetch_redirect_response=False,
        )
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_regular_user_cannot_delete_project(self):
        self.client.force_login(self.regular_user)

        response = self.client.post(
            reverse("main:delete_project", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_project_controls_are_hidden_from_non_superusers(self):
        create_url = reverse("main:create_project")

        anonymous_response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(anonymous_response, f'href="{create_url}"')
        self.assertContains(anonymous_response, 'data-can-edit="false"')
        self.assertContains(anonymous_response, 'data-is-superuser="false"')

        self.client.force_login(self.regular_user)
        regular_response = self.client.get(reverse("main:show_projects"))
        self.assertNotContains(regular_response, f'href="{create_url}"')
        self.assertContains(regular_response, 'data-can-edit="false"')
        self.assertContains(regular_response, 'data-is-superuser="false"')

    def test_editor_sees_only_project_update_control(self):
        self.client.force_login(self.editor)
        create_url = reverse("main:create_project")

        response = self.client.get(reverse("main:show_projects"))

        self.assertNotContains(response, f'href="{create_url}"')
        self.assertContains(response, 'data-can-edit="true"')
        self.assertContains(response, 'data-is-superuser="false"')

    def test_project_controls_are_visible_to_superuser(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(
            response,
            f'href="{reverse("main:create_project")}"',
        )
        self.assertContains(response, 'data-can-edit="true"')
        self.assertContains(response, 'data-is-superuser="true"')

    def test_anonymous_user_is_redirected_from_toggle_star(self):
        star_url = reverse("main:toggle_star", args=[self.project.id])

        response = self.client.post(star_url)

        self.assertRedirects(
            response,
            f'{reverse("main:login")}?next={star_url}',
            fetch_redirect_response=False,
        )
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_anonymous_user_sees_login_prompt_instead_of_star_form(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, 'data-is-authenticated="false"')
        self.assertContains(
            response,
            f'data-login-url="{reverse("main:login")}"',
        )

    def test_authenticated_star_control_uses_post_and_csrf(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, 'data-is-authenticated="true"')
        self.assertContains(response, "data-star-url-template=")
        self.assertContains(response, "data-csrf-token=")

    def test_logged_in_user_can_star_and_unstar_project(self):
        self.client.force_login(self.regular_user)
        star_url = reverse("main:toggle_star", args=[self.project.id])

        star_response = self.client.post(star_url)

        self.assertRedirects(star_response, reverse("main:show_projects"))
        self.assertTrue(self.project.starred_by.filter(pk=self.regular_user.pk).exists())
        self.assertTrue(
            self.regular_user.starred_projects.filter(pk=self.project.pk).exists()
        )

        unstar_response = self.client.post(star_url)

        self.assertRedirects(unstar_response, reverse("main:show_projects"))
        self.assertFalse(
            self.project.starred_by.filter(pk=self.regular_user.pk).exists()
        )

    def test_get_request_is_rejected_without_changing_project_star(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(
            reverse("main:toggle_star", args=[self.project.id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_editor_can_star_project(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("main:toggle_star", args=[self.project.id])
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(self.project.starred_by.filter(pk=self.editor.pk).exists())

    def test_multiple_users_can_star_the_same_project(self):
        self.project.starred_by.add(self.regular_user, self.superuser)

        self.assertEqual(self.project.starred_by.count(), 2)

    def test_projects_page_shows_star_state_and_count(self):
        self.project.starred_by.add(self.regular_user)
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("main:get_projects_json"))
        fields = json.loads(response.content)[0]["fields"]

        self.assertTrue(fields["is_starred"])
        self.assertEqual(fields["star_count"], 1)

    def test_projects_json_does_not_expose_users_who_starred(self):
        self.project.starred_by.add(self.regular_user)

        response = self.client.get(reverse("main:get_projects_json"))

        data = json.loads(response.content)
        self.assertNotIn("starred_by", data[0]["fields"])
        self.assertNotIn("password", data[0]["fields"])
        self.assertNotContains(response, self.regular_user.username)
        self.assertNotContains(response, self.regular_user.email)
