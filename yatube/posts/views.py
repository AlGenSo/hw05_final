from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .models import Follow, Post, Group, User
from .utils import pagination
from posts.forms import PostForm, CommentForm
from .constants import CACHE_UPDATE


@cache_page(CACHE_UPDATE, key_prefix='index_page')
def index(request):
    '''view-функция для главной страницы'''
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group')
    page_obj = pagination(post_list, request)
    context = {
        'page_obj': page_obj,
        'cache_updates': CACHE_UPDATE,
    }

    return render(request, template, context)


def groups_posts(request, slug):
    '''view-функция для страницы на которой будут посты'''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = pagination(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def profile(request, username):
    '''Страница профайла пользователя:
    на ней будет отображаться информация об авторе и его посты.'''
    temmplate = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    page_obj = pagination(posts_list, request)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, temmplate, context)


def post_detail(request, post_id):
    '''Страница для просмотра отдельного поста.'''
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, template, context)


@login_required
def post_create(request):
    '''Страница для публикации постов'''
    template = 'posts/post_create.html'
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=post.author)

    return render(request, template, {'form': form, 'username': request.user})


@login_required
def edit(request, post_id):
    """Вью-функция изменения публикации"""
    template = 'posts:post_detail'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(template, post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect(template, post_id=post_id)

    form = PostForm(instance=post)

    return render(
        request,
        'posts/post_create.html',
        {'is_edit': True, 'form': form, 'post': post},
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = pagination(post_list, request)
    context = {
        'page_obj': page_obj,
    }

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:profile', username=username)
