from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Users, Profile


# Create your tests here.


class BaseAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_data = {'username': 'email', "first_name": "email", "last_name": "email"}
        self.profile = Profile.objects.create(username='email', first_name="email", last_name="email")
        self.user = Users.objects.create(email='email@email.com', phone='900000000', profile=self.profile,
                                         is_active=True)
        self.user.set_password("1")
        self.user.save()
        self.admin_profile = Profile.objects.create(username='admin', first_name="admin", last_name="admin")
        self.admin = Users.objects.create_superuser(email='admin@email.com', phone='911111111', profile=self.admin_profile)
        self.user.set_password("1")
        self.user.save()


class UsersListApiViewTestCase(BaseAPITestCase):
    def test_users_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('auth-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_users_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('auth-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_anonym(self):
        url = reverse('auth-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])



class RegisterApiViewTestCase(BaseAPITestCase):
    def test_register_success(self):
        url=reverse('auth-register')
        payload={
            'email':'test@email.com',
            'phone':'910000000',
            'password':'1',
            'profile':{
                "first_name":"test",
                "last_name":"test",
                "username":"test"
            }
        }
        response = self.client.post(url,payload,format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(Users.objects.filter(email='test@email.com').exists())

    def test_register_duplicate_phone_fails(self):
        url = reverse("auth-register")
        payload = {
            "email": "another@example.com",
            "phone": self.user.phone,  # allaqachon mavjud telefon
            "password": "NewPass123",
            "profile": {
                "username": "another",
                "first_name": "Another",
                "last_name": "User",
            },
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class LoginApiViewTestCase(BaseAPITestCase):
    def test_login_success(self):
        url=reverse('auth-login')
        payload={'email':'email@email.com',
                 'password':"1"
        }
        response=self.client.post(url,payload,format='json')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertIn("access",response.data)
        self.assertIn("refresh",response.data)
