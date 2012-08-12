from django.db import models
import zlib, base64

class Project(models.Model):
    name = models.TextField(primary_key = True)
    excluded_checkers = models.TextField(help_text = 'Excluded checkers for all units in project (comma separated)')

class Unit(models.Model):
    filename = models.TextField(help_text = 'Filename extracted from report')
    raw = models.XMLField(help_text = 'Raw XML of report')
    project = models.ForeignKey(Project)
    date = models.DateTimeField(auto_now_add = True, help_text = 'Time of report')
    reporter = models.TextField(help_text = 'Network address of reporting compiler')
    excluded_checkers = models.TextField(help_text = 'Excluded checkers for this unit (comma separated)')
    

class Annotation(models.Model):
    SEVERITY_INFO = 0
    SEVERITY_WARNING = 10
    SEVERITY_ERROR = 20

    SEVERITIES = (
      (SEVERITY_INFO,    'Information'),
      (SEVERITY_WARNING, 'Warning'),
      (SEVERITY_ERROR,   'Error'),
    )
    
    unit = models.ForeignKey(Unit)
    lineno = models.IntegerField(help_text = 'Line of annotation')
    column = models.IntegerField(help_text = 'Column of annotation (0 = whole line, 1 = first column)')
    severity = models.PositiveSmallIntegerField(help_text = 'Filename extracted from report', choices = SEVERITIES)
    note = models.TextField(help_text = 'Short note')
    text = models.TextField(help_text = 'Long explanation')
    tag = models.TextField(help_text = 'Checker-specific code')
    checker = models.TextField(help_text = 'Name of checker')
    