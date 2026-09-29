from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse

from main.models import Experience, Project


class PortfolioAuthorizationMatrixTest(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(username="regular-user")
        self.editor = User.objects.create_user(username="editor")
        self.superuser = User.objects.create_superuser(
            username="portfolio-owner",
            email="owner@example.com",
            password="StrongPassword123!",
        )

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(
            *Permission.objects.filter(
                content_type__app_label="main",
                codename__in=("change_experience", "change_project"),
            )
        )
        self.editor.groups.add(editor_group)

        self.experience = Experience.objects.create(
            title="Existing Experience",
            description="An existing portfolio experience.",
            category="part-time",
        )
        self.project = Project.objects.create(
            title="Existing Project",
            role="Developer",
            description="An existing portfolio project.",
            thumbnail="/static/img/project-veto.jpg",
            display_order=1,
        )

    def experience_payload(self, title):
        return {
            "title": title,
            "description": "Updated experience description.",
            "category": "part-time",
            "thumbnail": "",
        }

    def project_payload(self, title):
        return {
            "title": title,
            "role": "Developer",
            "description": "Updated project description.",
            "thumbnail": "/static/img/project-veto.jpg",
            "display_order": 1,
        }

    def mutation_urls(self):
        return {
            "create_experience": reverse("main:create_experience"),
            "update_experience": reverse(
                "main:update_experience",
                args=[self.experience.id],
            ),
            "delete_experience": reverse(
                "main:delete_experience",
                args=[self.experience.id],
            ),
            "create_project": reverse("main:create_project"),
            "update_project": reverse(
                "main:update_project",
                args=[self.project.id],
            ),
            "delete_project": reverse(
                "main:delete_project",
                args=[self.project.id],
            ),
        }

    def post_all_mutations(self):
        urls = self.mutation_urls()
        return {
            "create_experience": self.client.post(
                urls["create_experience"],
                self.experience_payload("Created Experience"),
            ),
            "update_experience": self.client.post(
                urls["update_experience"],
                self.experience_payload("Updated Experience"),
            ),
            "delete_experience": self.client.post(urls["delete_experience"]),
            "create_project": self.client.post(
                urls["create_project"],
                self.project_payload("Created Project"),
            ),
            "update_project": self.client.post(
                urls["update_project"],
                self.project_payload("Updated Project"),
            ),
            "delete_project": self.client.post(urls["delete_project"]),
        }

    def assert_original_portfolio_data_is_unchanged(self):
        self.experience.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.experience.title, "Existing Experience")
        self.assertEqual(self.project.title, "Existing Project")
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(Project.objects.count(), 1)

    def test_read_pages_and_json_are_public_for_every_role(self):
        read_urls = (
            reverse("main:show_experience"),
            reverse("main:show_projects"),
            reverse("main:get_experiences_json"),
            reverse("main:get_projects_json"),
        )
        roles = (None, self.regular_user, self.editor, self.superuser)

        for user in roles:
            self.client.logout()
            if user is not None:
                self.client.force_login(user)

            for url in read_urls:
                with self.subTest(user=user, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_guest_mutations_redirect_to_login_without_changing_data(self):
        responses = self.post_all_mutations()
        urls = self.mutation_urls()

        for action, response in responses.items():
            with self.subTest(action=action):
                self.assertRedirects(
                    response,
                    f"{reverse('main:login')}?next={urls[action]}",
                    fetch_redirect_response=False,
                )

        self.assert_original_portfolio_data_is_unchanged()

    def test_regular_user_mutations_return_forbidden_without_changing_data(self):
        self.client.force_login(self.regular_user)

        responses = self.post_all_mutations()

        for action, response in responses.items():
            with self.subTest(action=action):
                self.assertEqual(response.status_code, 403)

        self.assert_original_portfolio_data_is_unchanged()

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.client.force_login(self.editor)
        urls = self.mutation_urls()

        create_experience = self.client.post(
            urls["create_experience"],
            self.experience_payload("Created Experience"),
        )
        create_project = self.client.post(
            urls["create_project"],
            self.project_payload("Created Project"),
        )
        update_experience = self.client.post(
            urls["update_experience"],
            self.experience_payload("Editor Updated Experience"),
        )
        update_project = self.client.post(
            urls["update_project"],
            self.project_payload("Editor Updated Project"),
        )
        delete_experience = self.client.post(urls["delete_experience"])
        delete_project = self.client.post(urls["delete_project"])

        self.assertEqual(create_experience.status_code, 403)
        self.assertEqual(create_project.status_code, 403)
        self.assertRedirects(update_experience, reverse("main:show_experience"))
        self.assertRedirects(update_project, reverse("main:show_projects"))
        self.assertEqual(delete_experience.status_code, 403)
        self.assertEqual(delete_project.status_code, 403)

        self.experience.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.experience.title, "Editor Updated Experience")
        self.assertEqual(self.project.title, "Editor Updated Project")
        self.assertEqual(Experience.objects.count(), 1)
        self.assertEqual(Project.objects.count(), 1)

    def test_superuser_can_create_update_and_delete_portfolio_data(self):
        self.client.force_login(self.superuser)
        urls = self.mutation_urls()

        create_experience = self.client.post(
            urls["create_experience"],
            self.experience_payload("Created Experience"),
        )
        create_project = self.client.post(
            urls["create_project"],
            self.project_payload("Created Project"),
        )
        update_experience = self.client.post(
            urls["update_experience"],
            self.experience_payload("Owner Updated Experience"),
        )
        update_project = self.client.post(
            urls["update_project"],
            self.project_payload("Owner Updated Project"),
        )
        delete_experience = self.client.post(urls["delete_experience"])
        delete_project = self.client.post(urls["delete_project"])

        self.assertRedirects(create_experience, reverse("main:show_experience"))
        self.assertRedirects(create_project, reverse("main:show_projects"))
        self.assertRedirects(update_experience, reverse("main:show_experience"))
        self.assertRedirects(update_project, reverse("main:show_projects"))
        self.assertRedirects(delete_experience, reverse("main:show_experience"))
        self.assertRedirects(delete_project, reverse("main:show_projects"))
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertTrue(
            Experience.objects.filter(title="Created Experience").exists()
        )
        self.assertTrue(Project.objects.filter(title="Created Project").exists())

    def test_only_authenticated_roles_can_toggle_project_star(self):
        star_url = reverse("main:toggle_star", args=[self.project.id])

        anonymous_response = self.client.post(star_url)
        self.assertRedirects(
            anonymous_response,
            f"{reverse('main:login')}?next={star_url}",
            fetch_redirect_response=False,
        )

        for user in (self.regular_user, self.editor, self.superuser):
            self.client.force_login(user)
            response = self.client.post(star_url)

            with self.subTest(user=user):
                self.assertRedirects(response, reverse("main:show_projects"))
                self.assertTrue(
                    self.project.starred_by.filter(pk=user.pk).exists()
                )

        self.assertEqual(self.project.starred_by.count(), 3)
