from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
        )

    def test_cache_index_page(self):
        first_view = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Changed text'
        post_1.save()
        second_view = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_view.content, second_view.content)
        cache.clear()
        third_view = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_view.content, third_view.content)
