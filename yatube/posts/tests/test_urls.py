
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.user2 = User.objects.create_user(username='not_auth')
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group
        )

        id = self.post.id

        self.REDIRECT_LOGIN_CREATE = '/auth/login/?next=/create/'
        self.REDIRECT_LOGIN_EDIT = f'/auth/login/?next=/posts/{id}/edit/'
        self.REDIRECT_POST_DETAIL = f'/posts/{id}/'
        self.REDIRECT_LOGIN_FOLLOW = '/auth/login/?next=/follow/'

    def test_urls_for_unauthorised_users(self):
        page_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user.username}/follow/': HTTPStatus.FOUND,
            f'posts/{self.post.id}/comment/': HTTPStatus.NOT_FOUND,
        }
        for page, expected_status in page_url_names.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page).status_code
                self.assertEqual(response, expected_status)

    def test_create_url_exists_at_desired_location(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_exists_at_desired_location(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        cache.clear()
        templates_url_names = {
            'posts/index.html': '/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/create_post.html': '/create/',
            'posts/follow.html': '/follow/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_edit_url_uses_correct_template(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_urls_redirect(self):
        client_url_redirect = [
            [self.guest_client, reverse(
                'posts:post_create'), self.REDIRECT_LOGIN_CREATE],
            [self.guest_client, f'/posts/{self.post.id}/edit/',
             self.REDIRECT_LOGIN_EDIT],
            [self.authorized_client2, f'/posts/{self.post.id}/edit/',
             self.REDIRECT_POST_DETAIL],
            [self.guest_client, reverse(
                'posts:follow_index'), self.REDIRECT_LOGIN_FOLLOW],
            [self.authorized_client2, reverse('posts:add_comment',
                                              kwargs={'post_id': self.post.id}
                                              ), reverse('posts:post_detail',
                                                         args=[self.post.pk])]
        ]
        for client, url, redirect_url in client_url_redirect:
            with self.subTest(url=url):
                self.assertRedirects(
                    client.get(url, follow=True), redirect_url)
