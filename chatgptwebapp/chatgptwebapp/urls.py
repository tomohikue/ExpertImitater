"""
Definition of urls for chatgptwebapp.
"""

from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views
from rest_framework_swagger.views import get_swagger_view

### Swagger ###
schema_view = get_swagger_view(title='API')

urlpatterns = [
    path('', views.chatui, name='chatui'),
    path('chat', views.chat, name='chat'),
    path('getid', views.getid, name='getid'),
    path('documentsearch', views.documentsearch, name='documentsearch'), # type: ignore
    path('getlist_of_registered_document', views.getlist_of_registered_document, name='getlist_of_registered_document'),    
    path('document_upload_save', views.document_upload_save, name='document_upload_save'),
    path('conv_save2db', views.conv_save2db, name='conv_save2db'),
    path('code_interpreter', views.code_interpreter, name='code_interpreter'), # type: ignore
    path('code_interpreter_sql', views.code_interpreter_sql, name='code_interpreter_sql'), # type: ignore
    path('code_interpreter_upload_csv', views.code_interpreter_upload_csv, name='code_interpreter_upload_csv'), # type: ignore
    path('code_interpreter_sql_get_tablelayout', views.code_interpreter_sql_get_tablelayout, name='code_interpreter_sql_get_tablelayout'), # type: ignore
    path('login/',
         LoginView.as_view
         (
             template_name='app/login.html',
             authentication_form=forms.BootstrapAuthenticationForm,
             extra_context=
             {
                 'title': 'Log in',
                 'year' : datetime.now().year,
             }
         ),
         name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view),
]
