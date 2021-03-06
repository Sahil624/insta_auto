import json
import requests
import re


class UserInfo:
    """
    This class try to take some user info (following, followers, etc.)
    """

    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36"
    )
    url_user_info = "https://www.instagram.com/%s/"
    url_list = {
        "ink361": {
            "main": "http://ink361.com/",
            "user": "http://ink361.com/app/users/%s",
            "search_name": "https://data.ink361.com/v1/users/search?q=%s",
            "search_id": "https://data.ink361.com/v1/users/ig-%s",
            "followers": "https://data.ink361.com/v1/users/ig-%s/followed-by",
            "following": "https://data.ink361.com/v1/users/ig-%s/follows",
            "stat": "http://ink361.com/app/users/ig-%s/%s/stats",
        }
    }
    session = None
    user_name = None
    user_id = None
    followers = []
    following = []

    def __init__(self, info_aggregator="ink361"):
        self.i_a = info_aggregator
        self.handshake()

    def handshake(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        main = self.session.get(self.url_list[self.i_a]["main"])
        if main.status_code == 200:
            return True
        return False

    def get_user_id_by_login(self, user_name):
        url_info = self.url_user_info % user_name
        info = self.session.get(url_info)
        json_info = json.loads(
            re.search(
                "window._sharedData = (.*?);</script>", info.text, re.DOTALL
            ).group(1)
        )
        id_user = json_info["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]
        return id_user

    def search_user(self, user_id=None, user_name=None):
        """
        Search user_id or user_name, if you don't have it.
        """
        self.user_id = user_id or False
        self.user_name = user_name or False

        if not self.user_id and not self.user_name:
            # you have nothing
            return False
        elif self.user_id:
            # you have just id
            search_url = self.url_list[self.i_a]["search_id"] % self.user_id
        elif self.user_name:
            # you have just name
            search_url = self.url_list[self.i_a]["search_name"] % self.user_name
        else:
            # you have id and name
            return True

        search = self.session.get(search_url)

        if search.status_code == 200:
            r = json.loads(search.text)
            if self.user_id:
                # you have just id
                self.user_name = r["data"]["username"]
            else:
                for u in r["data"]:
                    if u["username"] == self.user_name:
                        t = u["id"].split("-")
                        self.user_id = t[1]
                # you have just name
            return True
        return False

    def get_followers(self, limit=-1):
        self.followers = None
        self.followers = []
        if self.user_id:
            next_url = self.url_list[self.i_a]["followers"] % self.user_id
            while True:
                followers = self.session.get(next_url)
                r = json.loads(followers.text)
                for u in r["data"]:
                    if limit > 0 or limit < 0:
                        self.followers.append(
                            {
                                "username": u["username"],
                                # "profile_picture": u["profile_picture"],
                                "id": u["id"].split("-")[1],
                                # "full_name": u["full_name"]
                            }
                        )
                        limit -= 1
                    else:
                        return True
                if r["pagination"]["next_url"]:
                    # have more data
                    next_url = r["pagination"]["next_url"]
                else:
                    # end of data
                    return True
        return False

    def get_following(self, limit=-1):
        self.following = None
        self.following = []
        if self.user_id:
            next_url = self.url_list[self.i_a]["following"] % self.user_id
            while True:
                following = self.session.get(next_url)
                r = json.loads(following.text)
                for u in r["data"]:
                    if limit > 0 or limit < 0:
                        self.following.append(
                            {
                                "username": u["username"],
                                # "profile_picture": u["profile_picture"],
                                "id": u["id"].split("-")[1],
                                # "full_name": u["full_name"]
                            }
                        )
                        limit -= 1
                    else:
                        return True
                if r["pagination"]["next_url"]:
                    # have more data
                    next_url = r["pagination"]["next_url"]
                else:
                    # end of data
                    return True
        return False

