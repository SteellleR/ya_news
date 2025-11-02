import pytest
from django.urls import reverse

from news.models import News, Comment


pytestmark = pytest.mark.django_db


# Фикстуры


@pytest.fixture
def author(django_user_model):
    """Создаёт пользователя-автора."""
    return django_user_model.objects.create_user(username="Автор")


@pytest.fixture
def not_author(django_user_model):
    """Создаёт пользователя, не являющегося автором."""
    return django_user_model.objects.create_user(username="Другой")


@pytest.fixture
def author_client(author, client):
    """Создаёт авторизованный клиент для автора."""
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author, client):
    """Создаёт авторизованный клиент для другого пользователя."""
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    """Создаёт новость для тестов маршрутов."""
    return News.objects.create(title="Новость", text="Текст новости")


@pytest.fixture
def comment(news, author):
    """Создаёт комментарий автора к новости."""
    return Comment.objects.create(
        news=news,
        author=author,
        text="Комментарий автора",
    )


# Тесты маршрутов

def test_anonymous_user_routes(client, news, comment):
    """Анонимный пользователь: доступность и редиректы."""
    home_url = reverse("news:home")
    detail_url = reverse("news:detail", args=(news.id,))
    edit_url = reverse("news:edit", args=(comment.id,))
    delete_url = reverse("news:delete", args=(comment.id,))
    login_url = reverse("users:login")
    signup_url = reverse("users:signup")
    logout_url = reverse("users:logout")

    # Доступные страницы
    assert client.get(home_url).status_code == 200
    assert client.get(detail_url).status_code == 200
    assert client.get(login_url).status_code == 200
    assert client.get(signup_url).status_code == 200

    # Logout — только POST, GET запрещён
    assert client.get(logout_url).status_code == 405

    # Попытка редактировать или удалить → редирект на login
    response_edit = client.get(edit_url)
    response_delete = client.get(delete_url)
    expected_redirect = f"{login_url}?next={edit_url}"
    assert response_edit.status_code == 302
    assert response_edit.url == expected_redirect
    expected_redirect = f"{login_url}?next={delete_url}"
    assert response_delete.status_code == 302
    assert response_delete.url == expected_redirect


def test_author_can_access_edit_and_delete(author_client, comment):
    """Автор комментария может открыть страницы редактирования и удаления."""
    edit_url = reverse("news:edit", args=(comment.id,))
    delete_url = reverse("news:delete", args=(comment.id,))
    response_edit = author_client.get(edit_url)
    response_delete = author_client.get(delete_url)
    assert response_edit.status_code == 200
    assert response_delete.status_code == 200


def test_not_author_gets_404_on_edit_and_delete(not_author_client, comment):
    """Другой пользователь получает 404 при доступе к чужим комментариям."""
    edit_url = reverse("news:edit", args=(comment.id,))
    delete_url = reverse("news:delete", args=(comment.id,))
    assert not_author_client.get(edit_url).status_code == 404
    assert not_author_client.get(delete_url).status_code == 404
