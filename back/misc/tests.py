import pytest


@pytest.mark.django_db
def test_to_slack_block(new_hire_factory, to_do_factory):
    # fmt: off
    to_do = to_do_factory(content={"time":1651693330143,"blocks":[{"id":"4qrek_mikV","type":"paragraph","data":{"text":"paragraph <b>bold</b><i> italic</i> <a href=\"https://chiefonboarding.com\">link</a><br>"}},{"id":"kD0wLqPzXv","type":"header","data":{"text":"H1","level":1}},{"id":"xMrMIh9Huu","type":"header","data":{"text":"H2","level":2}},{"id":"YocSd-LRxo","type":"header","data":{"text":"H3","level":3}},{"id":"QaByEzQfWA","type":"form","data":{"type":"input","text":"Input field"}},{"id":"O6jUy5IxQk","type":"form","data":{"type":"text","text":"Multiline"}},{"id":"OWFDBODLgM","type":"quote","data":{"text":"Quote","caption":"From someone","alignment":"left"}},{"id":"63FTRJS2eq","type":"list","data":{"style":"ordered","items":[{"content":"Ordered item 1","items":[]},{"content":"Ordered item 2","items":[]}]}},{"id":"jwrOdLiyWI","type":"list","data":{"style":"unordered","items":[{"content":"Unordered item 1","items":[]},{"content":"Unordered item 2","items":[]}]}},{"id":"yc7OL9vCXZ","type":"delimiter","data":{}}],"version":"2.22.2"})  # noqa: E231, E501

    new_hire = new_hire_factory()
    assert to_do.to_slack_block(new_hire) == [{'type': 'section', 'text': {'type': 'mrkdwn', 'text': 'paragraph *bold*_ italic_ <https://chiefonboarding.com|link>'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*H1*'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*H2*'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*H3*'}}, {'type': 'input', 'block_id': 'QaByEzQfWA', 'element': {'type': 'plain_text_input', 'action_id': 'QaByEzQfWA'}, 'label': {'type': 'plain_text', 'text': 'Input field', 'emoji': True}}, {'type': 'input', 'block_id': 'O6jUy5IxQk', 'element': {'type': 'plain_text_input', 'multiline': True, 'action_id': 'O6jUy5IxQk'}, 'label': {'type': 'plain_text', 'text': 'Multiline', 'emoji': True}}, {'type': 'context', 'elements': {'text': {'type': 'mrkdwn', 'text': 'Quote\nFrom someone'}}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': "1. Ordered item 1\n2. Ordered item 2\n"}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': "* Unordered item 1\n* Unordered item 2\n"}}, {'type': 'divider'}]  # noqa: E231, E501
    # fmt: on


@pytest.mark.django_db
def test_to_slack_block_questions(new_hire_factory, to_do_factory):
    # fmt: off
    to_do = to_do_factory(content={"blocks":[{"content":"TEst","items":[{"id":"temp-54be","text":"test"},{"text":"tesstt","id":"temp-4eb2"},{"text":"testttttt","id":"temp-7300"},{"text":"test2","id":"temp-215a"}],"type":"question","answer":"temp-4eb2"},{"content":"Another question","items":[{"id":"temp-6272","text":"option1"},{"text":"option2","id":"temp-6e14"}],"type":"question","answer":"temp-6272"}]})  # noqa: E231, E501

    new_hire = new_hire_factory()

    assert to_do.to_slack_block(new_hire) == [{'type': 'input', 'block_id': 'item-0', 'element': {'type': 'radio_buttons', 'options': [{'text': {'type': 'plain_text', 'text': 'test', 'emoji': True}, 'value': 'temp-54be'}, {'text': {'type': 'plain_text', 'text': 'tesstt', 'emoji': True}, 'value': 'temp-4eb2'}, {'text': {'type': 'plain_text', 'text': 'testttttt', 'emoji': True}, 'value': 'temp-7300'}, {'text': {'type': 'plain_text', 'text': 'test2', 'emoji': True}, 'value': 'temp-215a'}], 'action_id': 'item-0'}, 'label': {'type': 'plain_text', 'text': 'TEst', 'emoji': True}}, {'type': 'input', 'block_id': 'item-1', 'element': {'type': 'radio_buttons', 'options': [{'text': {'type': 'plain_text', 'text': 'option1', 'emoji': True}, 'value': 'temp-6272'}, {'text': {'type': 'plain_text', 'text': 'option2', 'emoji': True}, 'value': 'temp-6e14'}], 'action_id': 'item-1'}, 'label': {'type': 'plain_text', 'text': 'Another question', 'emoji': True}}]  # noqa: E231, E501
    # fmt: on
