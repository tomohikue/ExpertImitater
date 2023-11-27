"""
Definition of models.
"""

from django.db import models
from pgvector.django import VectorField

# Create your models here.
class ChatHistoryModel(models.Model):
    id = models.IntegerField(primary_key=True)
    userid = models.CharField(max_length=100)
    functionid = models.CharField(max_length=100)
    content = models.CharField(max_length=20000)
    timestamp = models.DateTimeField(auto_now_add=True)
    
class DocumentVectorDataModel(models.Model):
    id = models.UUIDField(primary_key=True)
    document_filename = models.CharField(max_length=300)
    page_no = models.CharField(max_length=10)
    embedding = VectorField(dimensions=1536)
    embeddingtext = models.CharField(max_length=20000, null=True)
    origntext = models.CharField(max_length=20000)
    create_timestamp = models.DateTimeField(auto_now_add=True)

class DocumentFileNameVectorData(models.Model):
    document_filename = models.CharField(max_length=300,primary_key=True)
    document_name = models.CharField(max_length=300,unique=True)
    total_page_no = models.CharField(max_length=10, null=True)
    discription = models.CharField(max_length=500, null=True)
    document_url = models.CharField(max_length=3000, null=True)
    create_timestamp = models.DateTimeField(auto_now_add=True)