import re

from telethon import TelegramClient, functions
from telethon.errors import FloodWaitError, InviteHashInvalidError, \
    UserNotMutualContactError, UserKickedError, UserIdInvalidError, UserChannelsTooMuchError, \
    UserPrivacyRestrictedError, InputUserDeactivatedError, UserBlockedError, UserBotError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest, InviteToChannelRequest, \
    UpdateUsernameRequest, CreateChannelRequest, DeleteChannelRequest
from telethon.tl.functions.contacts import AddContactRequest, GetContactsRequest
from telethon.tl.functions.messages import AddChatUserRequest, ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.types import Channel, Chat, User
from telethon.utils import get_display_name

# ===================Sessions===================
sessions = {
    'fendabot1': {
        'name': 'sessions/fendabot1',
        'api_id': 26241828,
        'api_hash': '5a200bcdb33eadf1de021a70c227b658',
    },
    'fdboot2': {
        'name': 'sessions/fdboot2',
        'api_id': 26859493,
        'api_hash': '37d1d3b4f2203a5f4e3978b1d1b19626',
    }
}


def get_client(name):
    session = sessions[name]
    return TelegramClient(session['name'], session['api_id'], session['api_hash'])


# ===================Functions===================
async def get_all_contacts(client):
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


async def get_all_dialogs(client):
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


async def check_group_type1(client, link):
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


async def check_group_type(client, invite_link):
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


async def join_group(client, channel):
    """
    :param client:
    :param channel: link,username,entity
    :return success: bool
    """
    try:
        updates = await client(JoinChannelRequest(channel))
        return len(updates.chats) > 0
    except Exception as e:
        print(f"操作失败：{e}")


async def join_private_group(client, group_username):
    try:
        updates = await client(ImportChatInviteRequest(group_username))
        print(updates.stringify())
    except Exception as e:
        print(f"操作失败：{e}")


async def leave_group(client, channel):
    """
    :param client:
    :param channel: link,username,entity
    :return success: bool
    """
    try:
        updates = await client(LeaveChannelRequest(channel))
        return len(updates.chats) > 0
    except Exception as e:
        print(f"操作失败：{e}")


async def get_group_or_channel_users(client, entity):
    """
    :param client:
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


async def add_user_to_contacts(client, user_id, user_firstname, user_lastname, user_phone):
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


async def join_user_to_regular_group(client, chat, user):
    # real_id, peer_type = utils.resolve_id(chat_id)
    group = await client.get_entity(chat)
    print(group)
    updates = await client(AddChatUserRequest(
        group.id,
        user,
        fwd_limit=10  # Allow the user to see the 10 last messages
    ))
    print(updates.stringify())


async def join_user_to_channel_or_megagroup(client, channel, user):
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


async def create_private_megagroup_or_channel(client, title, about='', channel=False):
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


async def edit_group_to_public(client, input_channel, username):
    try:
        success = await client(UpdateUsernameRequest(
            channel=input_channel,
            username=username
        ))
        return success
    except Exception as e:
        print(f"操作失败：{e}")


async def create_public_megagroup_or_channel(client, username, title, about='', channel=False, delete_on_fail=True):
    channel = await create_private_megagroup_or_channel(client, title, about, channel)
    if channel:
        success = False
        is_valid = await check_username_valid(client, channel, username)
        if is_valid:
            success = await edit_group_to_public(client, channel, username)
        if delete_on_fail and (not success):
            await delete_channel(client, channel)


async def check_username_valid(client, channel, username):
    """
    :param client:
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


async def delete_channel(client, channel):
    """
    :param client:
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


# ===================Functions===================
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


async def test(client):
    # await get_all_contacts(client)
    dialogs = await get_all_dialogs(client)
    # await join_user_to_channel_or_megagroup(client, 'https://t.me/fendatestchannel1', 'cola_pls')
    # await add_user_to_contacts(client, 6472628002, 'INK', '阿英🦋', '')
    pass


if __name__ == '__main__':
    client = get_client('fendabot1')
    with client:
        result = client.loop.run_until_complete(test(client))
