from django.db import models
from django.db.models import Case, F, When


class ConditionQuerySet(models.QuerySet):
    def alias_days_order(self):
        from admin.sequences.models import Condition

        return self.alias(
            days_order=Case(
                When(condition_type=Condition.Type.BEFORE, then=F("days") * -1),
                When(condition_type=Condition.Type.TODO, then=99998),
                When(condition_type=Condition.Type.ADMIN_TASK, then=99999),
                default=F("days"),
            )
        )
