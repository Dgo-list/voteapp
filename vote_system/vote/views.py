from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from vote.models import Question, Question_option, Vote
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, Http404

# Create your views here.
def Home(request):
    context = {}
    if request.GET.has_key('next'):
        context['nexturl']= request.GET['next']
    if request.session.has_key('message'):
        context['message']= request.session['message']
        del request.session['message']

    return render(request, 'vote/home.html', context=context)

def Register(request):
    usr = request.POST.get('username')
    pwd = request.POST.get('password')
    cfpwd = request.POST.get('confirmpassword')

    if(pwd==cfpwd):
        newuser = User.objects.create_user(username=usr, password=pwd)
        newuser.save()
        request.session['message'] = 'User created'
        return redirect('/home')
    else:
        request.session['message'] = 'Password and confirm password mismatch'
        return redirect('/home')

def Login(request):
    username=request.POST.get('username')
    password=request.POST.get('password')
    user = authenticate(username=username, password=password)
    print str(user)
    if user != None:
        login(request,user)
        if request.POST.has_key('nexturl'):
            next_url = request.POST.get('nexturl')
            return redirect(next_url)
        else:
            if has_moderation_privileges(user):
                return redirect('/administration/')
            else:
                return redirect('/questions/')
    else:
        request.session['message'] = 'Invalid password or username'
        return redirect('/home')

@login_required
def ListQuestions(request):
    print 'LIST QUESTION'
    class Question_data:
        def __init__(self, question_id, question_text):
            self.id = question_id
            self.question_text = question_text
            is_taken = Vote.objects.filter(question_id=question_id).filter(username=request.user.username).count()
            print 'is taken is '+str(is_taken)+' for question '+str(question_id)+' and user '+request.user.username
            if is_taken>0:
                self.is_disabled = True
                self.style = 'disabled-question-content'
            else:
                self.is_disabled = False
                self.style = 'question-content'

            ops = Question_option.objects.filter(question_id=question_id)
            self.options = []
            for op in ops:
                    self.options.append({'text': op.option_text, 'id': op.id})

    questions = []
    for question in Question.objects.all():
        questions.append(Question_data(question.id, question.question_text))

    if request.session.has_key('message'):
        message_text = request.session['message']
        del request.session['message']
    else:
        message_text = ''
    context={'questions': questions, 'message': message_text}
    return render(request, 'vote/questions.html', context=context)

@login_required
def FetchQuestion(request, questionid):
    print "FETCH QUESTIOn"
    class Question_data:
        def __init__(self, question_id, question_text):
            self.id = question_id
            self.question_text = question_text
            is_taken = Vote.objects.filter(question_id=question_id).filter(username=request.user.username).count()
            print 'is taken is '+str(is_taken)+' for question '+str(question_id)+' and user '+request.user.username
            if is_taken>0:
                self.is_disabled = True
                self.style = 'disabled-question-content'
            else:
                self.is_disabled = False
                self.style = 'question-content'

            ops = Question_option.objects.filter(question_id=question_id)
            self.options = []
            for op in ops:
                    self.options.append({'text': op.option_text, 'id': op.id})

    question = Question.objects.get(pk=questionid)
    q_data = Question_data(question.id, question.question_text)

    if request.session.has_key('message'):
        message_text = request.session['message']
        del request.session['message']
    elif q_data.is_disabled:
        message_text = 'You have already voted on this question'
    else:
        message_text = ''
    context={'questions': [q_data], 'message': message_text}

    return render(request, 'vote/questions.html', context=context)

@login_required
def VoteQuestion(request, questionid):
    option = request.POST.get(questionid)
    option_obj = Question_option.objects.get(pk=option)
    question_obj = Question.objects.get(pk=questionid)
    username = request.user.username
    applyVote = Vote(question=question_obj, username=username, question_option=option_obj)
    applyVote.save()
    request.session['message'] = 'Your poll has been accepted'
    return redirect('/questions/'+str(questionid))


#Utility Method
def has_moderation_privileges(user):
    user_groups = []
    for g in user.groups.all():
        user_groups.append(g.name)
    if 'moderator' in user_groups:
        return True
    else:
        return False


@login_required
def AdministrationPage(request):
    if not has_moderation_privileges(request.user):
        return HttpResponseForbidden()
    class question_data:
        def __init__(self, question_id, question_text):
            self.id = question_id
            self.question_text = question_text

            ops = Question_option.objects.filter(question_id=question_id)
            self.options = []
            for op in ops:
                    votes_on_option = Vote.objects.filter(question_id=question_id).filter(question_option=op).count
                    self.options.append({'text': op.option_text, 'id': op.id, 'votes': votes_on_option})
    questions = []
    for question in Question.objects.all():
        questions.append(question_data(question.id, question.question_text))
    if request.session.has_key('message'):
        message_text = request.session['message']
        context = {'questions': questions, 'has_message': True, 'message': message_text}
    else:
        context = {'questions': questions, 'has_message': False}

    return render(request, 'vote/administration.html', context=context)

@login_required
def CreateQuestion(request):
    if not has_moderation_privileges(request.user):
        return HttpResponseForbidden()
    question_text = request.POST.get('question_text')
    question = Question(question_text=question_text, is_published=1)
    question.save() #persist question

    #check for first option
    option_counter=1
    has_more_options = True
    option_name = 'option'+str(option_counter)
    if not request.POST.has_key(option_name):
        has_more_options=False

    while has_more_options:
        option_text = request.POST.get(option_name)
        if option_text==None or option_text=='':
            continue
        q_option = Question_option(question=question, option_text=option_text)
        q_option.save() #persist option

        #check for further options
        option_counter=option_counter+1
        option_name = 'option'+str(option_counter)
        if not request.POST.has_key(option_name):
            has_more_options=False

    request.session['message'] = 'The question has been published to the url: \n http://localhost:8000/questions/'+str(question.id)

    return redirect('/administration/')