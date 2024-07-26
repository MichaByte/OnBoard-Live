import secrets
import requests
import pickle

users = {}

with open('users.dat', 'rb') as f:
    users = pickle.load(f)

def add_stream(stream):
    requests.post('http://127.0.0.1:9997/v3/config/paths/add/' + stream, json={'name': stream})

def main():
    print(users)
    for user in users.values():
        add_stream(user)
    while True:
        new_user = input('Enter new user\'s Slack ID: ')
        if new_user in users:
            print('User already exists.')
            continue
        users[new_user] = secrets.token_hex(32)
        print(users[new_user])
        add_stream(users[new_user])
        with open('users.dat', 'wb') as f:
            pickle.dump(users, f)


if __name__ == '__main__':
    main()
