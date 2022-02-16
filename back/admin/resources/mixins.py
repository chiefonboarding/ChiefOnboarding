from .models import Chapter

class ResourceMixin:
    counter = 0

    def _create_or_update_chapter(self, resource, parent, chapter):
        if isinstance(chapter['id'], int):
            chap = Chapter.objects.get(id=chapter['id'])
            chap.name = chapter['name']
            chap.content = chapter['content']
            chap.resource = resource
            chap.order = self.counter
            chap.save()
        else:
            chap = Chapter.objects.create(
                resource=resource,
                name=chapter['name'],
                content=chapter['content'],
                type=chapter['type'],
                order=self.counter
            )
            if parent is not None:
                chap.parent_chapter = Chapter.objects.get(id=parent)
                chap.save()
        self.counter += 1

        # Return new/updated item id
        return chap.id

    def _get_child_chapters(self, resource, parent, children):
        if len(children) == 0:
            return

        for chapter in children:
            # Save or update item
            parent_id = self._create_or_update_chapter(resource, parent, chapter)

            # Go one level deeper - check and create chapters
            self._get_child_chapters(resource, parent_id, chapter['children'])
