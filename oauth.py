import requests
import config

class Oauth:
    client_id = config.CLIENT_ID
    client_secret = config.CLIENT_SECRET
    redirect_uri = config.REDIRECT_URI
    discord_login_url = config.DISCORD_LOGIN_URL
    discord_api_endpoint = config.DISCORD_API_ENDPOINT

    @staticmethod
    def get_access_token(code):
        data = {
            'client_id': config.CLIENT_ID,
            'client_secret': config.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': config.REDIRECT_URI
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post('%s/oauth2/token' % Oauth.discord_api_endpoint, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


    @staticmethod
    def get_user(access_token):
        response = requests.get(url=f"{Oauth.discord_api_endpoint}/users/@me", headers={"authorization": f"Bearer {access_token}"})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_user_guilds(access_token):
        response = requests.get(url=f"{Oauth.discord_api_endpoint}/users/@me/guilds", headers={"authorization": f"Bearer {access_token}"})
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_bot_guilds():
        response = requests.get(url=f"{Oauth.discord_api_endpoint}/users/@me/guilds", headers={"authorization": f"Bot {config.BOT_TOKEN}"})
        response.raise_for_status()
        return response.json()
