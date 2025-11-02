import pytest
from django.urls import reverse

from news.models import News, Comment
from news.forms import BAD_WORDS, WARNING


pytestmark = pytest.mark.django_db


# --- Фикстуры --- #

@pytest.fixture
def author(django_user_model):
    """Создаёт пользователя-автора."""
    return django_user_model.objects.create_user(username="Автор")


@pytest.fixture
def not_author(django_user_model):
    """Создаёт другого пользователя."""
    return django_user_model.objects.create_user(username="Другой пользователь")


@pytest.fixture
def author_client(author, client):
    """Авторизованный клиент."""
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author, client):
    """Авторизованный клиент другого пользователя."""
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    """Создаёт новость для тестов."""
    return News.objects.create(title="Новость", text="Текст новости")


@pytest.fixture
def comment(news, author):
    """Создаёт комментарий автора под новостью."""
    return Comment.objects.create(news=news, author=author, text="Текст комментария")


@pytest.fixture
def form_data():
    """Данные для формы комментария."""
    return {"text": "Новый комментарий"}


# --- Тесты --- #

def test_anonymous_cant_create_comment(client, news, form_data):
    """Анонимный пользователь не может создать комментарий."""
    url = reverse("news:detail", args=(news.id,))
    client.post(url, data=form_data)
    assert Comment.objects.count() == 0


def test_author_can_create_comment(author_client, news, form_data):
    """Авторизованный пользователь может создать комментарий."""
    url = reverse("news:detail", args=(news.id,))
    response = author_client.post(url, data=form_data)
    assert response.status_code == 302
    assert response.url == reverse("news:detail", args=(news.id,)) + "#comments"
    assert Comment.objects.count() == 1
    comment = Comment.objects.first()
    assert comment.text == form_data["text"]
    assert comment.author.username == "Автор"


def test_bad_words_in_comment(author_client, news):
    """Если комментарий содержит стоп-слово, появляется ошибка формы."""
    bad_word = BAD_WORDS[0]
    data = {"text": f"Ты {bad_word}!"}
    url = reverse("news:detail", args=(news.id,))
    response = author_client.post(url, data=data)
    form = response.context["form"]
    assert form.errors["text"] == [WARNING]
    assert Comment.objects.count() == 0


def test_author_can_delete_own_comment(author_client, comment):
    """Автор может удалить свой комментарий."""
    url = reverse("news:delete", args=(comment.id,))
    response = author_client.post(url)
    assert response.status_code == 302
    assert response.url == reverse("news:detail", args=(comment.news.id,)) + "#comments"
    assert Comment.objects.count() == 0


def test_not_author_cant_delete_comment(not_author_client, comment):
    """Другой пользователь не может удалить чужой комментарий."""
    url = reverse("news:delete", args=(comment.id,))
    response = not_author_client.post(url)
    assert response.status_code == 404
    assert Comment.objects.count() == 1


def test_author_can_edit_own_comment(author_client, comment):
    """Автор может отредактировать свой комментарий."""
    url = reverse("news:edit", args=(comment.id,))
    data = {"text": "Обновлённый текст"}
    response = author_client.post(url, data=data)
    assert response.status_code == 302
    assert response.url == reverse("news:detail", args=(comment.news.id,)) + "#comments"
    comment.refresh_from_db()
    assert comment.text == "Обновлённый текст"


def test_not_author_cant_edit_comment(not_author_client, comment):
    """Другой пользователь не может редактировать чужой комментарий."""
    url = reverse("news:edit", args=(comment.id,))
    data = {"text": "Попытка взлома"}
    response = not_author_client.post(url, data=data)
    assert response.status_code == 404
    comment.refresh_from_db()
    assert comment.text == "Текст комментария"
