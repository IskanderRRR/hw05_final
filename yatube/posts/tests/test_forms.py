import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Test text',
            group=self.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_with_picture(self):
        posts_count = Post.objects.count()
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test.jpg',
            content=image,
            content_type='image/jpg'
        )
        form_data = {
            'text': 'Test post with image',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()

        self.assertEqual(post.image, 'posts/test.jpg',)
        
    def test_create_group_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Another test',
            'group': self.group.id,
            'author_id': self.user.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.author_id, form_data['author_id'])

    def test_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста с группой',
            'group': self.group.id,
            'author_id': self.user.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        post = Post.objects.filter(id=self.post.id).first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.author_id, form_data['author_id'])
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post_by_guest(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Post from unauthorized client',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        create_url = reverse('posts:post_create')
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_by_guest(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Edited post from unauthorized client',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edit_url = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={edit_url}')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.text, self.post.text)
        self.assertNotEqual(self.post.text, form_data['text'])

    def test_add_comments_by_guest(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Comment from guest client',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        )
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={comment_url}')
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_add_comments_by_authorized_user(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Writing comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        # Comment will appear in the page for post detail
        last_comment = response.context['comments'][0]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.post.id, self.post.id)
