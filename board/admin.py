from django.contrib import admin
from .models import Post, Thread, Reply, Subject, Notice
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
    list_display = ('code', 'name', 'teachers', 'schools', 'colleges')
    list_display_links = ('code', 'name')
    list_filter = ('schools', 'colleges')
    search_fields = ['code', 'name', 'teachers']

admin.site.register(Post, PostModelAdmin)
admin.site.register(Thread, ThreadModelAdmin)
admin.site.register(Reply, ReplyModelAdmin)
admin.site.register(Subject, SubjectModelAdmin)
admin.site.register(Notice)