import re

from utils import file_read_json

filename = 'data/users.json'


def analyze1():
    all_users = file_read_json(filename)
    undeleted_users = all_users['undeleted']
    deleted_users = all_users['deleted']

    users = []
    for i in undeleted_users:
        users.extend(undeleted_users[i])
    print('undeleted_users:', len(users), 'deleted_users:', len(deleted_users))

    for u in users:
        if u['phone']:
            print(u)

    # all_status = set()
    # for user in users:
    #     # print(user['status'])
    #     name = extract_status_name(user['status'])
    #     all_status.add(name)
    # print(all_status)


if __name__ == '__main__':
    analyze1()
    pass
