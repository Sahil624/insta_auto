import datetime
import os
import pickle
import random
import re
import time

import fake_useragent
from instaloader import instaloader
import requests

from bot.consts import LIST_OF_FAKE_UA
from bot.core.insta_explorer import Explorer
from bot.core.media_manager import MediaManager
from bot.core.user_info import UserInfo
from bot.models import FakeUA
from users.models import User


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
    login_credentials = {}
    media_manager = None
    media_by_tag = []

    def __init__(self, login, password):
        try:

            self.user_instance = User.objects.get(username=login)
            self.password = password
            try:
                fallback = random.sample(LIST_OF_FAKE_UA, 1)
                fake_ua = fake_useragent.UserAgent(fallback=fallback[0])
                self.user_agent = self.check_and_insert_user_agent(str(fake_ua))
                self.configurations = self.user_instance.configuration.__dict__

            except Exception as e:
                fake_ua = random.sample(LIST_OF_FAKE_UA, 1)
                self.user_agent = self.check_and_insert_user_agent(str(fake_ua[0]))

            self.instaloader = instaloader.Instaloader()

            self.bot_creation_time = datetime.datetime.now()
            self.bot_start_time = time.time()

            self.session_file = f"{self.user_instance.username}.session"
            self.session_1 = requests.Session()
            self.session_2 = requests.Session()

            self.login()
            self.media_manager = MediaManager(self)
            self.insta_explorer = Explorer(self)

        except User.DoesNotExist as e:
            print(e)

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
            print(f"Found session file {self.session_file}")
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
                print("Request didn't return 200 as status code!", login.status_code)

            login_response = login.json()

            try:
                self.csrftoken = login.cookies["csrftoken"]
                self.session_1.headers.update({"X-CSRFToken": login.cookies["csrftoken"]})
            except Exception as e:
                print("Something wrong with login", e)
                print(login.text)
            if login_response.get("errors"):
                print(
                    "Something is wrong with Instagram! Please try again later..."
                )
                for error in login_response["errors"]["error"]:
                    print(f"Error =>{error}")
                return

            if login_response.get("message") == "checkpoint_required":
                try:
                    if "instagram.com" in login_response["checkpoint_url"]:
                        challenge_url = login_response["checkpoint_url"]
                    else:
                        challenge_url = (
                            f"https://instagram.com{login_response['checkpoint_url']}"
                        )
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
                            print("Entered code is wrong, Try again later!")
                            return
                        self.csrftoken = complete_challenge.cookies["csrftoken"]
                        self.session_1.headers.update(
                            {"X-CSRFToken": self.csrftoken, "X-Instagram-AJAX": "1"}
                        )
                        logged_in = complete_challenge.status_code == 200

                except Exception as err:
                    print(f"Login failed, response: \n\n{login.text} {err}")
                    quit()
            elif login_response.get("authenticated") is False:
                print("Login error! Check your login data!")
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
            print('Logged in', logged_in, 'sleeping')
            time.sleep(5 * random.random())
            print('waked up')

        if logged_in:
            print('go go go')
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
                        print(
                            f"Saving cookies to session file {self.session_file}"
                        )
                        with open(self.session_file, "wb") as output:
                            pickle.dump(self.session_1.cookies, output, pickle.HIGHEST_PROTOCOL)
                else:
                    self.login_status = False
                    print("Login error! Check your login data!")
                    if self.session_file is not None and os.path.isfile(self.session_file):
                        try:
                            os.remove(self.session_file)
                        except Exception as e:
                            print(
                                "Could not delete session file. Please delete manually", e
                            )

                    # self.prog_run = False
            except requests.exceptions.ConnectionError:
                print('Problem with internet connectivity')
        else:
            print("Login error! Connection error!")

    def check_and_insert_user_agent(self, user_agent):
        try:
            fake_agent = FakeUA.objects.filter(user=self.user_instance)
            if len(fake_agent) is 0:
                FakeUA.objects.create(fake_user_agent=user_agent, user=self.user_instance)
                return user_agent
            else:
                return fake_agent[0].fake_user_agent
        except Exception as e:
            return user_agent
