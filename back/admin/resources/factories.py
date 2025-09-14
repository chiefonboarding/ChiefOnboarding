import factory
from factory.fuzzy import FuzzyChoice, FuzzyText
from pytest_factoryboy import register

from admin.resources.models import Category, Chapter, Resource


@register
class CategoryFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Category


@register
class ChapterFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    content = {
        "time": 0,
        "blocks": [
            {"data": {"text": "Please complete this item!"}, "type": "paragraph"}
        ],
    }
    type = FuzzyChoice([0, 1, 2])
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Chapter


@register
class ResourceFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    category = factory.SubFactory(CategoryFactory)

    class Meta:
        model = Resource
        skip_postgeneration_save=True

    @factory.post_generation
    def chapters(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Create two resources. One with a page and one with a question
            ChapterFactory(resource=obj, type=0)
            ChapterFactory(
                resource=obj,
                type=2,
                content={
                    "time": 0,
                    "blocks": [
                        {
                            "id": "1",
                            "type": "question",
                            "content": "Please answer this question",
                            "items": [
                                {"id": "1", "text": "first option"},
                                {"id": "2", "text": "second option"},
                            ],
                        }
                    ],
                },
            )
        else:
            for chapter in extracted:
                chapter.resource = obj
                chapter.save()


@register
class ResourceWithLevelDeepChaptersFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Resource
        skip_postgeneration_save = True

    @factory.post_generation
    def chapters(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Create two resources. One with a page and one with a question
            ChapterFactory(name="top_lvl0", resource=obj, type=0, order=0)
            top_level1 = ChapterFactory(name="top_lvl1", resource=obj, type=1, order=1)
            ChapterFactory(name="top_lvl2", resource=obj, type=0, order=5)
            top_level3 = ChapterFactory(name="top_lvl3", resource=obj, type=1, order=6)
            ChapterFactory(name="top_lvl4_q", resource=obj, type=2, order=10)

            ChapterFactory(
                parent_chapter=top_level1,
                name="inner_lvl1_0",
                resource=obj,
                type=0,
                order=2,
            )
            innerLevel1 = ChapterFactory(
                parent_chapter=top_level1,
                name="inner_lvl1_1",
                resource=obj,
                type=1,
                order=2,
            )
            ChapterFactory(
                parent_chapter=innerLevel1,
                name="inner_lvl1_1_1",
                resource=obj,
                type=0,
                order=4,
            )

            ChapterFactory(
                parent_chapter=top_level3,
                name="inner_lvl3_0",
                resource=obj,
                type=0,
                order=7,
            )
            ChapterFactory(
                parent_chapter=top_level3,
                name="inner_lvl3_1",
                resource=obj,
                type=0,
                order=8,
            )
            ChapterFactory(
                parent_chapter=top_level3,
                name="inner_lvl3_2",
                resource=obj,
                type=0,
                order=9,
            )
