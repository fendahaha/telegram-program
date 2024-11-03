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

from utils import file_write_json, file_read_json, chunk_list

# fendabot1
api_id = 26241828
api_hash = '5a200bcdb33eadf1de021a70c227b658'
client = TelegramClient('fendabot1', api_id, api_hash)


#########################
def extract_seconds(s):
    pattern = f'A wait of (\d+) seconds is required \(caused by InviteToChannelRequest\)'
    match = re.search(pattern, s, re.I)
    if match:
        return int(match.group(1))


def extract_status_name(s):
    p = f'^(\w+)\(.+\)$'
    match = re.search(p, s, re.I)
    if match:
        return match.group(1)
    return s


#########################

async def get_all_contacts():
    contacts = await client(GetContactsRequest(hash=0))
    all_info = []
    for entity in contacts.users:
        user_info = {
            'type': 'contact',
            'id': entity.id,
            'name': get_display_name(entity),
            'username': entity.username,
            'link': f'https://t.me/{entity.username}' if entity.username else None,
            'status': str(entity.status),
            'is_contact': entity.contact,
            'is_mutual_contact': entity.mutual_contact,
        }
        all_info.append(user_info)
    for item in all_info:
        print(item)
    return all_info


async def get_all_dialogs():
    all_info = []
    # 获取群组和频道
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        entity = dialog.entity
        group_info = {
            'type': None,
            'id': dialog.id,
            'name': '',
            'username': None,
            'link': None
        }
        if type(dialog.entity) == Channel:
            group_info['type'] = 'channel'
            group_info['name'] = entity.title
            group_info['username'] = entity.username
            group_info['link'] = f'https://t.me/{entity.username}' if entity.username else None
            group_info['is_broadcast'] = entity.broadcast
            group_info['is_megagroup'] = entity.megagroup
        elif type(dialog.entity) == Chat:
            group_info['type'] = 'chat'
            group_info['name'] = entity.title
        elif type(dialog.entity) == User:
            group_info['type'] = 'user'
            group_info['name'] = (entity.first_name or '') + (entity.last_name or '')
            group_info['username'] = entity.username
            group_info['link'] = f'https://t.me/{entity.username}' if entity.username else None
            group_info['status'] = str(entity.status)
            group_info['is_contact'] = entity.contact
            group_info['is_mutual_contact'] = entity.mutual_contact
        else:
            group_info['type'] = str(dialog.entity)
        all_info.append(group_info)

    # 打印或返回信息
    for item in all_info:
        print(item)
    return all_info


async def check_group_type1(link):
    try:
        # 获取群组或频道的实体
        entity = await client.get_entity(link)
        # 判断群组类型
        if isinstance(entity, Channel):
            if entity.broadcast:
                return entity, 'channel'
            elif entity.megagroup:
                return entity, 'megagroup'
            else:
                return entity, 'regular_group'
        elif isinstance(entity, Chat):
            return entity, 'chat'
        else:
            return entity, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None


async def check_group_type(invite_link):
    try:
        # 使用 CheckChatInviteRequest 获取群组信息
        invite = await client(CheckChatInviteRequest(invite_link))
        if hasattr(invite, 'chat'):
            if invite.chat.username:
                print("This is a public group.")
            else:
                print("This is a private group.")
    except InviteHashInvalidError:
        print("Invalid invite link.")
    except Exception as e:
        print(f"An error occurred: {e}")


async def print_all_dialogs():
    async for dialog in client.iter_dialogs():
        print(dialog.name, 'has ID', dialog.id, dialog.is_group)


async def join_group(channel):
    """
    :param channel: link,username,entity
    :return success: bool
    """
    try:
        updates = await client(JoinChannelRequest(channel))
        return len(updates.chats) > 0
    except Exception as e:
        print(f"操作失败：{e}")


async def join_private_group(group_username):
    try:
        updates = await client(ImportChatInviteRequest(group_username))
        print(updates.stringify())
    except Exception as e:
        print(f"操作失败：{e}")


async def leave_group(channel):
    """
    :param channel: link,username,entity
    :return success: bool
    """
    try:
        updates = await client(LeaveChannelRequest(channel))
        return len(updates.chats) > 0
    except Exception as e:
        print(f"操作失败：{e}")


async def get_group_or_channel_users(entity):
    """
    :param entity:id, username, link
    :return: users: List[User]
    """
    error = None
    all_users = []
    try:
        # real_id, peer_type = utils.resolve_id(chat_id)
        # group=peer_type(real_id)
        my_chat = await client.get_entity(entity)
        users = await client.get_participants(my_chat)
        for user in users:
            all_users.append({
                'id': user.id,
                'username': user.username,
                'deleted': user.deleted,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'status': str(user.status),
            })
        # print(all_users)
    except Exception as e:
        print(f"操作失败：{e}")
        error = str(e)
    return all_users, error


async def add_user_to_contacts(user_id, user_firstname, user_lastname, user_phone):
    success = False
    error = None
    try:
        result = await client(AddContactRequest(
            id=user_id,
            first_name=user_firstname or "Unknown",
            last_name=user_lastname or "",
            phone=user_phone or '',
        ))
        # print(result.stringify())
        success = True
    # except FloodWaitError as e:
    #     print(f"Rate limit reached. Sleeping for {e.seconds} seconds.")
    except Exception as e:
        error = str(e)
        print(f"操作失败：{e}")
    return success, error


async def join_user_to_regular_group(chat, user):
    # real_id, peer_type = utils.resolve_id(chat_id)
    group = await client.get_entity(chat)
    print(group)
    updates = await client(AddChatUserRequest(
        group.id,
        user,
        fwd_limit=10  # Allow the user to see the 10 last messages
    ))
    print(updates.stringify())


async def join_user_to_channel_or_megagroup(channel, user):
    success = False
    error = None
    error_name = None
    flood_wait_seconds = 0
    should_continue = True
    try:
        updates = await client(InviteToChannelRequest(
            channel,
            [user]
        ))
        # print(updates.stringify())
        # missing_invitees_ids = [getattr(i, 'user_id') for i in updates.missing_invitees]
        # return missing_invitees_ids
        success = len(updates.missing_invitees) == 0
    except Exception as e:
        print(f"操作失败：{e}", type(e))
        error = str(e)
        error_name = type(e).__name__
        if type(e) == FloodWaitError:
            flood_wait_seconds = extract_seconds(str(e)) or 0
        elif type(e) in [UserBlockedError, UserBotError, UserChannelsTooMuchError, UserIdInvalidError, UserKickedError,
                         UserNotMutualContactError, UserPrivacyRestrictedError, InputUserDeactivatedError]:
            pass
        else:
            should_continue = False
    return success, error, error_name, flood_wait_seconds, should_continue


async def create_private_megagroup_or_channel(title, about='', channel=False):
    try:
        params = {
            'title': title,
            'about': about,
        }
        if channel:
            params['broadcast'] = True
        else:
            params['for_import'] = True  # Add members
            params['megagroup'] = True
        updates = await client(CreateChannelRequest(**params))
        if len(updates.chats):
            return updates.chats[0]
    except Exception as e:
        print(f"操作失败：{e}")


async def edit_group_to_public(input_channel, username):
    try:
        success = await client(UpdateUsernameRequest(
            channel=input_channel,
            username=username
        ))
        return success
    except Exception as e:
        print(f"操作失败：{e}")


async def create_public_megagroup_or_channel(username, title, about='', channel=False, delete_on_fail=True):
    channel = await create_private_megagroup_or_channel(title, about, channel)
    if channel:
        success = False
        is_valid = await check_username_valid(channel, username)
        if is_valid:
            success = await edit_group_to_public(channel, username)
        if delete_on_fail and (not success):
            await delete_channel(channel)


async def check_username_valid(channel, username):
    """
    :param channel: channel link or entity
    :param username: string
    :return: success: bool
    """
    try:
        is_valid = client(functions.channels.CheckUsernameRequest(
            channel=channel,
            username=username
        ))
        return is_valid
    except Exception as e:
        print(f"操作失败：{e}")


async def delete_channel(channel):
    """
    :param channel: channel link or entity
    :return: success: bool
    """
    try:
        updates = await client(DeleteChannelRequest(
            channel=channel,
        ))
        return len(updates.chats) > 0
    except Exception as e:
        print(f"操作失败：{e}")


async def test0():
    # await get_all_contacts()
    dialogs = await get_all_dialogs()
    # await join_user_to_channel_or_megagroup('https://t.me/fendatestchannel1', 'cola_pls')
    # await add_user_to_contacts(6472628002, 'INK', '阿英🦋', '')
    pass


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

filename = 'users.json'
results_file = 'user_invite_results.json'


async def test():
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
    # for link in group_links:
    #     all_users = await get_group_or_channel_users(link)
    #     if all_users is None:
    #         print(link, None)
    #     else:
    #         print(link, len(all_users))

    for link in group_links:
        success = await join_group(link)
        print(success, link)
        if not success:
            break
        time.sleep(10)


async def save_users_task():
    all_users = []
    for link in group_links:
        users, error = await get_group_or_channel_users(link)
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


async def join_users_to_channel_task():
    channel_link = 'https://t.me/jobinphlg'
    channel = await client.get_input_entity(channel_link)

    exist_users, error = await get_group_or_channel_users(channel)
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
            await join_user_to_channel_or_megagroup(channel, user['id'])
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


async def main():
    await test0()
    # await test()
    # await save_users_task()
    await join_users_to_channel_task()
    # return 1


def ddd_main():
    with client:
        result = client.loop.run_until_complete(main())
        print(result)


if __name__ == '__main__':
    ddd_main()
