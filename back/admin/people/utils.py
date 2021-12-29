from django.apps import apps

MODELS = [
    { 'app': 'to_do', 'model': 'ToDo', 'user_field': 'to_do'},
    { 'app': 'resources', 'model': 'Resource', 'user_field': 'resources'},
    { 'app': 'introductions', 'model': 'Introduction', 'user_field': 'introductions'},
    { 'app': 'appointments', 'model': 'Appointment', 'user_field': 'appointments'},
    { 'app': 'preboarding', 'model': 'Preboarding', 'user_field': 'preboarding'},
]

def template_model_exists(template_slug):
    return any([ x['model'].lower() == template_slug for x in MODELS ])

def get_templates_model(template_slug):
    if template_model_exists(template_slug):
        app = next((x['app'] for x in MODELS if x['model'].lower() == template_slug), None)
        return apps.get_model(app, template_slug)

def get_user_field(template_slug):
    if template_model_exists(template_slug):
        return next((x['user_field'] for x in MODELS if x['model'].lower() == template_slug), None)

