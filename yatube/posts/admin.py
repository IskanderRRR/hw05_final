from django.contrib import admin

from .models import Comment, Follow, Group, Post

CONS = '-пусто-'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = CONS


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = (
        'pk',
        'title',
        'description',
    )
    empty_value_display = CONS


admin.site.register(Follow)
admin.site.register(Comment)
