from collections import OrderedDict

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, path
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from guardian.forms import GroupObjectPermissionsForm, UserObjectPermissionsForm
from django.contrib.auth.models import Group
from guardian.shortcuts import (get_group_perms, get_groups_with_perms, get_perms_for_model, get_user_perms,
                                get_users_with_perms)


class AdminUserObjectPermissionsForm(UserObjectPermissionsForm):
    """
    Extends :form:`UserObjectPermissionsForm`. It only overrides
    ``get_obj_perms_field_widget`` method so it return
    ``django.contrib.admin.widgets.FilteredSelectMultiple`` widget.
    """

    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class AdminGroupObjectPermissionsForm(GroupObjectPermissionsForm):
    """
    Extends :form:`GroupObjectPermissionsForm`. It only overrides
    ``get_obj_perms_field_widget`` method so it return
    ``django.contrib.admin.widgets.FilteredSelectMultiple`` widget.
    """

    def get_obj_perms_field_widget(self):
        return FilteredSelectMultiple(_("Permissions"), False)


class GuardedModelAdminMixin:
    """
    Serves as a helper for custom subclassing ``admin.ModelAdmin``.
    """
    change_form_template = \
        'admin/guardian/model/change_form.html'
    obj_perms_manage_template = \
        'admin/guardian/model/obj_perms_manage.html'
    obj_perms_manage_user_template = \
        'admin/guardian/model/obj_perms_manage_user.html'
    obj_perms_manage_group_template = \
        'admin/guardian/model/obj_perms_manage_group.html'
    user_can_access_owned_objects_only = False
    user_owned_objects_field = 'user'
    user_can_access_owned_by_group_objects_only = False
    group_owned_objects_field = 'group'
    include_object_permissions_urls = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if self.user_can_access_owned_objects_only:
            filters = {self.user_owned_objects_field: request.user}
            qs = qs.filter(**filters)
        if self.user_can_access_owned_by_group_objects_only:
            User = get_user_model()
            user_rel_name = User.groups.field.related_query_name()
            qs_key = '{}__{}'.format(self.group_owned_objects_field, user_rel_name)
            filters = {qs_key: request.user}
            qs = qs.filter(**filters)
        return qs

    def get_urls(self):
        """
        Extends standard admin model urls with the following:

        - ``.../permissions/`` under ``app_mdodel_permissions`` url name (params: object_pk)
        - ``.../permissions/user-manage/<user_id>/`` under ``app_model_permissions_manage_user`` url name (params: object_pk, user_pk)
        - ``.../permissions/group-manage/<group_id>/`` under ``app_model_permissions_manage_group`` url name (params: object_pk, group_pk)

        .. note::
           ``...`` above are standard, instance detail url (i.e.
           ``/admin/flatpages/1/``)

        """
        urls = super().get_urls()
        if self.include_object_permissions_urls:
            info = self.model._meta.app_label, self.model._meta.model_name
            myurls = [
                path('<object_pk>/permissions/',
                     view=self.admin_site.admin_view(
                         self.obj_perms_manage_view),
                     name='%s_%s_permissions' % info),
                path('<object_pk>/permissions/user-manage/<user_id>/',
                     view=self.admin_site.admin_view(
                         self.obj_perms_manage_user_view),
                     name='%s_%s_permissions_manage_user' % info),
                path('<object_pk>/permissions/group-manage/<group_id>/',
                     view=self.admin_site.admin_view(
                         self.obj_perms_manage_group_view),
                     name='%s_%s_permissions_manage_group' % info),
            ]
            urls = myurls + urls
        return urls

    def get_obj_perms_base_context(self, request, obj):
        """
        Returns context dictionary with common admin and object permissions
        related content. It uses AdminSite.each_context,
        making sure all required template vars are in the context.
        """
        context = self.admin_site.each_context(request)
        context.update({
            'adminform': {'model_admin': self},
            'media': self.media,
            'object': obj,
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'original': str(obj),
            'has_change_permission': self.has_change_permission(request, obj),
            'model_perms': get_perms_for_model(obj),
            'title': _("Object permissions"),
        })
        return context

    def obj_perms_manage_view(self, request, object_pk):
        """
        Main object permissions view. Presents all users and groups with any
        object permissions for the current model *instance*. Users or groups
        without object permissions for related *instance* would **not** be
        shown. In order to add or manage user or group one should use links or
        forms presented within the page.
        """
        if not self.has_change_permission(request, None):
            post_url = reverse('admin:index', current_app=self.admin_site.name)
            return redirect(post_url)

        from django.contrib.admin.utils import unquote
        obj = get_object_or_404(self.get_queryset(
            request), pk=unquote(object_pk))
        users_perms = OrderedDict(
            sorted(
                get_users_with_perms(obj, attach_perms=True,
                                     with_group_users=False).items(),
                key=lambda user: getattr(
                    user[0], get_user_model().USERNAME_FIELD)
            )
        )

        groups_perms = OrderedDict(
            sorted(
                get_groups_with_perms(obj, attach_perms=True).items(),
                key=lambda group: group[0].name
            )
        )

        if request.method == 'POST' and 'submit_manage_user' in request.POST:
            user_form = self.get_obj_perms_user_select_form(
                request)(request.POST)
            group_form = self.get_obj_perms_group_select_form(
                request)(request.POST)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
            if user_form.is_valid():
                user_id = user_form.cleaned_data['user'].pk
                url = reverse(
                    '%s:%s_%s_permissions_manage_user' % info,
                    args=[obj.pk, user_id]
                )
                return redirect(url)
        elif request.method == 'POST' and 'submit_manage_group' in request.POST:
            user_form = self.get_obj_perms_user_select_form(
                request)(request.POST)
            group_form = self.get_obj_perms_group_select_form(
                request)(request.POST)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
            if group_form.is_valid():
                group_id = group_form.cleaned_data['group'].id
                url = reverse(
                    '%s:%s_%s_permissions_manage_group' % info,
                    args=[obj.pk, group_id]
                )
                return redirect(url)
        else:
            user_form = self.get_obj_perms_user_select_form(request)()
            group_form = self.get_obj_perms_group_select_form(request)()

        context = self.get_obj_perms_base_context(request, obj)
        context['users_perms'] = users_perms
        context['groups_perms'] = groups_perms
        context['user_form'] = user_form
        context['group_form'] = group_form

        # https://github.com/django/django/commit/cf1f36bb6eb34fafe6c224003ad585a647f6117b
        request.current_app = self.admin_site.name

        return render(request, self.get_obj_perms_manage_template(), context)

    def get_obj_perms_manage_template(self):
        """
        Returns main object permissions admin template.  May be overridden if
        need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage.html'
        return self.obj_perms_manage_template

    def obj_perms_manage_user_view(self, request, object_pk, user_id):
        """
        Manages selected users' permissions for current object.
        """
        if not self.has_change_permission(request, None):
            post_url = reverse('admin:index', current_app=self.admin_site.name)
            return redirect(post_url)

        user = get_object_or_404(get_user_model(), pk=user_id)
        obj = get_object_or_404(self.get_queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_user_form(request)
        form = form_class(user, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            msg = gettext("Permissions saved.")
            messages.success(request, msg)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
            url = reverse(
                '%s:%s_%s_permissions_manage_user' % info,
                args=[obj.pk, user.pk]
            )
            return redirect(url)

        context = self.get_obj_perms_base_context(request, obj)
        context['user_obj'] = user
        context['user_perms'] = get_user_perms(user, obj)
        context['form'] = form

        request.current_app = self.admin_site.name

        return render(request, self.get_obj_perms_manage_user_template(), context)

    def get_obj_perms_manage_user_template(self):
        """
        Returns object permissions for user admin template.  May be overridden
        if need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage_user.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage_user.html'
        return self.obj_perms_manage_user_template

    def get_obj_perms_user_select_form(self, request):
        """
        Returns form class for selecting a user for permissions management.  By
        default :form:`UserManage` is returned.
        """
        return UserManage

    def get_obj_perms_group_select_form(self, request):
        """
        Returns form class for selecting a group for permissions management.  By
        default :form:`GroupManage` is returned.
        """
        return GroupManage

    def get_obj_perms_manage_user_form(self, request):
        """
        Returns form class for user object permissions management.  By default
        :form:`AdminUserObjectPermissionsForm` is returned.
        """
        return AdminUserObjectPermissionsForm

    def obj_perms_manage_group_view(self, request, object_pk, group_id):
        """
        Manages selected groups' permissions for current object.
        """
        if not self.has_change_permission(request, None):
            post_url = reverse('admin:index', current_app=self.admin_site.name)
            return redirect(post_url)

        group = get_object_or_404(Group, id=group_id)
        obj = get_object_or_404(self.get_queryset(request), pk=object_pk)
        form_class = self.get_obj_perms_manage_group_form(request)
        form = form_class(group, obj, request.POST or None)

        if request.method == 'POST' and form.is_valid():
            form.save_obj_perms()
            msg = gettext("Permissions saved.")
            messages.success(request, msg)
            info = (
                self.admin_site.name,
                self.model._meta.app_label,
                self.model._meta.model_name,
            )
            url = reverse(
                '%s:%s_%s_permissions_manage_group' % info,
                args=[obj.pk, group.id]
            )
            return redirect(url)

        context = self.get_obj_perms_base_context(request, obj)
        context['group_obj'] = group
        context['group_perms'] = get_group_perms(group, obj)
        context['form'] = form

        request.current_app = self.admin_site.name

        return render(request, self.get_obj_perms_manage_group_template(), context)

    def get_obj_perms_manage_group_template(self):
        """
        Returns object permissions for group admin template.  May be overridden
        if need to change it dynamically.

        .. note::
           If ``INSTALLED_APPS`` contains ``grappelli`` this function would
           return ``"admin/guardian/grappelli/obj_perms_manage_group.html"``.

        """
        if 'grappelli' in settings.INSTALLED_APPS:
            return 'admin/guardian/contrib/grappelli/obj_perms_manage_group.html'
        return self.obj_perms_manage_group_template

    def get_obj_perms_manage_group_form(self, request):
        """
        Returns form class for group object permissions management.  By default
        :form:`AdminGroupObjectPermissionsForm` is returned.
        """
        return AdminGroupObjectPermissionsForm


class GuardedModelAdmin(GuardedModelAdminMixin, admin.ModelAdmin):
    """
    Extends ``django.contrib.admin.ModelAdmin`` class. Provides some extra
    views for object permissions management at admin panel. It also changes
    default ``change_form_template`` option to
    ``'admin/guardian/model/change_form.html'`` which is required for proper
    url (object permissions related) being shown at the model pages.

    **Extra options**

    ``GuardedModelAdmin.obj_perms_manage_template``

        *Default*: ``admin/guardian/model/obj_perms_manage.html``

    ``GuardedModelAdmin.obj_perms_manage_user_template``

        *Default*: ``admin/guardian/model/obj_perms_manage_user.html``

    ``GuardedModelAdmin.obj_perms_manage_group_template``

        *Default*: ``admin/guardian/model/obj_perms_manage_group.html``

    ``GuardedModelAdmin.user_can_access_owned_objects_only``

        *Default*: ``False``

        If this would be set to ``True``, ``request.user`` would be used to
        filter out objects he or she doesn't own (checking ``user`` field
        of used model - field name may be overridden by
        ``user_owned_objects_field`` option).

        .. note::
           Please remember that this will **NOT** affect superusers!
           Admins would still see all items.

    ``GuardedModelAdmin.user_can_access_owned_by_group_objects_only``

        *Default*: ``False``

        If this would be set to ``True``, ``request.user`` would be used to
        filter out objects her or his group doesn't own (checking if any group
        user belongs to is set as ``group`` field of the object; name of the
        field can be changed by overriding ``group_owned_objects_field``).

        .. note::
           Please remember that this will **NOT** affect superusers!
           Admins would still see all items.

    ``GuardedModelAdmin.group_owned_objects_field``

        *Default*: ``group``

    ``GuardedModelAdmin.include_object_permissions_urls``

        *Default*: ``True``

        .. versionadded:: 1.2

        Might be set to ``False`` in order **NOT** to include guardian-specific
        urls.

    **Usage example**

    Just use :admin:`GuardedModelAdmin` instead of
    ``django.contrib.admin.ModelAdmin``.

    .. code-block:: python

        from django.contrib import admin
        from guardian.admin import GuardedModelAdmin
        from myapp.models import Author

        class AuthorAdmin(GuardedModelAdmin):
            pass

        admin.site.register(Author, AuthorAdmin)

    """


class UserManage(forms.Form):
    user = forms.CharField(label=_("User identification"),
                           max_length=200,
                           error_messages={'does_not_exist': _(
                               "This user does not exist")},
                           help_text=_(
                               'Enter a value compatible with User.USERNAME_FIELD')
                           )

    def clean_user(self):
        """
        Returns ``User`` instance based on the given identification.
        """
        identification = self.cleaned_data['user']
        user_model = get_user_model()
        try:
            username_field = user_model.USERNAME_FIELD
        except AttributeError:
            username_field = 'username'
        try:
            user = user_model.objects.get(**{username_field: identification})
            return user
        except user_model.DoesNotExist:
            raise forms.ValidationError(
                self.fields['user'].error_messages['does_not_exist'])


class GroupManage(forms.Form):
    group = forms.CharField(max_length=80, error_messages={'does_not_exist':
                                                           _("This group does not exist")})

    def clean_group(self):
        """
        Returns ``Group`` instance based on the given group name.
        """
        name = self.cleaned_data['group']
        try:
            group = Group.objects.get(name=name)
            return group
        except Group.DoesNotExist:
            raise forms.ValidationError(
                self.fields['group'].error_messages['does_not_exist'])
