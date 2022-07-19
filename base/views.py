from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Room, Topic, Message, User
from .forms import RoomForm, MessageForm, UserForm, MyUserCreationForm


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    topics = Topic.objects.all()
    room_messages = user.message_set.all()
    context = {
        'user': user,
        'rooms': rooms,
        'room_messages': room_messages,
        'topics': topics
    }
    return render(request, 'base/profile.html', context)


def loginPage(request):
    page = 'login'
    # prevent user from relogin (login user redirected to home)
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist.')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username or Password does not exist.")

    context = {
        'page': page
    }
    return render(request, 'base/login_register.html', context)


def registerPage(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # be shure to save username as lower case
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "An error ocurred during registeration.")
    context = {
        'form': form
    }
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    # if request.GET.get('q') != None:
    #     q = request.GET.get('q')
    # else:
    #     q = ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q))
    # Q to search in multiple fields
    room_count = rooms.count()
    topics = Topic.objects.all()[0:5]
    # to show the most recent activites that belong to choosed room
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {
        "rooms": rooms,
        "topics": topics,
        "room_count": room_count,
        "room_messages": room_messages,
    }
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    # create new comment
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants
    }
    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('home')

        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        #     return redirect('home')
    context = {
        'form': form,
        'topics': topics
    }
    return render(request, "base/room_form.html", context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    form = RoomForm(instance=room)
    # if the user is not the owner, prevent to update
    if request.user != room.host:
        return HttpResponse("You are not allowed to update this room")
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        #     return redirect('home')
    context = {
        'form': form,
        'topics': topics,
        'room': room
    }
    return render(request, "base/room_form.html", context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.user != room.host:
        return HttpResponse("You are not allowed to delete this room")
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    context = {
        'msg': room
    }
    return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    room = message.room
    if request.user != message.user:
        return HttpResponse("You are not allowed to delete this message")
    if request.method == 'POST':
        message.delete()
        return redirect('room', pk=room.id)
    context = {
        'msg': message
    }
    return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def updateMessage(request, pk):
    message = Message.objects.get(id=pk)
    room = message.room
    form = MessageForm(instance=message)
    if request.user != message.user:
        return HttpResponse("You are not allowed to update this message")
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('room', pk=room.id)
    context = {
        'form': form,
        'msg': message
    }
    return render(request, 'base/msg_form.html', context)


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    context = {
        'form': form
    }
    return render(request, 'base/update-user.html', context)


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {
        'topics': topics
    }
    return render(request, 'base/topics.html', context)


def activityPage(request):
    room_messages = Message.objects.all()
    context = {
        'room_messages': room_messages
    }
    return render(request, 'base/activity.html', context)
