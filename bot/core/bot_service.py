import atexit
import datetime
import os
import pickle
import random
import re
import signal
import sys
import time

import fake_useragent
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils import timezone
from instaloader import instaloader

from bot.consts import LIST_OF_FAKE_UA
from bot.core.comment_manager import CommentManager
from bot.core.follow_manager import FollowManager
from bot.core.insta_explorer import Explorer
from bot.core.like_manager import LikeManager
from bot.core.media_manager import MediaManager
from bot.core.unfollow_manager import UnfollowManager
from bot.core.user_info import UserInfo
from bot.models import FakeUA, WhiteListedUser, BotSession
from users_profile.models import UserProfile


class InstagramBot:
    url = "https://www.instagram.com/"
    url_tag = "https://www.instagram.com/explore/tags/%s/?__a=1"
    url_location = "https://www.instagram.com/explore/locations/%s/?__a=1"
    url_likes = "https://www.instagram.com/web/likes/%s/like/"
    url_unlike = "https://www.instagram.com/web/likes/%s/unlike/"
    url_comment = "https://www.instagram.com/web/comments/%s/add/"
    url_follow = "https://www.instagram.com/web/friendships/%s/follow/"
    url_unfollow = "https://www.instagram.com/web/friendships/%s/unfollow/"
    url_login = "https://www.instagram.com/accounts/login/ajax/"
    url_logout = "https://www.instagram.com/accounts/logout/"
    url_media_detail = "https://www.instagram.com/p/%s/?__a=1"
    url_media = "https://www.instagram.com/p/%s/"
    url_user_detail = "https://www.instagram.com/%s/"
    api_user_detail = "https://i.instagram.com/api/v1/users/%s/info/"

    user_agent = "" ""
    accept_language = "en-US,en;q=0.5"
    csrftoken = ""
    user_info = None
    login_status = False
    user_id = None
    unfollow_counter = 0
    like_counter = 0
    login_credentials = {}
    bot_follow_list = []
    follow_counter = 0
    media_manager = None
    media_by_tag = []
    user_blacklist = {}
    this_tag_like_count = 0
    bot_run_time = None
    unfollow_whitelist = [],
    comments_counter = 0
    max_like_for_one_tag = 0
    max_tag_like_count = 0
    prog_run = True

    # If instagram ban you - query return 400 error.
    error_400 = 0
    # If you have 3 400 error in row - looks like you banned.
    error_400_to_ban = 3
    # If InstaBot think you are     banned - going to sleep.
    ban_sleep_time = 3 * 60 * 60

    next_iteration = {
        "Like": 0,
        "Unlike": 0,
        "Follow": 0,
        "Unfollow": 0,
        "Comments": 0,
        "Populate": 0,
    }

    def __init__(self, login, password):
        try:

            self.user_instance = UserProfile.objects.get(username=login)
            self.user = self.user_instance.user

            self.password = password
            self.logger = self.user_instance.get_user_logger()
            self.configurations = self.user_instance.configuration

            try:
                fallback = random.sample(LIST_OF_FAKE_UA, 1)
                fake_ua = fake_useragent.UserAgent(fallback=fallback[0])
                self.user_agent = self.check_and_insert_user_agent(str(fake_ua))

            except Exception as e:
                self.logger.warning('Exception in creating fake user', e)
                fake_ua = random.sample(LIST_OF_FAKE_UA, 1)
                self.user_agent = self.check_and_insert_user_agent(str(fake_ua[0]))

            self.instaloader = instaloader.Instaloader()
            self.time_in_day = 24 * 60 * 60
            self.unfollow_whitelist = list(WhiteListedUser.objects.values_list('username', flat=True))
            self.like_delay = self.time_in_day / self.configurations.likes_per_day

            try:
                self.bot_session = BotSession.objects.create(user=self.user_instance, bot_creation_time=timezone.now())
            except Exception as e:
                print('Exception in adding bot session in model' + str(e))
                return

            self.unlike_per_day = self.configurations.unlike_per_day
            if self.configurations.unlike_per_day and self.configurations.unlike_per_day != 0:
                self.unlike_per_day = self.time_in_day / self.unlike_per_day

            if self.configurations.follow_per_day != 0:
                self.follow_delay = self.time_in_day / self.configurations.follow_per_day

            if self.configurations.comments_per_day != 0:
                self.comments_delay = self.time_in_day / self.configurations.comments_per_day

            if self.configurations.unfollow_per_day != 0:
                self.unfollow_delay = self.time_in_day / self.configurations.unfollow_per_day

            self.bot_creation_time = datetime.datetime.now()
            self.bot_start_time = time.time()
            self.bot_mode = 0

            self.session_file = f"{self.user_instance.username}.session"
            self.session_1 = requests.Session()
            self.session_2 = requests.Session()

            self.login()
            self.set_blacked_list_user_dict()
            self.media_manager = MediaManager(self)
            self.insta_explorer = Explorer(self)
            self.insta_explorer.populate_user_blacklist()
            self.like_manager = LikeManager(self)
            self.comment_manager = CommentManager(self)
            self.follow_manager = FollowManager(self)
            self.unfollow_manager = UnfollowManager(self)

            signal.signal(signal.SIGINT, self.stop_bot)
            signal.signal(signal.SIGTERM, self.stop_bot)
            atexit.register(self.stop_bot)

        except User.DoesNotExist as e:
            self.logger.error('User does not exist', str(e))

        except Exception as e:
            print(e)

    def set_blacked_list_user_dict(self):
        blacked_listed_users_obj = self.user_instance.blacklisted_users.all()

        if len(blacked_listed_users_obj):
            for user in blacked_listed_users_obj:
                self.user_blacklist[user.username] = ''

    def login(self):

        logged_in = False

        self.session_1.headers.update(
            {
                "Accept": "*/*",
                "Accept-Language": self.accept_language,
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Host": "www.instagram.com",
                "Origin": "https://www.instagram.com",
                "Referer": "https://www.instagram.com/",
                "User-Agent": self.user_agent,
                "X-Instagram-AJAX": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        if self.session_file is not None and os.path.isfile(self.session_file):
            self.logger.info(f"Found session file {self.session_file}")
            self.send_to_socket(f"Found session file {self.session_file}")
            logged_in = True
            with open(self.session_file, "rb") as i:
                cookies = pickle.load(i)
                self.session_1.cookies.update(cookies)

        else:
            self.login_credentials = {
                "username": self.user_instance.username,
                "password": self.password
            }

            response = self.session_1.get(self.url)
            csrf_token = re.search('(?<="csrf_token":")\w+', response.text).group(0)
            self.session_1.headers.update({"X-CSRFToken": csrf_token})
            time.sleep(5 * random.random())

            login = self.session_1.post(
                self.url_login,
                data=self.login_credentials,
                allow_redirects=True
            )
            print('login status code', login.status_code)
            if login.status_code != 200 and login.status_code != 400:
                self.logger.error("Request didn't return 200 as status code!", login.status_code)
                self.send_to_socket("Request didn't return 200 as status code! Status code :-" + str(login.status_code))

            login_response = login.json()

            try:
                self.csrftoken = login.cookies["csrftoken"]
                self.session_1.headers.update({"X-CSRFToken": login.cookies["csrftoken"]})
            except Exception as e:
                self.send_to_socket("Something wrong with login" + str(e))
                self.logger.error("Something wrong with login", e)
                print(login.text)
            if login_response.get("errors"):
                print(
                    "Something is wrong with Instagram! Please try again later..."
                )
                self.send_to_socket("Something is wrong with Instagram! Please try again later...")
                for error in login_response["errors"]["error"]:
                    self.send_to_socket(error)
                    self.logger.error(error)
                return

            if login_response.get("message") == "checkpoint_required":
                try:
                    if "instagram.com" in login_response["checkpoint_url"]:
                        challenge_url = login_response["checkpoint_url"]
                    else:
                        challenge_url = (
                            f"https://instagram.com{login_response['checkpoint_url']}"
                        )
                    self.logger.warning(f"Challenge required at {challenge_url}")
                    self.send_to_socket(f"Challenge required at {challenge_url}")
                    print(f"Challenge required at {challenge_url}")
                    with self.session_1 as clg:
                        clg.headers.update(
                            {
                                "Accept": "*/*",
                                "Accept-Language": self.accept_language,
                                "Accept-Encoding": "gzip, deflate, br",
                                "Connection": "keep-alive",
                                "Host": "www.instagram.com",
                                "Origin": "https://www.instagram.com",
                                "User-Agent": self.user_agent,
                                "X-Instagram-AJAX": "1",
                                "Content-Type": "application/x-www-form-urlencoded",
                                "x-requested-with": "XMLHttpRequest",
                            }
                        )
                        # Get challenge page
                        challenge_request_explore = clg.get(challenge_url)

                        # Get CSRF Token from challenge page
                        challenge_csrf_token = re.search(
                            '(?<="csrf_token":")\w+', challenge_request_explore.text
                        ).group(0)
                        # Get Rollout Hash from challenge page
                        rollout_hash = re.search(
                            '(?<="rollout_hash":")\w+', challenge_request_explore.text
                        ).group(0)

                        # Ask for option 1 from challenge, which is usually Email or Phone
                        challenge_post = {"choice": 1}

                        # Update headers for challenge submit page
                        clg.headers.update({"X-CSRFToken": challenge_csrf_token})
                        clg.headers.update({"Referer": challenge_url})

                        # Request instagram to send a code
                        challenge_request_code = clg.post(
                            challenge_url, data=challenge_post, allow_redirects=True
                        )

                        # User should receive a code soon, ask for it
                        challenge_userinput_code = input(
                            "Challenge Required.\n\nEnter the code sent to your mail/phone: "
                        )
                        challenge_security_post = {
                            "security_code": int(challenge_userinput_code)
                        }

                        complete_challenge = clg.post(
                            challenge_url,
                            data=challenge_security_post,
                            allow_redirects=True,
                        )
                        if complete_challenge.status_code != 200:
                            self.logger.warning("Entered code is wrong, Try again later!")
                            self.send_to_socket("Entered code is wrong, Try again later!")
                            print("Entered code is wrong, Try again later!")
                            return
                        self.csrftoken = complete_challenge.cookies["csrftoken"]
                        self.session_1.headers.update(
                            {"X-CSRFToken": self.csrftoken, "X-Instagram-AJAX": "1"}
                        )
                        logged_in = complete_challenge.status_code == 200

                except Exception as err:
                    print(f"Login failed, response: \n\n{login.text} {err}")
                    self.logger.error("Login failed, response: \n\n{login.text} {err}")
                    self.send_to_socket("Login failed, response: \n\n{login.text} {err}")
                    quit()
            elif login_response.get("authenticated") is False:
                print("Login error! Check your login data!")
                self.logger.error("Login error! Check your login data!")
                self.send_to_socket("Login error! Check your login data!")
                return

            else:
                rollout_hash = re.search('(?<="rollout_hash":")\w+', response.text).group(0)
                self.session_1.headers.update({"X-Instagram-AJAX": rollout_hash})
                logged_in = True

            self.session_1.cookies["csrftoken"] = self.csrftoken
            self.session_1.cookies["ig_vw"] = "1536"
            self.session_1.cookies["ig_pr"] = "1.25"
            self.session_1.cookies["ig_vh"] = "772"
            self.session_1.cookies["ig_or"] = "landscape-primary"
            time.sleep(5 * random.random())

        if logged_in:
            self.logger.info('Logged in')
            self.send_to_socket("Logged in")
            try:
                response = self.session_1.get("https://www.instagram.com/")
                self.csrftoken = re.search('(?<="csrf_token":")\w+', response.text).group(0)
                self.session_1.cookies["csrftoken"] = self.csrftoken
                self.session_1.headers.update({"X-CSRFToken": self.csrftoken})
                finder = response.text.find(self.user_instance.username)
                if finder != -1:
                    self.user_info = UserInfo()
                    self.user_id = self.user_info.get_user_id_by_login(self.user_instance.username)
                    self.login_status = True
                    log_string = f"{self.user_instance.username} login success!\n"
                    print(log_string)
                    if self.session_file is not None:
                        self.logger.info(f'Saving cookies to session file {self.session_file}')
                        print(
                            f"Saving cookies to session file {self.session_file}"
                        )
                        with open(self.session_file, "wb") as output:
                            pickle.dump(self.session_1.cookies, output, pickle.HIGHEST_PROTOCOL)
                else:
                    self.login_status = False
                    print("Login error! Check your login data!")
                    self.logger.error("Login error! Check your login data!")
                    self.send_to_socket("Login error! Check your login data!")
                    if self.session_file is not None and os.path.isfile(self.session_file):
                        try:
                            os.remove(self.session_file)
                        except Exception as e:
                            print(
                                "Could not delete session file. Please delete manually", e
                            )
                            self.logger.error("Could not delete session file. Please delete manually", e)

                    self.prog_run = False
            except requests.exceptions.ConnectionError:
                self.logger.error('Problem with internet connectivity')
                print('Problem with internet connectivity')
        else:
            self.logger.error("Login error! Connection error!")
            print("Login error! Connection error!")

    def check_and_insert_user_agent(self, user_agent):
        try:
            fake_agent = FakeUA.objects.filter(user=self.user_instance)
            if len(fake_agent) is 0:
                self.logger.info('Created Fake UA')
                FakeUA.objects.create(fake_user_agent=user_agent, user=self.user)
                return user_agent
            else:
                return fake_agent[0].fake_user_agent
        except Exception as e:
            self.logger.info('Fake UA exception', str(e))
        return user_agent

    def run_bot(self):
        while self.prog_run and self.login_status:
            now = datetime.datetime.now()
            self.bot_run_time = timezone.now()
            self.bot_session.bot_start_time = self.bot_run_time
            self.bot_session.save()
            if (not self.configurations.start_time or self.configurations.start_time <= now.time()) and (
                    not self.configurations.ends_time or self.configurations.ends_time >= now.time()):
                # ------------------- Get media_id -------------------
                if len(self.media_by_tag) == 0:
                    if len(self.user_instance.get_tag_list()):
                        self.media_manager.get_media_id_by_tag(random.choice(self.user_instance.get_tag_list()))
                    else:
                        log = "Please specify atleast one tag for searching media"
                        self.logger.error(log)
                        self.send_to_socket(log)
                        self.stop_bot(None)

                    self.this_tag_like_count = 0
                    self.max_tag_like_count = random.randint(
                        1, self.configurations.max_like_for_one_tag
                    )
                    self.like_manager.remove_already_liked()
                # ------------------- Like -------------------
                self.like_manager.new_auto_mod_like()
                # ------------------- Unlike -------------------
                # TODO: Test unlike media
                self.like_manager.new_auto_mod_unlike()
                # ------------------- Follow -------------------
                self.follow_manager.new_auto_mod_follow()
                # # ------------------- Unfollow -------------------
                self.unfollow_manager.new_auto_mod_unfollow()
                # # ------------------- Comment -------------------
                self.comment_manager.new_auto_mod_comments()
                # # Bot iteration in 1 sec
                time.sleep(3)
                # # print("Tic!")
            else:
                self.logger.warning("!!sleeping until {hour}:{min}".format(
                    hour=self.configurations.start_at_h, min=self.configurations.start_at_m
                ))
                self.send_to_socket("!!sleeping until {hour}:{min}".format(
                    hour=self.configurations.start_at_h, min=self.configurations.start_at_m
                ))
                print(
                    "!!sleeping until {hour}:{min}".format(
                        hour=self.configurations.start_at_h, min=self.configurations.start_at_m
                    ),
                    end="\r",
                )
                time.sleep(100)
        self.send_to_socket("Exit Program... GoodBye")
        self.logger.info("Exit Program... GoodBye")
        sys.exit(0)

    def stop_bot(self, *_):
        # Unfollow all bot follow
        print("stopping bot", self.follow_counter >= self.unfollow_counter)
        if self.follow_counter >= self.unfollow_counter:
            for i in range(len(self.bot_follow_list)):
                f = self.bot_follow_list[0]
                if self.unfollow_manager.check_already_unfollowed(f[0]):
                    log_string = "Already unfollowed before, skipping: %s" % (f[0])
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                else:
                    log_string = "Trying to unfollow: %s" % (f[0])
                    self.logger.info(log_string)
                    self.unfollow_on_cleanup(f[0])
                    sleeptime = random.randint(
                        self.configurations.unfollow_break_min, self.configurations.unfollow_break_max
                    )
                    log_string = "Pausing for %i seconds... %i of %i" % (
                        sleeptime,
                        self.unfollow_counter,
                        self.follow_counter,
                    )
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    time.sleep(sleeptime)
                self.bot_follow_list.remove(f)

        # Logout
        print("will logout", self.login_status and self.session_file is None)
        if self.login_status and self.session_file is None:
            self.logout()
        self.prog_run = False

        try:
            self.bot_session.bot_stop_time = timezone.now()
            self.bot_session.save()
        except Exception as e:
            self.logger.exception("Exception in updating bot stop time in session " + str(e))

    def logout(self):
        now_time = datetime.datetime.now()
        log_string = (
                "Logout: likes - %i, follow - %i, unfollow - %i, comments - %i."
                % (
                    self.like_counter,
                    self.follow_counter,
                    self.unfollow_counter,
                    self.comments_counter,
                )
        )
        self.logger.info(log_string)
        self.send_to_socket(log_string)
        work_time = time.time() - self.bot_start_time
        log_string = f"Bot work time: {work_time}"
        self.logger.info(log_string)
        self.send_to_socket(log_string)

        try:
            logout_post = {"csrfmiddlewaretoken": self.csrftoken}
            logout = self.session_1.post(self.url_logout, data=logout_post)
            self.logger.info("Logout success!")
            self.send_to_socket(log_string)
            self.login_status = False
        except Exception as e:
            self.logger.exception("Logout error! " + str(e))

    def unfollow_on_cleanup(self, user_id):
        """ Unfollow on cleanup by @rjmayott """
        if self.login_status:
            url_unfollow = self.url_unfollow % user_id
            try:
                unfollow = self.session_1.post(url_unfollow)
                if unfollow.status_code == 200:
                    self.unfollow_counter += 1
                    try:
                        self.bot_session.unfollow_counter += 1
                        self.bot_session.save()
                    except Exception as e:
                        self.logger.exception("Exception in updating unfollow counter" + str(e))
                    log_string = f"Unfollow: {user_id} #{self.unfollow_counter} of {self.follow_counter}."
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    self.unfollow_manager.update_unfollow_count(user_id=user_id)
                else:
                    log_string = (
                        "Slow Down - Pausing for 5 minutes to avoid getting banned"
                    )
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    time.sleep(300)
                    unfollow = self.session_1.post(url_unfollow)
                    if unfollow.status_code == 200:
                        self.unfollow_counter += 1
                        try:
                            self.bot_session.unfollow_counter += 1
                            self.bot_session.save()
                        except Exception as e:
                            self.logger.exception("Exception in updating unfollow counter" + str(e))
                        log_string = f"Unfollow: {user_id} #{self.unfollow_counter} of {self.follow_counter}."
                        self.logger.info(log_string)
                        self.send_to_socket(log_string)
                        self.unfollow_manager.update_unfollow_count(user_id=user_id)
                    else:
                        log_string = "Still no good :( Skipping and pausing for another 5 minutes"
                        self.logger.info(log_string)
                        self.send_to_socket(log_string)
                        time.sleep(300)
                    return False
                return unfollow
            except Exception as e:
                self.logger.exception("Except on unfollow. " + str(e))
        return False

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + self.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
