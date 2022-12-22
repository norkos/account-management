import random
import threading

from locust import HttpUser, task, between

from integration_tests.env import URL, TOKEN
from integration_tests.utils import generate_account_details, generate_region, generate_is_vip, generate_agent_details

lock = threading.Lock()


def locker(fun):
    def wrapper(*args, **kwargs):
        try:
            lock.acquire()
            return fun(*args, **kwargs)
        finally:
            lock.release()
    return wrapper


class LocustUser(HttpUser):
    wait_time = between(1, 5)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._url = URL
        self._header = TOKEN
        self._accounts = {}

    def on_start(self):
        self.client.headers = {'x-token': self._header,
                               'accept': 'application/json',
                               'Content-Type': 'application/json'}
        self.create_account()
        self.create_agent()

    @locker
    def get_random_account(self) -> str:
        account_id = random.choice(list(self._accounts.keys()))
        return account_id

    @locker
    def get_random_agent(self) -> (str, str):
        account = random.choice(list(self._accounts.keys()))
        agent = random.choice(list(self._accounts[account]))
        return account, agent

    @locker
    def add_agent(self, account: str, agent: str):
        self._accounts[account].append(agent)

    @locker
    def add_account(self, account: str):
        self._accounts[account] = []

    @task(1)
    def create_account(self):
        account_name, email = generate_account_details()
        result = self.client.post(url=f'/accounts',
                                  json={
                                      'name': account_name,
                                      'email': email,
                                      'region': generate_region(),
                                      'vip': generate_is_vip()
                                  }
                                  )
        self.add_account(result.json()['id'])

    @task(2)
    def create_agent(self):
        agent_name, agent_email = generate_agent_details()
        account_id = self.get_random_account()
        result = self.client.post(url=f'/accounts/{account_id}/agents',
                                  json={
                                      'name': agent_name,
                                      'email': agent_email
                                  }
                                  )

        self.add_agent(account_id, result.json()['id'])

    @task(4)
    def get_account(self):
        account_id = self.get_random_account()
        self.client.get(url=f'/accounts/{account_id}')

    @task(5)
    def get_agent(self):
        account_id, agent_id = self.get_random_agent()
        self.client.get(url=f'/accounts/{account_id}/agents/{agent_id}')

    @task(6)
    def generate_company_report(self):
        account_id = self.get_random_account()
        self.client.post(url=f'/accounts/generate_company_report/{account_id}')

    @task(3)
    def block_agent(self):
        _, agent_id = self.get_random_agent()
        self.client.post(url=f'/agents/block_agent/{agent_id}')

    @task(3)
    def unblock_agent(self):
        _, agent_id = self.get_random_agent()
        self.client.post(url=f'/agents/unblock_agent/{agent_id}')
