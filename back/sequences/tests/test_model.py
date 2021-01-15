import pytest
from sequences.models import *
from resources.models import *
from preboarding.test import preboarding_obj, second_preboarding_obj
from misc.models import Content
from freezegun import freeze_time
import datetime

@pytest.fixture
def sequence(preboarding_obj, second_preboarding_obj):
    seq = Sequence.objects.create(name='Test sequence')

    seq.preboarding.add([preboarding_obj, second_preboarding_obj])

    res = Resource.objects.create(name='Test chapter', course=True)
    content = Content.objects.create(type='p', content='Test content')
    chapter = Chapter.objects.create(resource=res, name='Test chapter', type=0)
    chapter.content.add(content)
    chapter2 = Chapter.objects.create(resource=res, name='Test chapter2', type=0)
    chapter2.content.add(content)
    return res
