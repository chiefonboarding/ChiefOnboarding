import pytest
from django.urls import reverse

@pytest.mark.django_db
@pytest.mark.parametrize(
    'email, password, status_code', [
        ('', '', 400),
        ('', 'strong_pass', 400),
        ('user@example.com', '', 400),
        ('user@example.com', 'invalid_pass', 400),
        ('user@example.com', 'strong_pass', 200)
    ]
)
def test_login_data_validation(email, password, status_code, client):
    User.objects.create_new_hire('john', 'smith', 'user@example.com', 'strong_pass')
    url = reverse('login-url')
    data = {
        'username': email,
        'password': password
    }
    response = client.post(url, data=data)
    assert response.status_code == status_code