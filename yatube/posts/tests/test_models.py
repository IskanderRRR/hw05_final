from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    def test_group_name_is_group_title(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_post_name_is_correct(self):
        post = PostModelTest.post
        expected_object_name = post.text
        self.assertEqual(expected_object_name, str(post))
