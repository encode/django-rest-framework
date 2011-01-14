from django.db import models
from django.template.defaultfilters import slugify
import uuid

def uuid_str():
    return str(uuid.uuid1())

#class ExampleModel(models.Model):
#    num = models.IntegerField(default=2, choices=((1,'one'), (2, 'two')))
#    hidden_num = models.IntegerField(verbose_name='Something', help_text='HELP')
#    text = models.TextField(blank=False)
#    another = models.CharField(max_length=10)


#class ExampleContainer(models.Model):
#    """Container.  Has a key, a name, and some internal data, and contains a set of items."""
#    key = models.CharField(primary_key=True, default=uuid_str, max_length=36, editable=False)
#    name = models.CharField(max_length=256)
#    internal = models.IntegerField(default=0)

#    @models.permalink
#    def get_absolute_url(self):
#        return ('testapp.views.ContainerInstance', [self.key])


#class ExampleItem(models.Model):
#    """Item.  Belongs to a container and has an index number and a note.
#    Items are uniquely identified by their container and index number."""
#    container = models.ForeignKey(ExampleContainer, related_name='items')
#    index = models.IntegerField()
#    note = models.CharField(max_length=1024)
#    unique_together = (container, index)


RATING_CHOICES = ((0, 'Awful'),
                  (1, 'Poor'),
                  (2, 'OK'),
                  (3, 'Good'),
                  (4, 'Excellent'))

class BlogPost(models.Model):
    key = models.CharField(primary_key=True, max_length=64, default=uuid_str, editable=False)
    title = models.CharField(max_length=128)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(editable=False, default='')

    class Meta:
        ordering = ('created',)

    @models.permalink
    def get_absolute_url(self):
        return ('testapp.views.BlogPostInstance', (self.key,))

    @property
    @models.permalink
    def comments_url(self):
        """Link to a resource which lists all comments for this blog post."""
        return ('testapp.views.CommentList', (self.key,))

    @property
    @models.permalink
    def comment_url(self):
        """Link to a resource which can create a comment for this blog post."""
        return ('testapp.views.CommentCreator', (self.key,))

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(self.__class__, self).save(*args, **kwargs)


class Comment(models.Model):
    blogpost = models.ForeignKey(BlogPost, editable=False, related_name='comments')
    username = models.CharField(max_length=128)
    comment = models.TextField()
    rating = models.IntegerField(blank=True, null=True, choices=RATING_CHOICES, help_text='How did you rate this post?')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created',)

    @models.permalink
    def get_absolute_url(self):
        return ('testapp.views.CommentInstance', (self.blogpost.key, self.id))
    
    @property
    @models.permalink
    def blogpost_url(self):
        """Link to the blog post resource which this comment corresponds to."""
        return ('testapp.views.BlogPostInstance', (self.blogpost.key,))
        
