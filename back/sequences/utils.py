def get_task_items(c):
    return [
        {'app': 'to_do', 'model': 'ToDo', 'item': 'to_do', 's_model': c.to_do},
        {'app': 'resources', 'model': 'Resource', 'item': 'resources', 's_model': c.resources},
        {'app': 'preboarding', 'model': 'Preboarding', 'item': 'preboarding', 's_model': c.preboarding},
        {'app': 'introductions', 'model': 'Introduction', 'item': 'introductions', 's_model': c.introductions},
        {'app': 'appointments', 'model': 'Appointment', 'item': 'appointments', 's_model': c.appointments}
    ]


def get_condition_items(original, new):
    return [
        {'old_model': original.condition_to_do, 'new_model': new.condition_to_do},
        {'old_model': original.to_do, 'new_model': new.to_do},
        {'old_model': original.badges, 'new_model': new.badges},
        {'old_model': original.resources, 'new_model': new.resources},
        {'old_model': original.admin_tasks, 'new_model': new.admin_tasks},
        {'old_model': original.external_messages, 'new_model': new.external_messages},
        {'old_model': original.introductions, 'new_model': new.introductions}
    ]
