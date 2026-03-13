from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from apps.blog.models import Category, Comment, Post, PostStatus, Tag

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with realistic test data"

    def handle(self, *args, **options):
        fake = Faker()

        users = []
        for index in range(1, 6):
            email = f"user{index}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "preferred_language": ["en", "ru", "kk"][index % 3],
                    "timezone": "Asia/Almaty",
                },
            )
            if created:
                user.set_password("TestPass123!")
                user.save()
            users.append(user)

        categories_data = [
            ("tech", "Technology", "Технологии", "Технологиялар"),
            ("news", "News", "Новости", "Жаңалықтар"),
            ("life", "Lifestyle", "Стиль жизни", "Өмір салты"),
        ]

        categories = []
        for slug, name_en, name_ru, name_kk in categories_data:
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    "name_en": name_en,
                    "name_ru": name_ru,
                    "name_kk": name_kk,
                },
            )
            categories.append(category)

        tags = []
        for slug, name in [
            ("django", "Django"),
            ("drf", "DRF"),
            ("python", "Python"),
            ("async", "Async"),
            ("redis", "Redis"),
            ("api", "API"),
        ]:
            tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
            tags.append(tag)

        for i in range(1, 21):
            post, created = Post.objects.get_or_create(
                slug=f"post-{i}",
                defaults={
                    "author": users[i % len(users)],
                    "title": fake.sentence(nb_words=5),
                    "body": fake.text(max_nb_chars=500),
                    "category": categories[i % len(categories)],
                    "status": PostStatus.PUBLISHED if i % 3 else PostStatus.DRAFT,
                },
            )
            if created:
                post.tags.set(tags[: (i % len(tags)) + 1])

        published_posts = Post.objects.filter(status=PostStatus.PUBLISHED)[:10]
        for post in published_posts:
            for j in range(3):
                Comment.objects.get_or_create(
                    post=post,
                    author=users[j % len(users)],
                    body=fake.sentence(nb_words=10),
                )

        self.stdout.write(self.style.SUCCESS("Seed data completed successfully"))
