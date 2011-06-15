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

MAX_POSTS = 10

class BlogPost(models.Model):
    key = models.CharField(primary_key=True, max_length=64, default=uuid_str, editable=False)
    title = models.CharField(max_length=128)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(editable=False, default='')

    def save(self, *args, **kwargs):
        """
        For the purposes of the sandbox, limit the maximum number of stored models.
        """
        self.slug = slugify(self.title)
        super(self.__class__, self).save(*args, **kwargs)
        for obj in self.__class__.objects.order_by('-created')[MAX_POSTS:]:
            obj.delete()


class Comment(models.Model):
    blogpost = models.ForeignKey(BlogPost, editable=False, related_name='comments')
    username = models.CharField(max_length=128)
    comment = models.TextField()
    rating = models.IntegerField(blank=True, null=True, choices=RATING_CHOICES, help_text='How did you rate this post?')
    created = models.DateTimeField(auto_now_add=True)

