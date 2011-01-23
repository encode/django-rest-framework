from django.db import models
from django.template.defaultfilters import slugify
import uuid

def uuid_str():
    return str(uuid.uuid1())


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
        return ('blogpost.views.BlogPostInstance', (), {'key': self.key})

    @property
    @models.permalink
    def comments_url(self):
        """Link to a resource which lists all comments for this blog post."""
        return ('blogpost.views.CommentList', (), {'blogpost_id': self.key})

    @property
    @models.permalink
    def comment_url(self):
        """Link to a resource which can create a comment for this blog post."""
        return ('blogpost.views.CommentCreator', (), {'blogpost_id': self.key})

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
        return ('blogpost.views.CommentInstance', (), {'blogpost': self.blogpost.key, 'id': self.id})
    
    @property
    @models.permalink
    def blogpost_url(self):
        """Link to the blog post resource which this comment corresponds to."""
        return ('blogpost.views.BlogPostInstance', (), {'key': self.blogpost.key})
        
