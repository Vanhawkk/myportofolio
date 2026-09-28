from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from main.permissions import editor_or_superuser_required, superuser_required


class PortfolioAuthorizationDecoratorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.regular_user = User.objects.create_user(username="regular-user")
        self.editor = User.objects.create_user(username="editor")
        self.superuser = User.objects.create_superuser(
            username="portfolio-owner",
            email="owner@example.com",
            password="StrongPassword123!",
        )

        editor_group = Group.objects.create(name="Editor")
        editor_group.permissions.add(
            Permission.objects.get(
                content_type__app_label="main",
                codename="change_project",
            )
        )
        self.editor.groups.add(editor_group)

    @staticmethod
    def protected_view(request):
        return HttpResponse("allowed")

    def request_for(self, user):
        request = self.factory.get("/protected/")
        request.user = user
        return request

    def test_superuser_required_redirects_anonymous_user_to_login(self):
        decorated_view = superuser_required(self.protected_view)

        response = decorated_view(self.request_for(AnonymousUser()))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/?next=/protected/")

    def test_superuser_required_rejects_authenticated_non_superuser(self):
        decorated_view = superuser_required(self.protected_view)

        with self.assertRaises(PermissionDenied):
            decorated_view(self.request_for(self.regular_user))

    def test_superuser_required_allows_superuser(self):
        decorated_view = superuser_required(self.protected_view)

        response = decorated_view(self.request_for(self.superuser))

        self.assertEqual(response.status_code, 200)

    def test_editor_permission_redirects_anonymous_user_to_login(self):
        decorated_view = editor_or_superuser_required(
            "main.change_project"
        )(self.protected_view)

        response = decorated_view(self.request_for(AnonymousUser()))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/?next=/protected/")

    def test_editor_permission_rejects_regular_user(self):
        decorated_view = editor_or_superuser_required(
            "main.change_project"
        )(self.protected_view)

        with self.assertRaises(PermissionDenied):
            decorated_view(self.request_for(self.regular_user))

    def test_editor_permission_allows_editor_with_matching_permission(self):
        decorated_view = editor_or_superuser_required(
            "main.change_project"
        )(self.protected_view)

        response = decorated_view(self.request_for(self.editor))

        self.assertEqual(response.status_code, 200)

    def test_editor_permission_is_scoped_to_requested_model(self):
        decorated_view = editor_or_superuser_required(
            "main.change_experience"
        )(self.protected_view)

        with self.assertRaises(PermissionDenied):
            decorated_view(self.request_for(self.editor))

    def test_editor_permission_allows_superuser(self):
        decorated_view = editor_or_superuser_required(
            "main.change_project"
        )(self.protected_view)

        response = decorated_view(self.request_for(self.superuser))

        self.assertEqual(response.status_code, 200)
