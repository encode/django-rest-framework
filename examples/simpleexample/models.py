from django.db import models

MAX_INSTANCES = 10

class MyModel(models.Model):
    foo = models.BooleanField()
    bar = models.IntegerField(help_text='Must be an integer.')
    baz = models.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('created',)

    def save(self, *args, **kwargs):
        """For the purposes of the sandbox, limit the maximum number of stored models."""
        super(MyModel, self).save(*args, **kwargs)
        while MyModel.objects.all().count() > MAX_INSTANCES:
            MyModel.objects.all()[0].delete()
    
    @models.permalink
    def get_absolute_url(self):
        return ('simpleexample.views.MyModelResource', (self.pk,))

