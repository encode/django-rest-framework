from django.db import models
from django.template.defaultfilters import slugify
from datetime import datetime
import uuid

def uuid_str():
    return str(uuid.uuid1())

class ExampleModel(models.Model):
    num = models.IntegerField(default=2, choices=((1,'one'), (2, 'two')))
    hidden_num = models.IntegerField(verbose_name='Something', help_text='HELP')
    text = models.TextField(blank=False)
    another = models.CharField(max_length=10)


class ExampleContainer(models.Model):
    """Container.  Has a key, a name, and some internal data, and contains a set of items."""
    key = models.CharField(primary_key=True, default=uuid_str, max_length=36, editable=False)
    name = models.CharField(max_length=256)
    internal = models.IntegerField(default=0)

    @models.permalink
    def get_absolute_url(self):
        return ('testapp.views.ContainerInstance', [self.key])


class ExampleItem(models.Model):
    """Item.  Belongs to a container and has an index number and a note.
    Items are uniquely identified by their container and index number."""
    container = models.ForeignKey(ExampleContainer, related_name='items')
    index = models.IntegerField()
    note = models.CharField(max_length=1024)
    unique_together = (container, index)


class BlogPost(models.Model):
    slug = models.SlugField(editable=False, primary_key=True, default='blah')
    title = models.CharField(max_length=128)
    content = models.TextField()
    when = models.DateTimeField(editable=False)

    @models.permalink
    def get_absolute_url(self):
        return ('testapp.views.BlogPostInstance', (self.slug,))

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        self.when = datetime.now()
        super(self.__class__, self).save(*args, **kwargs)


class Comment(models.Model):
    blogpost = models.ForeignKey(BlogPost, related_name='comments')
    name = models.CharField(max_length=128)
    content = models.TextField()
    when = models.DateTimeField(auto_now_add=True)

    @models.permalink
    def get_absolute_url(self):
        return ('testapp.views.CommentInstance', (self.blogpost.slug, self.id))
   
    def save(self):
        self.index = self.blogpost.comments.count()