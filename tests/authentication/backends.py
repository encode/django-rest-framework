from collections import defaultdict

from django.contrib.auth.models import Permission


def assign_perm(perm, group, obj=None):
    if "." not in perm:
        raise ValueError("perm must be in the format 'app_label.codename'")

    if obj:
        ObjectPermissionBackend.assign_perm(perm, group, obj)
    else:
        # Assign global permissions if there is no object
        app_label, codename = perm.split(".", 1)
        perm = Permission.objects.get(
            content_type__app_label=app_label, codename=codename
        )
        group.permissions.add(perm)


class ObjectPermissionBackend:
    # Stores the set of groups that have the given permission for the given object
    object_perms = defaultdict(lambda: defaultdict(set))

    def authenticate(self, *_, **__):
        return None

    @classmethod
    def assign_perm(cls, perm, group, obj):
        cls.object_perms[obj][perm].add(group)

    def has_perm(self, user_obj, perm, obj=None):
        groups_with_obj_perm = self.object_perms[obj][perm]
        users_groups = {*user_obj.groups.all()}
        return bool(groups_with_obj_perm.intersection(users_groups))
