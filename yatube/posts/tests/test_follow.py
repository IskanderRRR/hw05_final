from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post

User = get_user_model()


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.user = User.objects.create_user(username='auth')
        self.post = Post.objects.create(
            author=self.user,
            text='Test text',
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def setUp(self):
        self.user = User.objects.create_user(username='authFollower')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_autorized_user_can_follow(self):
        follow_count = Follow.objects.count()
        author = FollowViewsTests.user
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_autorized_user_can_unfollow(self):
        author = FollowViewsTests.user
        Follow.objects.create(user=self.user, author=author)
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_unfollow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_autorized_user_can_follow_once(self):
        follow_count = Follow.objects.count()
        author = FollowViewsTests.user
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists())
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': author.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=author
        ).exists())

    def test_autorized_user_cant_follow_yourself(self):
        follow_count = Follow.objects.count()
        response = (self.authorized_client.
                    get(reverse('posts:profile_follow',
                        kwargs={'username': self.user.username})))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.user
        ).exists())

    def test_follow_index(self):
        author = FollowViewsTests.user
        self.authorized_client.get(reverse('posts:profile_follow',
                                   kwargs={'username': author.username}))
        response = (self.authorized_client.get(reverse('posts:follow_index')))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.id, self.post.id)
        self.authorized_client.get(reverse('posts:profile_unfollow',
                                   kwargs={'username': author.username}))
        response = (self.authorized_client.get(reverse('posts:follow_index')))
        self.assertNotContains(response, self.post.text)
    