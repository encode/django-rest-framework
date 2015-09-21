from django.db import router


class BaseDbRouter(object):
    def get_db_alias(self, request, model):
        raise NotImplementedError(".get_db_alias() must be overridden.")


class DjangoDbRouter(BaseDbRouter):
    def get_db_alias(self, request, model):
        if request.method.lower() != "get":
            return router.db_for_write(model)
