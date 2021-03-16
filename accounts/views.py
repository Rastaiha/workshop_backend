import logging
import json
import os
import string
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from fsm.models import PlayerHistory, Event
from workshop_backend.settings.base import KAVENEGAR_TOKEN
from .models import Team, VerifyCode
import random
from django.db import transaction
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser, MultiPartParser
from accounts.tokens import account_activation_token
from .models import Member, Participant, Payment
from accounts.cache import TeamsCache
from rest_framework_simplejwt.authentication import JWTAuthentication
from accounts import zarinpal
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status, permissions
from rest_framework.views import APIView
from .utils import *
from .serializers import MyTokenObtainPairSerializer, MemberSerializer
import pytz

logger = logging.getLogger(__name__)


# def check_bibot_response(request):
#     if request.POST.get('bibot-response') is not None:
#         if request.POST.get('bibot-response') != '':
#             r = requests.post('https://api.bibot.ir/api1/siteverify/', data={
#                 'secretkey': '9270bf6cd4a087673ca9e86666977a30',
#                 'response': request.POST['bibot-response']
#             })
#             if r.json()['success']:
#                 return True
#             else:
#                 messages.error(request, 'کپچا به درستی حل نشده است!')
#                 return False
#         else:
#             messages.error(request, 'کپچا به درستی حل نشده است!')
#             return False
#     return False


class ObtainTokenPair(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'username' not in request.data:
            if 'phone' in request.data:
                try:
                    member = Member.objects.get(phone_number=request.data['phone'])
                    data['username'] = member.username
                except Member.DoesNotExist:
                    return Response(
                        {'success': False, 'error': "کاربری با این شماره یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)
            elif 'email' in request.data:
                try:
                    member = Member.objects.get(email=request.data['email'])
                    data['username'] = member.username
                except Member.DoesNotExist:
                    return Response(
                        {'success': False, 'error': "کاربری با این ایمیل یافت نشد."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        validated_data = serializer.validated_data
        validated_data['user_info'] = get_member_json_info(member)
        participants = member.event_participant
        validated_data['events'] = [p.event.id for p in participants.all()]
        return Response(validated_data, status=status.HTTP_200_OK)


class ChangePassword(APIView):
    # parser_class = (MultiPartParser,)
    permission_classes = (permissions.AllowAny,)

    @transaction.atomic
    def post(self, request):
        verify_code = request.data['verify_code']
        phone = request.data['phone']
        v = VerifyCode.objects.filter(phone_number=phone, code=verify_code, is_valid=True)
        if len(v) <= 0:
            return Response({'success': False, 'error': "کد اعتبارسنجی وارد شده اشتباه است."},
                            status=status.HTTP_400_BAD_REQUEST)

        if datetime.now(v[0].expiration_date.tzinfo) > v[0].expiration_date:
            return Response({'success': False, 'error': "اعتبار این کد منقضی شده است."},
                            status=status.HTTP_400_BAD_REQUEST)
        member = Member.objects.get(phone_number=phone)
        member.set_password(request.data['password'])
        member.save()
        return Response({'success': True, 'error': "عملیات با موفقیت انجام شد"}, status=status.HTTP_200_OK)


class SignIn(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        password = request.data['password']
        if 'phone' in request.data:
            phone = request.data['phone']
            print(phone)
            member = authenticate(request, phone_number=phone, password=password)

        elif 'email' in request.data:
            email = request.data['email']
            member = authenticate(request, email=email, password=password)
        elif 'username' in request.data:
            username = request.data['username']
            member = authenticate(request, username=username, password=password)
        print(member)
        if member is not None:
            auth_login(request, member)
            Response({'success': True, 'member': member.id}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'error': 'اطلاعات اشتباه می باشد'}, status=status.HTTP_400_BAD_REQUEST)


class Signup(APIView):
    # after phone verification code sent
    parser_class = (MultiPartParser,)
    permission_classes = (permissions.AllowAny,)

    @transaction.atomic
    def post(self, request):
        verify_code = request.data['verify_code']
        phone = request.data['phone']
        v = VerifyCode.objects.filter(phone_number=phone, code=verify_code, is_valid=True)
        if len(v) <= 0:
            return Response({'success': False, 'error': "کد اعتبارسنجی وارد شده اشتباه است."},
                            status=status.HTTP_400_BAD_REQUEST)

        if datetime.now(v[0].expiration_date.tzinfo) > v[0].expiration_date:
            return Response({'success': False, 'error': "اعتبار این کد منقضی شده است."},
                            status=status.HTTP_400_BAD_REQUEST)

        if Member.objects.filter(username__exact=request.data['username']).count() > 0:
            return Response(
                {'success': False, "error": "فردی با نام کاربری " + request.data['username'] + "قبلا ثبت‌نام کرده"},
                status=status.HTTP_400_BAD_REQUEST)
        if Member.objects.filter(phone_number__exact=request.data['phone']).count() > 0:
            return Response(
                {'success': False, "error": "فردی با شماره همراه " + request.data['phone'] + "قبلا ثبت‌نام کرده"},
                status=status.HTTP_400_BAD_REQUEST)

        if 'document' not in request.data:
            raise ParseError("اطلاعات تأیید هویت ضمیمه نشده است.")

        doc = request.data['document']
        doc.name = str(request.data['phone']) + "-" + doc.name

        # TODO Hard coded event name
        current_event = Event.objects.get(name='مسافر صفر')
        if current_event.has_selection:
            if 'selection_doc' not in request.data:
                raise ParseError("پاسخ سوالات ضمیمه نشده است.")
            selection_doc = request.data['selection_doc']
            selection_doc.name = str(request.data['phone']) + "-" + selection_doc.name
        else:
            if current_event.maximum_participant:
                if current_event.event_cost <= 0:
                    participants = Participant.objects.filter(event=current_event)
                    if len(participants) >= current_event.maximum_participant:
                        return Response({'success': False, "error": "ظرفیت رویداد پر شده است."},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    paid_participants = Participant.objects.filter(event=current_event, is_paid=True)
                    if len(paid_participants) >= current_event.maximum_participant:
                        return Response({'success': False, "error": "ظرفیت رویداد پر شده است."},
                                        status=status.HTTP_400_BAD_REQUEST)

        if current_event.event_type == 'team':
            if 'team_code' in request.data and request.data['team_code'] != '':
                team_code = request.data['team_code']
                try:
                    team = Team.objects.get(team_code=team_code)
                except Team.DoesNotExist:
                    return Response(
                        {'success': False, 'error': "کد تیم نامعتبر است."},
                        status=status.HTTP_400_BAD_REQUEST)
                if len(team.team_participants.all()) >= current_event.team_size:
                    return Response(
                        {'success': False, 'error': "ظرفیت تیم تکمیل است"},
                        status=status.HTTP_400_BAD_REQUEST)
                is_team_head = False
            else:
                team_code = Member.objects.make_random_password(length=6)
                is_team_head = True

        member = Member.objects.create(
            first_name=request.data['name'],
            username=request.data['username'],
            email=request.data['email'],
            is_active=True,
            gender=request.data['gender'],
            city=request.data['city'],
            school=request.data['school'],
            grade=request.data['grade'],
            phone_number=request.data['phone'],
            document=doc,
        )
        member.set_password(request.data['password'])

        participant = Participant.objects.create(
            member=member,
            event=current_event,
            player_type='PARTICIPANT',
        )
        if current_event.has_selection:
            participant.selection_doc = selection_doc

        if current_event.event_type == 'team':
            if 'team_code' not in request.data or request.data['team_code'] == '':
                team = Team.objects.create(team_code=team_code, event=current_event, player_type='TEAM', )
            participant.event_team = team

        member.save()
        participant.save()

        # TODO check email - unit test سپس
        # absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
        # member.send_signup_email(absolute_uri)
        if current_event.event_type == 'team':
            if is_team_head:
                try:
                    Signup.send_signup_sms(phone, request.data['username'], team_code)
                except:
                    return Response({'error': 'مشکلی در ارسال پیامک بوجود آمده'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                try:
                    Signup.send_signup_sms(phone, request.data['username'])
                except:
                    return Response({'error': 'مشکلی در ارسال پیامک بوجود آمده'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({'success': True, 'team_code': team_code, 'is_team_head': is_team_head},
                            status=status.HTTP_200_OK)
        else:
            # TODO - add individual signup
            return Response({'success': True}, status=status.HTTP_200_OK)

    @staticmethod
    def send_signup_sms(phone_number, username, team_code=None):
        api = KAVENEGAR_TOKEN
        params = {
            'receptor': phone_number,
            'template': 'signupNew' if team_code else 'signupTeam',
            'token': username,
            'type': 'sms'
        }
        if team_code:
            params['token2'] = team_code
        api.verify_lookup(params)


class SendVerifyCode(APIView):
    permission_classes = (permissions.AllowAny,)

    @transaction.atomic
    def post(self, request):
        code = Member.objects.make_random_password(length=5, allowed_chars='1234567890')
        phone_number = request.data['phone']
        other_codes = VerifyCode.objects.filter(phone_number=phone_number, is_valid=True)
        for c in other_codes:
            c.is_valid = False
            c.save()
        verify_code = VerifyCode.objects.create(code=code, phone_number=phone_number,
                                                expiration_date=datetime.now(pytz.timezone('Asia/Tehran')) + timedelta(
                                                    minutes=5))
        try:
            verify_code.send_sms(request.data['code_type'])
        except:
            return Response({'error': 'مشکلی در ارسال پیامک بوجود آمده'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'success': True}, status=status.HTTP_200_OK)


class GetTeamData(APIView):
    # after verifying phone number
    parser_class = (MultiPartParser,)
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        # TODO Hard coded event name - get data
        current_event = Event.objects.get(name='مسافر صفر')
        if current_event.event_type != 'team':
            return Response({'success': False, "error": "این رویداد گروهی نیست."},
                            status=status.HTTP_400_BAD_REQUEST)
        if 'team_code' not in request.data or request.data['team_code'] == '':
            return Response({'success': False, "error": "لطفا کد تیم را وارد کنید."},
                            status=status.HTTP_400_BAD_REQUEST)
        team_code = request.data['team_code']
        try:
            team = Team.objects.get(team_code=team_code)
        except Team.DoesNotExist:
            return Response({'success': False, 'error': "کد تیم نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True,
                         'team_members': list(map(lambda p: p.member.first_name, list(team.team_participants.all())))},
                        status=status.HTTP_200_OK)


def create_team(request):
    pass


def send_team_invitation(request):
    # TODO send sms to target
    # if team count in not more than limit
    pass


def accept_team_invitation(request):
    # TODO send sms to inviter
    pass


def reject_team_invitation(request):
    # TODO send sms to inviter
    pass


@login_required
def get_participant_profile(request):
    pass


@login_required
def logout(request):
    auth_logout(request)
    return Response({'success': True}, status=status.HTTP_200_OK)


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str


def _redirect_login_with_action_status(action='payment', status=settings.OK_STATUS):
    response = redirect('/login')
    # response['Location'] += '?%s=%s' % (action, status)
    return response


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        member = Member.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Member.DoesNotExist):
        member = None
    if member is not None and account_activation_token.check_token(member, token):
        member.is_active = True
        member.save()
        member_team = member.participant.team
        if member_team is not None:
            team_active = True
            for participant in member_team.participant_set.all():
                if not participant.member.is_active:
                    team_active = False
            member_team.active = team_active
            member_team.save()

        auth_login(request, member)
        token = MyTokenObtainPairSerializer.get_token(member)
        # return redirect('home')
        return _redirect_login_with_action_status('activate', settings.OK_STATUS)
    elif member is not None and member.is_active:
        return _redirect_login_with_action_status('activate', settings.HELP_STATUS)
    else:
        return _redirect_login_with_action_status('activate', settings.ERROR_STATUS)


class ChangePass(APIView):

    def post(self, request):
        user = JWTAuthentication.get_user(self, JWTAuthentication.get_validated_token(self,
                                                                                      JWTAuthentication.get_raw_token(
                                                                                          self,
                                                                                          JWTAuthentication.get_header(
                                                                                              JWTAuthentication,
                                                                                              request))))
        new_pass = request.data['newPass']
        # username = request.POST.get('username')
        # member = get_object_or_404(Member, username=username)
        user.set_password(new_pass)
        user.save()

        return Response({'success': True}, status=status.HTTP_200_OK)


class UserInfo(APIView):

    def get(self, request):
        member = request.user
        if "uuid" in request.GET:
            member = Member.objects.filter(uuid=request.GET.get('uuid'))
            if not member.count() > 0:
                return Response({'success': False, "error": "user not found"}, status=status.HTTP_400_BAD_REQUEST)
            member = member[0]
        response = get_member_json_info(member)
        return Response(response)


class TeamInfo(APIView):

    def get(self, request):
        member = request.user
        if "teamId" in request.GET:
            team = Team.objects.filter(id=request.GET.get('teamId'))
            if not team.count() > 0:
                return Response({'success': False, "error": "user not found"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                team = team[0]
        elif "uuid" in request.GET:
            team = Team.objects.filter(uuid=request.GET.get('uuid'))
            if not team.count() > 0:
                return Response({'success': False, "error": "user not found"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                team = team[0]
        else:
            team = request.user.participant.team

        if not team:
            return Response({'success': False, "error": "team not found"}, status=status.HTTP_400_BAD_REQUEST)
        response = get_team_json_info(team)
        return Response(response)


class Teams(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        start = datetime.now()
        print(datetime.now())
        valid_teams = TeamsCache.get_data()
        end = datetime.now()
        print(datetime.now())
        dureation = end - start
        print(dureation)
        print("--------------------------------------")

        return Response(valid_teams)


class UploadAnswerView(APIView):
    parser_class = (FileUploadParser,)

    # permission_classes = (permissions.AllowAny,)
    @transaction.atomic
    def post(self, request):
        if 'file' not in request.data:
            raise ParseError("Empty content")

        file = request.data['file']
        user = JWTAuthentication.get_user(self, JWTAuthentication.get_validated_token(self,
                                                                                      JWTAuthentication.get_raw_token(
                                                                                          self,
                                                                                          JWTAuthentication.get_header(
                                                                                              JWTAuthentication,
                                                                                              request))))
        file.name = str(user.username) + "-" + file.name
        participant = user.participant

        old_file = None
        if participant.ent_answer:
            old_file = participant.ent_answer
        participant.ent_answer = file
        participant.save()
        if old_file is not None:
            if os.path.isfile(old_file.path):
                os.remove(old_file.path)

        return Response({'success': True}, status=status.HTTP_201_CREATED)


class PayView(APIView):
    ZARINPAL_CONFIG = settings.ZARINPAL_CONFIG

    def __get_amount(self, user):
        return self.ZARINPAL_CONFIG['TEAM_FEE'] if user.team else self.ZARINPAL_CONFIG['PERSON_FEE']

    def get(self, request, *args, **kwargs):
        user = Participant.objects.filter(member=request.user)
        response = dict()
        status_r = int()
        if user:
            user = user[0]
            if user.accepted and not user.is_activated:
                amount = self.__get_amount(user)
                res = zarinpal.send_request(amount=amount,
                                            call_back_url=f'{request.build_absolute_uri("verify-payment")}?uuid={user.member.uuid}')
                status_r = res["status"]
                response = {
                    "message": res["message"],
                    "amount": amount,
                    "typePayment": "team" if user.team else "person"
                } if status_r == 201 else {
                    "message": res["message"]
                }
            elif not user.accepted:
                response = {
                    "message": "دانش آموز عزیز به علت تایید نشدن حساب کاربری شما امکان پرداخت وجود ندارد",
                }
                status_r = 403
            elif user.is_activated:
                response = {
                    "message": "دانش آموز عزیز هزینه ثبت نام قبلا پرداخت شده است.",
                }
                status_r = 403
        else:
            response = {
                "message": "حساب کاربری شما به عنوان شرکت کننده ثبت نشده است",
            }
            status_r = 403
        return Response(response, status=status_r)


class VerifyPayView(APIView):
    ZARINPAL_CONFIG = settings.ZARINPAL_CONFIG
    permission_classes = (permissions.AllowAny,)

    def __random_string(self, length=10):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))

    def __get_amount(self, user):
        return self.ZARINPAL_CONFIG['TEAM_FEE'] if user.team else self.ZARINPAL_CONFIG['PERSON_FEE']

    def get(self, request, *args, **kwargs):
        user = Participant.objects.filter(member__uuid=request.GET.get('uuid'))
        logger.warning(request.META.get('HTTP_X_FORWARDED_FOR'))
        logger.warning(request.META.get('REMOTE_ADDR'))
        if user:
            user = user[0]
            amount = self.__get_amount(user)
            random_s = self.__random_string()
            logger.warning(f'Zarinpal callback: {request.GET}')
            res = zarinpal.verify(status=request.GET.get('Status'),
                                  authority=request.GET.get('Authority'),
                                  amount=amount)
            if 200 <= int(res["status"]) <= 299:
                if user.team:
                    team = Participant.objects.filter(team=user.team)
                    # Update is_activated for member of a group
                    for participant in team:
                        participant.is_activated = True
                    Participant.objects.bulk_update(team, ['is_activated'])
                else:
                    user.is_activated = True
                    user.save()
                Payment.objects.create(user=user,
                                       amount=amount,
                                       ref_id=str(res['ref_id']),
                                       authority=request.GET.get('Authority'),
                                       status="SUCCESS" if res["status"] == 200 else "REPETITIOUS",
                                       uniq_code=random_s)
                return redirect(f'{settings.PAYMENT["FRONT_HOST_SUCCESS"]}{random_s}')
            else:
                Payment.objects.create(user=user,
                                       amount=amount,
                                       authority=request.GET.get('Authority'),
                                       status="FAILED",
                                       uniq_code=random_s)
                return redirect(f'{settings.PAYMENT["FRONT_HOST_FAILURE"]}{random_s}')
        else:
            return Response(
                {"message": "حساب کاربری شما به عنوان شرکت کننده ثبت نشده است"},
                status=403)

# class GroupSignup(APIView):
#     # We Are Not Using This Method
#     permission_classes = (permissions.AllowAny,)
#
#     @transaction.atomic
#     def post(self, request, format='json'):
#         members_info = request.data['data']
#         if type(members_info) is str:
#             members_info = json.loads(members_info)
#
#         # TODO change email to phone number
#         for member_info in members_info:
#             if Member.objects.filter(email__exact=member_info['email']).count() > 0:
#                 return Response(
#                     {'success': False, "error": "فردی با ایمیل " + member_info['email'] + " قبلا ثبت‌نام کرده"},
#                     status=status.HTTP_400_BAD_REQUEST)
#
#         if (members_info[0]['email'] == members_info[1]['email']
#                 or members_info[1]['email'] == members_info[2]['email']
#                 or members_info[2]['email'] == members_info[0]['email']):
#             return Response({'success': False, "error": "ایمیلهای اعضای گروه باید متمایز باشد."},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         if not (members_info[0]['gender'] == members_info[1]['gender']
#                 and members_info[2]['gender'] == members_info[1]['gender']):
#             return Response({'success': False, "error": "اعضای گروه باید همه دختر یا همه پسر باشند."},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         if 'document1' not in request.data:
#             raise ParseError("Empty content document1")
#         doc0 = request.data['document1']
#         doc0.name = str(members_info[0]['email']) + "-" + doc0.name
#         if 'document2' not in request.data:
#             raise ParseError("Empty content document2")
#         doc1 = request.data['document2']
#         doc1.name = str(members_info[1]['email']) + "-" + doc1.name
#         if 'document3' not in request.data:
#             raise ParseError("Empty content document3")
#         doc2 = request.data['document3']
#         doc2.name = str(members_info[2]['email']) + "-" + doc2.name
#
#         member0 = Member.objects.create(
#             first_name=members_info[0]['name'],
#             username=members_info[0]['email'],
#             email=members_info[0]['email'],
#             is_active=False,
#             city=members_info[0]['city'],
#             school=members_info[0]['school'],
#             grade=members_info[0]['grade'],
#             phone_number=members_info[0]['phone'],
#             gender=members_info[0]['gender'],
#             document=doc0
#
#         )
#
#         member0.set_password(members_info[0]['password'])
#         participant0 = Participant.objects.create(
#             member=member0,
#
#         )
#
#         member1 = Member.objects.create(
#             first_name=members_info[1]['name'],
#             username=members_info[1]['email'],
#             email=members_info[1]['email'],
#             is_active=False,
#             gender=members_info[1]['gender'],
#             city=members_info[1]['city'],
#             school=members_info[1]['school'],
#             grade=members_info[1]['grade'],
#             phone_number=members_info[1]['phone'],
#             document=doc1
#         )
#         password1 = get_random_alphanumeric_string(8)
#
#         member1.set_password(password1)
#         participant1 = Participant.objects.create(member=member1)
#
#         member2 = Member.objects.create(
#             first_name=members_info[2]['name'],
#             username=members_info[2]['email'],
#             email=members_info[2]['email'],
#             is_active=False,
#             gender=members_info[2]['gender'],
#             city=members_info[2]['city'],
#             school=members_info[2]['school'],
#             grade=members_info[2]['grade'],
#             phone_number=members_info[2]['phone'],
#             document=doc2
#         )
#         password2 = get_random_alphanumeric_string(8)
#         member2.set_password(password2)
#         participant2 = Participant.objects.create(member=member2)
#
#         team = Team()
#         participant0.team = team
#         participant1.team = team
#         participant2.team = team
#         team.save()
#         member0.save()
#         participant0.save()
#         member1.save()
#         participant1.save()
#         member2.save()
#         participant2.save()
#
#         absolute_uri = request.build_absolute_uri('/')[:-1].strip("/")
#         member0.send_signup_email(absolute_uri)
#         member1.send_signup_email(absolute_uri, password1)
#         member2.send_signup_email(absolute_uri, password2)
#
#         return Response({'success': True}, status=status.HTTP_200_OK)
