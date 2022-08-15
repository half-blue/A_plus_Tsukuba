from rest_framework import serializers
from .models import Post, Reply

class GetPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post                   
        fields = ["post_id","sender_name","text","created_at","emotion"]  

class GetReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply                   
        fields = ["reply_id","sender_name","text","created_at","emotion"]  

class PostPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post                   
        fields = ["post_id","sender_name","text","created_at","emotion", "thread"]  
        read_only_fields = ('post_id',"created_at")

class PostReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply                   
        fields = ["reply_id","sender_name","text","created_at","emotion","post_id"]
        read_only_fields = ('reply_id',"created_at") 