from django.dispatch import Signal

pre_create = Signal(providing_args=['request'])
post_create = Signal(providing_args=['request', 'response'])
pre_read = Signal(providing_args=['request'])
post_read = Signal(providing_args=['request', 'response'])
pre_update = Signal(providing_args=['request'])
post_update = Signal(providing_args=['request', 'response'])
pre_destroy = Signal(providing_args=['request'])
post_destroy = Signal(providing_args=['request', 'response'])
