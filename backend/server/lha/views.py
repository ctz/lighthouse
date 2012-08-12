
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
import lhpath
import lighthouse.input
import localsettings
import codepresentation
from models import *

def index(req):
    tu = lighthouse.input.parse(localsettings.ROOT + '/../dddstest.c.lh')
    lines = codepresentation.format_source(tu)
    for f in tu.functions:
        f.cyclomatic_complexity()
    return render_to_response('index.html', dict(lines = lines))

def projects(req):
    resp = HttpResponse()
    for p in Project.objects.all():
        print >>resp, p.name, '  ', len(Unit.objects.filter(project = p))
    return resp

def backend(req):
    if req.method != 'POST' or 'xml' not in req.FILES:
        return HttpResponseBadRequest('Only post with "xml" file allowed.')
    for x in ('project',):
        if x not in req.POST:
            return HttpResponseBadRequest('Missing %s' % x)
    
    project = Project(name = req.POST['project'])
    project.save()
    unit = Unit(raw = req.FILES['xml'].read(), project = project, reporter = req.get_host())
    unit.save()
    return HttpResponse('ok')
    