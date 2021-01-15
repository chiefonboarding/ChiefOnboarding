import pytest
from sequences.models import *
from resources.models import *
from misc.models import Content
from freezegun import freeze_time
import datetime

@pytest.fixture
def preboarding_obj():
    content = Content.objects.create(items=[{
            "type": "p",
            "items": [],
            "content": "<p>We would really love to get to you know you, {{first_name}}. We value a team spirit and we think that a great team spirit can only be achieve when people know eachother. Please fill in the form underneath so we know a bit more about you!</p>",
            "answer": "",
            "files": []
        }]
    )
    preboarding = Preboarding.objects.create(
        name='This is a paragraph',
        form=[
          {
            "id": "f087",
            "text": "What's your favorite color?",
            "type": "input"
          },
          {
            "id": "7264",
            "text": "If we would give you $10,000. What would you do with it?",
            "type": "text"
          },
          {
            "id": "887a",
            "text": "What do you prefer?",
            "type": "select",
            "options": [
              {
                "id": "bc97",
                "name": "Mangos"
              },
              {
                "id": "4221",
                "name": "Banana"
              },
              {
                "id": "94bf",
                "name": "Grapefruit"
              }
            ]
          },
          {
            "id": "0466",
            "text": "Upload your headshot",
            "type": "upload"
          }
        ]
    )
    preboarding.content.add(content)
    return preboarding 

@pytest.fixture
def second_preboarding_obj():
    content = Content.objects.create(items=[{
            "type": "p",
            "items": [],
            "content": "<p>Hi! We are this new company. Let's gooooooooo.</p>",
            "answer": "",
            "files": []
        }]
    )
    preboarding = Preboarding.objects.create(
        name='This is a paragraph',
        form=[]
    )
    preboarding.content.add(content)
    return preboarding 