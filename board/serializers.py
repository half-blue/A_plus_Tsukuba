from rest_framework import serializers
from .models import Post, Reply, Subject, Review

class GetPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post                   
        fields = ["post_id","sender_name","text","created_at","emotion"]  

class GetReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply                   
        fields = ["reply_id","sender_name","text","created_at","emotion"]  

class SearchSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject                   
        fields = ["code","name","teachers","subtype","schools","colleges","thread_id"]  

class PostPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post                   
        fields = ["post_id","sender_name","text","created_at","emotion", "thread", "allow_tweet"]  
        read_only_fields = ('post_id',"created_at")

class PostReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply                   
        fields = ["reply_id","sender_name","text","created_at","emotion","post_id"]
        read_only_fields = ('reply_id',"created_at") 

class GetSubjectScoresSerializer(serializers.Serializer):
      subcode = serializers.CharField(max_length=128)
      average_ratings_overall = serializers.FloatField()
      average_ratings_easiness = serializers.FloatField()
      average_ratings_content = serializers.FloatField()
      count_ratings = serializers.IntegerField()
