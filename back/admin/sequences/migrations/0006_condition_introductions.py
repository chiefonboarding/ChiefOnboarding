# Generated by Django 3.1.2 on 2020-11-24 16:21
from django.db import migrations, models


class Migration(migrations.Migration):
    def move_introductions(apps, schema_editor):
        Sequence = apps.get_model("sequences", "Sequence")
        Condition = apps.get_model("sequences", "Condition")

        for i in Sequence.objects.all():
            # finding sequences with introductions
            if i.introductions.all().count():
                # check if condition exists or otherwise create it
                if Condition.objects.filter(
                    sequence=i, days=1, condition_type=0
                ).exists():
                    con = Condition.objects.filter(
                        sequence=i, days=1, condition_type=0
                    ).first()
                else:
                    con = Condition.objects.create(sequence=i, days=1, condition_type=0)
                # adding introductions to the condition
                for j in i.introductions.all():
                    con.introductions.add(j)

    dependencies = [
        ("introductions", "0002_introduction_intro_person"),
        ("sequences", "0005_auto_20200924_1309"),
    ]

    operations = [
        migrations.AddField(
            model_name="condition",
            name="introductions",
            field=models.ManyToManyField(to="introductions.Introduction"),
        ),
        migrations.RunPython(move_introductions),
    ]
