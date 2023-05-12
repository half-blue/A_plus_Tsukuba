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

@admin.action(description="選択したthreadのレビュー機能を無効化する")
def disable_review(modeladmin, request, queryset):
    queryset.update(enable_review=False)

@admin.action(description="選択したthreadのレビュー機能を有効化する")
def enable_review(modeladmin, request, queryset):
    queryset.update(enable_review=True)

class ThreadModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'enable_review')
    search_fields = ['title',]
    list_filter = ('enable_review',)
    actions = [disable_review, enable_review]

class SubjectModelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'teachers', 'schools', 'colleges', 'year')
    list_display_links = ('code', 'name')
    list_filter = ('schools', 'colleges', 'year')
    search_fields = ['code', 'name', 'teachers']

class ReviewModelAdmin(admin.ModelAdmin):
    list_display = ('thread', 'ratings_overall', 'ratings_easiness', 'ratings_content', 'comment','created_at')
    search_fields = ('thread__title', 'comment')
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
