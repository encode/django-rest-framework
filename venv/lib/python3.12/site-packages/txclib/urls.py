# These are the Transifex API urls
# flake8: noqa

API_URLS = {
    'get_resources': '/api/2/project/%(project)s/resources/',
    'project_details': '/api/2/project/%(project)s/?details',
    'resource_details': '/api/2/project/%(project)s/resource/%(resource)s/',
    'pull_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file',
    'pull_pseudo_file': '/api/2/project/%(project)s/resource/%(resource)s/pseudo/?pseudo_type=MIXED',
    'pull_reviewed_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=reviewed',
    'pull_sourceastranslation_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=sourceastranslation',
    'pull_translator_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=translator',
    'pull_onlytranslated_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=onlytranslated',
    'pull_onlyreviewed_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=onlyreviewed',
    'pull_developer_file': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/?file&mode=default',
    'resource_stats': '/api/2/project/%(project)s/resource/%(resource)s/stats/',
    'create_resource': '/api/2/project/%(project)s/resources/',
    'push_source': '/api/2/project/%(project)s/resource/%(resource)s/content/',
    'push_translation': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/',
    'delete_translation': '/api/2/project/%(project)s/resource/%(resource)s/translation/%(language)s/',
    'formats': '/api/2/formats/',
    'delete_resource': '/api/2/project/%(project)s/resource/%(resource)s/',
}
