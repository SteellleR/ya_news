import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.models import News, Comment


pytestmark = pytest.mark.django_db


# --- Общие фикстуры --- #

@pytest.fixture
def author(db):
    """Создаёт пользователя-автора."""
    User = get_user_model()
    return User.objects.create_user(username="Автор")


@pytest.fixture
def author_client(author, client):
    """Авторизованный клиент."""
    client.force_login(author)
    return client


# --- Фикстуры для тестов --- #

@pytest.fixture
def news_list():
    """Создаёт (NEWS_COUNT_ON_HOME_PAGE + 1) новостей с разными датами."""
    news_count = settings.NEWS_COUNT_ON_HOME_PAGE + 1
    news_objects = []
    for i in range(news_count):
        news_objects.append(
            News.objects.create(
                title=f"Новость {i}",
                text="Текст новости",
                date=f"2024-01-{i + 1:02d}",
            )
        )
    return news_objects


@pytest.fixture
def news_with_comments(author):
    """Создаёт новость с несколькими комментариями с разными created."""
    news = News.objects.create(title="Заголовок", text="Текст новости")
    for i in range(3):
        Comment.objects.create(
            news=news,
            author=author,
            text=f"Комментарий {i}",
            created=f"2024-01-0{i + 1} 12:00:00",
        )
    return news


# --- Тесты --- #

def test_news_count_on_home_page(client, news_list):
    """На главной странице не больше NEWS_COUNT_ON_HOME_PAGE новостей."""
    url = reverse("news:home")
    response = client.get(url)
    object_list = response.context["object_list"]
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client, news_list):
    """Новости на главной отсортированы по убыванию даты."""
    url = reverse("news:home")
    response = client.get(url)
    object_list = response.context["object_list"]
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


def test_comments_order_on_detail(client, news_with_comments):
    """Комментарии на странице новости отсортированы по возрастанию даты."""
    url = reverse("news:detail", args=(news_with_comments.id,))
    response = client.get(url)
    comments = response.context["object"].comment_set.all()
    created_dates = [comment.created for comment in comments]
    assert created_dates == sorted(created_dates)


def test_anonymous_cant_see_form(client, news_with_comments):
    """Анонимный пользователь не видит форму добавления комментариев."""
    url = reverse("news:detail", args=(news_with_comments.id,))
    response = client.get(url)
    assert "form" not in response.context


def test_authorized_user_sees_form(author_client, news_with_comments):
    """Авторизованный пользователь видит форму комментария."""
    url = reverse("news:detail", args=(news_with_comments.id,))
    response = author_client.get(url)
    assert "form" in response.context
