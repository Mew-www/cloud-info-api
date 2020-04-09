from django.urls import path
from azure.views import *

urlpatterns = [
    path('catalog/', catalog_view),
    path('cert/<str:cert_uid>', cert_details_view),
    path('exam/<str:exam_uid>', exam_details_view),
]
