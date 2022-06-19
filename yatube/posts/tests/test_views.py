import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POSTS_PER_PAGE = settings.POSTS_PER_PAGE

TESTING_ATTEMPTS = 13
OTHER_GROUP_SLUG = 'other-test-group'
OTHER_GROUP_URL = reverse('posts:group_posts', args=[OTHER_GROUP_SLUG])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Test description',
        )
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
        self.post = Post.objects.create(
            text='Test text',
            author=self.user,
            group=self.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        cache.clear()
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_pages_uses_correct_template(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_group_list_page_show_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:group_posts',
                        kwargs={'slug': self.group.slug})))
        group = response.context['group']
        self.assertEqual(group, Group.objects.get(slug=self.group.slug))

    def test_profile_page_show_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                        kwargs={'username': self.user.username})))
        author = response.context['author']
        post_count = response.context['post_count']
        self.assertEqual(author, User.objects.get(username=self.user.username))
        self.assertEqual(post_count, Post.objects.filter(
            author__username=self.user.username
        ).count())

    def test_post_detail_pages_show_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        post_count = response.context['post_count']
        self.assertEqual(post, Post.objects.get(id=self.post.id))
        self.assertEqual(post_count, 1)

    def test_create_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context.get('is_edit')
        self.assertEqual(is_edit, False)

    def test_post_edit_pages_show_correct_context(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        self.assertEqual(post, Post.objects.get(id=self.post.id))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context.get('is_edit')
        self.assertEqual(is_edit, True)

    def test_post_show_correct_text(self):
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): self.post.text,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): self.post.text,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.text,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, expected)

    def test_post_show_correct_post_id(self):
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): self.post.id,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): self.post.id,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.id,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.id, expected)

    def test_new_post_do_not_view_other_group(self):
        Group.objects.create(
            title='Другой заголовок',
            slug=OTHER_GROUP_SLUG,
            description='Другое тестовое описание',
        )
        response = self.authorized_client.get(OTHER_GROUP_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_show_picture(self):
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): self.post.image,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): self.post.image,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}): self.post.image,
        }
        for value, expected in templates_pages_names.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.image, expected)

    def test_post_show_picture_in_post(self):
        response = (self.authorized_client.
                    get(reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})))
        post = response.context['post']
        self.assertEqual(post.image, self.post.image)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.user = User.objects.create_user(username='TestUser2')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Test group_2',
            slug='test-slug_2',
            description='Test description_2',
        )
        self.post = Post.objects.bulk_create(
            [
                Post(
                    text='Testing paginator',
                    author=self.user,
                    group=self.group,
                ),
            ] * TESTING_ATTEMPTS
        )

    def test_first_page_contains_ten_records(self):
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): settings.POSTS_PER_PAGE,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}):
            settings.POSTS_PER_PAGE,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            settings.POSTS_PER_PAGE,
        }
        for reverse_template, expected in templates_pages_names.items():
            with self.subTest(reverse_template=reverse_template):
                response = self.client.get(reverse_template)
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_contains_three_records(self):
        second_page_posts = TESTING_ATTEMPTS % POSTS_PER_PAGE
        templates_pages_names = {
            reverse('posts:index'): second_page_posts,
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): second_page_posts,
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
            second_page_posts,
        }
        for reverse_template, expected in templates_pages_names.items():
            with self.subTest(reverse_template=reverse_template):
                response = self.client.get(reverse_template + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)
