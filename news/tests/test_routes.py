from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from news.models import Comment, News

# Разрешаем доступ к базе данных для всех тестов в модуле.
pytestmark = pytest.mark.django_db

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты доступности маршрутов приложения новостей."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт тестовые объекты: новость, пользователей и комментарий."""
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='Текст комментария'
        )

    def test_home_page(self):
        """Главная страница новостей доступна любому пользователю."""
        url = reverse('news:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability(self):
        """Общие страницы приложения доступны анонимному пользователю."""
        urls = (
            ('news:home', None),
            ('news:detail', (self.news.id,)),
            ('users:login', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_comment_edit_and_delete(self):
        """Автор видит страницы редактирования и удаления.

        Читателю возвращается ответ 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('news:edit', 'news:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.comment.id,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Анонимного пользователя перенаправляют на страницу входа."""
        login_url = reverse('users:login')
        for name in ('news:edit', 'news:delete'):
            with self.subTest(name=name):
                url = reverse(name, args=(self.comment.id,))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)


def test_logout_requires_post(client):
    """Страница выхода принимает только POST-запрос."""
    url = reverse('users:logout')
    # LogoutView по умолчанию не разрешает GET-запросы, ожидаем 405.
    response = client.get(url)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
