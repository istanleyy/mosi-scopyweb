from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Machine(models.Model):
    BAG_MODE = 'B'
    QUEUE_MODE = 'Q'
    JOB_MODE_CHOICES = (
        (BAG_MODE, 'Bag'),
        (QUEUE_MODE, 'Queue'),
    )
    name = models.CharField(max_length=25)
    type = models.CharField(max_length=10)
    ipaddress = models.CharField(max_length=15)
    queuemode = models.CharField(max_length=1,
                                    choices=JOB_MODE_CHOICES,
                                    default=BAG_MODE)
    ownership = models.CharField(max_length=10)
    description = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name

@python_2_unicode_compatible    
class Job(models.Model):
    jobid = models.IntegerField(default=0)
    productid = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    ct = models.IntegerField(default=0)
    multiplier = models.IntegerField(default=1)
    moldid = models.CharField(max_length=50)
    urgent = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.productid

class ProductionDataTS(models.Model):
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    eventtime = models.DateTimeField(auto_now_add=True)
    output = models.IntegerField(default=0)
    mct = models.IntegerField(default=0)
    
    def __str__(self):
        return self.eventtime

class SessionManagement(models.Model):
    modified = models.DateField(auto_now=True)
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    msgid = models.IntegerField(default=0)