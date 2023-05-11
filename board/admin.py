from django.contrib import admin
from .models import Post, Thread, Reply, Subject, Notice, Review, Tag
# Register your models here.

class PostModelAdmin(admin.ModelAdmin):
    list_display = ('sender_name','emotion','created_at')
    ordering = ('-created_at',)
    list_filter = ('emotion',)

class ReplyModelAdmin(admin.ModelAdmin):
    list_display = ('sender_name','emotion','created_at')
    ordering = ('-created_at',)
    list_filter = ('emotion',)

class ThreadModelAdmin(admin.ModelAdmin):
    search_fields = ['title']

class SubjectModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'teachers', 'schools', 'colleges', 'year')
    list_display_links = ('code', 'name')
    list_filter = ('schools', 'colleges', 'year')
    search_fields = ['code', 'name', 'teachers']

class ReviewModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'ratings_overall', 'ratings_easiness', 'ratings_content', 'created_at')
    list_filter = ('subject',)
    search_fields = ('comment', 'tags__name')
    filter_horizontal = ('tags',)

class TagModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

admin.site.register(Post, PostModelAdmin)
admin.site.register(Thread, ThreadModelAdmin)
admin.site.register(Reply, ReplyModelAdmin)
admin.site.register(Subject, SubjectModelAdmin)
admin.site.register(Notice)
admin.site.register(Review, ReviewModelAdmin)
admin.site.register(Tag, TagModelAdmin)
