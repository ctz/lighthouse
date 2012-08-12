from django.conf.urls.defaults import *
import localsettings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^m/(?P<path>.*)$', 'django.views.static.serve', dict(document_root = localsettings.ROOT + '/media', show_indexes = 1)),
    (r'^$',     'lha.views.index'),
    (r'^projects$',     'lha.views.projects'),
    (r'^backend$',     'lha.views.backend'),
)
