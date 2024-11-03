import re
import time

from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError, UserAlreadyParticipantError, InviteHashInvalidError, \
    UserNotMutualContactError, UserKickedError, UserIdInvalidError, UserChannelsTooMuchError, \
    UserPrivacyRestrictedError, InputUserDeactivatedError, UserBlockedError, UserBotError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest, InviteToChannelRequest, \
    UpdateUsernameRequest, CreateChannelRequest, DeleteChannelRequest
from telethon.tl.functions.chatlists import JoinChatlistInviteRequest
from telethon.tl.functions.contacts import AddContactRequest, GetContactsRequest
from telethon.tl.functions.messages import AddChatUserRequest, ImportChatInviteRequest, CheckChatInviteRequest, \
    GetDialogsRequest

# from telethon.tl.types import PeerChat,UserStatusOffline
from telethon.tl.custom.dialog import Dialog
from telethon.tl.types import Channel, Chat, User, InputPeerUser, PeerChat, PeerChannel
from telethon.utils import get_display_name

from common import get_client, join_group, get_group_or_channel_users, extract_status_name, \
    join_user_to_channel_or_megagroup
from utils import file_write_json, file_read_json, chunk_list

"""
    https://t.me/kaikongnaja 348
    https://t.me/jobseekers_recruiters 3064
    https://t.me/missmulan1718 648
    https://t.me/worksfreepoipet 374
    https://t.me/Wihyoii 2577
    https://t.me/jbsph99 728
    https://t.me/adhywccffcbmkoa 4466
    https://t.me/thaijobs 1530
    https://t.me/ThainPHJobs 0
    https://t.me/workworkjobjob 4354
    https://t.me/jobthai 1997
    https://t.me/JobsOverseasSince2023 834
    https://t.me/ITbusinessfgroup 3995
    https://t.me/creditfreepg 2
    https://t.me/sarith199 5
    """
group_links = [
    'https://t.me/kaikongnaja',
    'https://t.me/jobseekers_recruiters',
    'https://t.me/missmulan1718',
    'https://t.me/worksfreepoipet',
    'https://t.me/Wihyoii',
    'https://t.me/jbsph99',
    'https://t.me/adhywccffcbmkoa',
    'https://t.me/thaijobs',
    'https://t.me/ThainPHJobs',
    'https://t.me/workworkjobjob',
    'https://t.me/jobthai',
    'https://t.me/JobsOverseasSince2023',
    'https://t.me/ITbusinessfgroup',
    'https://t.me/creditfreepg',
    'https://t.me/sarith199',
]

filename = 'data/users.json'
results_file = 'data/user_invite_results.json'


async def test(client):
    # for link in group_links:
    #     all_users = await get_group_or_channel_users(client,link)
    #     if all_users is None:
    #         print(link, None)
    #     else:
    #         print(link, len(all_users))

    for link in group_links:
        success = await join_group(client, link)
        print(success, link)
        if not success:
            break
        time.sleep(10)


async def get_groups_users(client):
    all_users = []
    for link in group_links:
        users, error = await get_group_or_channel_users(client, link)
        all_users.extend(users)
        print('access', link, error)
        if error:
            break
        time.sleep(5)
    # 去重
    users_map = {i['id']: i for i in all_users}
    all_users = users_map.values()
    # 分组
    deleted_users = []
    undeleted_users = []
    for user in all_users:
        if user['deleted']:
            deleted_users.append(user)
        else:
            undeleted_users.append(user)
    # 分组
    user_status_map = {}
    for user in undeleted_users:
        status_name = extract_status_name(user['status'])
        if status_name in user_status_map:
            user_status_map[status_name].append(user)
        else:
            user_status_map[status_name] = [user]

    all_users = {
        'undeleted': user_status_map,
        'deleted': deleted_users,
    }
    file_write_json(all_users, filename)


def get_undeleted_users(users, status):
    undeleted_users = users['undeleted']
    status = status or ['UserStatusRecently', 'UserStatusOnline', 'UserStatusLastWeek', 'UserStatusLastMonth',
                        'UserStatusOffline', 'None']
    # UserStatusRecently UserStatusOnline UserStatusLastWeek UserStatusLastMonth UserStatusOffline None
    users_to_process = []
    for s in status:
        users_to_process.extend(undeleted_users.get(s, []))
    return users_to_process


def get_cant_invite_users(user_invite_results):
    ids = []
    for result in user_invite_results:
        if not result['success']:
            if not result['error']:
                ids.append(result['user_id'])
            elif result['error_name'] in ['UserBlockedError', 'UserBotError', 'UserChannelsTooMuchError',
                                          'UserIdInvalidError', 'UserKickedError', 'UserNotMutualContactError',
                                          'UserPrivacyRestrictedError', 'InputUserDeactivatedError']:
                ids.append(result['user_id'])
    return ids


async def join_users_to_channel(client):
    channel_link = 'https://t.me/jobinphlg'
    channel = await client.get_input_entity(channel_link)

    exist_users, error = await get_group_or_channel_users(client, channel)
    if error:
        print(error)
        return
    exist_user_ids = [u['id'] for u in exist_users]

    user_invite_results = file_read_json(results_file)
    cant_invite_users_ids = get_cant_invite_users(user_invite_results)

    users = file_read_json(filename)
    undeleted_users = get_undeleted_users(users, ['UserStatusOffline'])

    no_exist_users = [user for user in undeleted_users if user['id'] not in exist_user_ids]
    no_exist_users = [user for user in no_exist_users if user['id'] not in cant_invite_users_ids]

    print('no_exist_users:', len(no_exist_users))
    for user in no_exist_users:
        success, error, error_name, flood_wait_seconds, should_continue = \
            await join_user_to_channel_or_megagroup(client, channel, user['id'])
        print([user['username'], success, error, flood_wait_seconds, should_continue])
        user_invite_results.append({'user_id': user['id'], 'username': user['username'],
                                    'success': success, 'error_name': error_name, 'error': error})
        if (not should_continue) or (flood_wait_seconds > 0):
            break
        if flood_wait_seconds:
            time.sleep(flood_wait_seconds)
        else:
            time.sleep(10)
    file_write_json(user_invite_results, results_file)


async def tasks(client):
    # await test(client)
    # await get_groups_users(client)
    await join_users_to_channel(client)
    # return 1


def main():
    client = get_client('fendabot1')
    with client:
        result = client.loop.run_until_complete(tasks(client))


if __name__ == '__main__':
    main()
