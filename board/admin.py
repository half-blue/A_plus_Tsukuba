from django.contrib import admin
from .models import Post, Thread, Reply, Subject, Notice
# Register your models here.

admin.site.register(Post)
admin.site.register(Thread)
admin.site.register(Reply)
admin.site.register(Subject)
admin.site.register(Notice)