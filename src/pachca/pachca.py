import time
import logging
from typing import Optional, Union, Literal
from itertools import chain
from http import HTTPStatus
from json import JSONDecodeError

from requests import Request, Session, Response

from pachca.file import File
from pachca.exceptions import (
    PachcaException,
    PachcaChatAlreadyExists,
)

logger = logging.getLogger()


class Pachca:
    """
    Pachca API client.
    Official reference is https://crm.pachca.com/dev/getting-started/overview/
    """
    API_URL = 'https://api.pachca.com/api/shared/v1'

    PROFILE = 'profile'
    CHATS = 'chats'
    MEMBERS = 'members'
    MESSAGES = 'messages'
    THREADS = 'threads'
    UPLOAD = 'uploads'

    def __init__(
        self,
        access_token: str,
        timeout_api: float = 0.2,
        timeout_rsp: int = 30,
    ) -> None:
        """
        Creates Python client to work with Pachca API.

        Args:
            access_token (str): Access token.
            timeout_api (float): Timeout between the requests [sec].
            timeout_rsp (float): Timeout to wait for response [sec].
        """

        self.__token = access_token
        self.__timeout_api = timeout_api
        self.__timeout_rsp = timeout_rsp
        self.__proxies = None
        self.__session = None        
        self.headers = {'Authorization': f'Bearer {self.__token }'}

    def __enter__(self):
        self.__session = Session()        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__session.close() 

    def call_api(
        self,
        path: str,
        method: Literal['get', 'post', 'put', 'delete'],
        payload: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    )  -> Union[dict, str]:
        """
        Call API with specified method and payload.

        Args:
            path (str): Pachca API URL (relative or absolute)
            method (str): The HTTP method (get, post, put, delete)
            payload (dict, optional): Request payload parameters
            data (dict, optional): Optional data attribute for file uploads.
            files (dict, optional): Optional files.

        Returns:
            (dict or list): List of objects or single dict
        """
        if not path.startswith('http'):
            url = f'{self.API_URL}/{path}'
        else:
            url = path

        request = Request(method=method, url=url, headers=self.headers, data=data)
        if payload:
            if method == 'get':
                request.params = payload
            else:
                request.json = payload
        if files:
            request.files = files
        prepared = request.prepare()
        response = self.__session.send(prepared, proxies=self.__proxies, timeout=self.__timeout_rsp)
        time.sleep(self.__timeout_api)
        self.__check_response(response)        
        return self.__handle_response(response)
    
    def __check_response(self, response: Response) -> None:
        """
        Checks for errors according to https://crm.pachca.com/dev/getting-started/errors/
        """
        if response.status_code in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.NO_CONTENT):  
            return        
        try:        
            error_message = {
                int(HTTPStatus.NOT_FOUND.value): f'Resource {response.url} not found.',
                int(HTTPStatus.UNAUTHORIZED.value): f'Token {self.__token[:5]}*** is not valid.',
                int(HTTPStatus.FORBIDDEN.value): f'Token {self.__token[:5]}*** is not valid for this request.',
                int(HTTPStatus.BAD_REQUEST.value): f'Error in request params. Check for docs.',
                int(HTTPStatus.TOO_MANY_REQUESTS.value): f'Too many requests. '
                                                         f'Increase API timeout ({self.__timeout_api} [sec]).'
            }[response.status_code]
            body = response.json()
            error_text = body['errors']
        except JSONDecodeError:
            error_message = f'Json could not be decode for {response.status_code}'
            error_text = response.text
        except KeyError:
            error_message = f'Some unhandled error occurred {response.status_code}'
            error_text = response.text

        raise Exception(f'Error: {error_message}: {error_text}')

    @staticmethod
    def __handle_response(response) -> Union[dict, str]:
        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    def get_profile(self) -> dict:
        """
        Get self (token owner) profile.

        Returns:
            dict: profile info.
        """
        response = self.call_api(Pachca.PROFILE, 'get')
        return response['data']

    def get_user_id(self) -> int:
        """
        Get self (token owner) user ID.

        Returns:
            int: User ID.
        """
        profile = self.get_profile()
        return profile['id']

    def get_chats(
        self,
        sort_field: Literal['id', 'last_message_at'] = 'id',
        sort_direction: Literal['asc', 'desc'] = 'desc',
        availability: Literal['is_member', 'public'] = 'is_member',
        last_message_at_after: Optional[str] = None,
        last_message_at_before: Optional[str] = None,
        personal: Optional[bool] = None,
        limit: int = 50
    ) -> list[dict]:
        """
        Gets available chats according to https://crm.pachca.com/dev/chats/list/

        Args:
            sort_field (str): Sort field: 'id' or 'last_message_at'.
            sort_direction (str): Sort direction: 'asc' or 'desc'.
            availability (str): Chat availability: 'public' or 'is_member' (access token user).
            last_message_at_after (str): Chats with last messages written after 'YYYY-MM-DDThh:mm:ss.sssZ'.
            last_message_at_before: Chats with last messages written before 'YYYY-MM-DDThh:mm:ss.sssZ'.
            personal (bool): Get personal chats.
            limit (50): Number of items per request (max 50).

        Return:
            list[dict]: List of chats.
        """
        
        chats = []

        payload = {
            f'sort[{sort_field}]': sort_direction,
            'availability': availability,
            'last_message_at_after': last_message_at_after,
            'personal': personal,
            'limit': limit,
            'cursor': None
        }
        if personal is not None:
            payload['personal'] = personal
        if last_message_at_after:
            payload['last_message_at_after'] = last_message_at_after
        if last_message_at_before:
            payload['last_message_at_before'] = last_message_at_before

        while True:
            response = self.call_api(Pachca.CHATS, 'get', payload)

            meta: dict = response['meta']
            data = response['data']            
            payload['cursor'] = meta['paginate']['next_page']
            chats.extend(data)            

            if len(data) < limit:
                break

        return chats

    def find_chats(self, name: str) -> list[dict]:
        """
        Return chats with specified name, if exists.

        Args:
            name (str): Name to search.

        Returns:
            list[dict]: List of chats.
        """
        public_chats: list[dict] = self.get_chats(availability='public')
        member_chats: list[dict] = self.get_chats(availability='is_member')
        chats = []
        chat_ids = set()
        for chat in chain(public_chats, member_chats):
            if chat['id'] not in chat_ids and chat['name'] == name:
                chat_ids.add(chat['id'])
                chats.append(chat)
        return chats

    def get_chat(self, chat_id: int) -> dict:
        """
        Get chat by ID.

        Args:
            chat_id (int): Unique integer chat ID.

        Returns:
            dict: Chat parameters.
        """
        path = f'{Pachca.CHATS}/{chat_id}'
        response = self.call_api(path, 'get')
        return response['data']
    
    def create_chat(
        self,
        name: str,
        member_ids: Optional[list[int]] = None,
        group_tag_ids: Optional[list[int]] = None,
        channel: bool = False,
        public: bool = False,
        ignore_existing: bool = True,
    ) -> dict:
        """
        Create new chat.

        Args:
            name (str): Name of the new chat.
            member_ids (list[int]): Member IDs (aka user IDs) of new chat.
            group_tag_ids: (list[int]): (User) Group Tag IDs of new chat.
            channel (bool): Simple chat (`False`) or read-only channel (only editors can write messages)
            public (bool): Is chat should be public or private.
            ignore_existing (bool): `False` will raise the PachcaChatAlreadyExists exception if chat with `name` already exists.

        Returns:
            dict: Parameters of created chat.
        """

        if not ignore_existing:
            chats = self.find_chats(name=name)
            n_chats = len(chats)
            if n_chats > 0:
                raise PachcaChatAlreadyExists(f'{n_chats} chats with name "{name}" has been found.')

        payload = {
            'chat': {
                'name': name,
                'member_ids': member_ids,
                'group_tag_ids': group_tag_ids,
                'channel': channel,
                'public': public
            }
        }

        response = self.call_api(Pachca.CHATS, 'post', payload)
        return response['data']

    def update_chat(
        self,
        chat_id: int,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        ignore_existing: bool = True,
    ) -> dict:
        """
        Update chat `name` or `public` flag (access type).

        Args:
            chat_id (int): Chat unique ID.
            name (str, optional): New name of the chat.
            public (bool, optional): New access type: public or private.
            ignore_existing (bool): `False` will raise the PachcaChatAlreadyExists exception if chat with `name` already exists.

        Returns:
            dict: Parameters of created chat.
        """
        if all((name is None, public is None)):
            raise PachcaException('Nothing to update. You must specify *name* or/and *public*.')

        if not ignore_existing:
            chats = self.find_chats(name=name)
            n_chats = len(chats)
            if n_chats > 0:
                raise PachcaChatAlreadyExists(f'{n_chats} chats with name "{name}" has been found.')

        payload = {
            'chat': {}
        }
        if name:
            payload['chat']['name'] = name
        if public is not None:
            payload['chat']['public'] = public

        path = f'{Pachca.CHATS}/{chat_id}'
        response = self.call_api(path, 'put', payload)
        return response['data']

    def archive_chat(self, chat_id: int) -> dict:
        """
        Archive chat.

        Args:
            chat_id (int): Chat ID.
        """
        path = f'{Pachca.CHATS}/{chat_id}/archive'
        response = self.call_api(path, 'put')
        return response

    def unarchive_chat(self, chat_id: int) -> dict:
        """
        Unarchive chat.

        Args:
            chat_id (int): Chat ID.
        """
        path = f'{Pachca.CHATS}/{chat_id}/unarchive'
        response = self.call_api(path, 'put')
        return response

    def add_member(
        self,
        chat_id: int,
        member_ids: list[int],
        silent: bool = False
    ) -> dict:
        """
        Add chat member.

        Args:
            chat_id (int): Add chat member(-s).
            member_ids (list[int]): List of member IDs.
            silent (bool): Without system message of new member(-s).
        """
        payload = {
            'member_ids': member_ids,
            'silent': silent,
        }
        path = f'{Pachca.CHATS}/{chat_id}/members'
        response = self.call_api(path, 'post', payload)
        return response

    def update_member(
        self,
        chat_id: int,
        member_id: int,
        role: Literal['member', 'admin', 'editor'],
    ) -> dict:
        """
        Update member parameters.

        Args:
            chat_id (int): Chat ID.
            member_id (int): Member ID.
            role (str): New role: `member`, `admin`, `editor` (only for channels).
        """
        payload = {
            'role': role,
        }
        path = f'{Pachca.CHATS}/{chat_id}/{Pachca.MEMBERS}/{member_id}'
        response = self.call_api(path, 'put', payload)
        return response

    def remove_member(
        self,
        chat_id: int,
        member_id: int
    ) -> dict:
        """
        Remove chat member.

        Args:
            chat_id (int): Chat ID.
            member_id (int): Member ID to remove.
        """
        path = f'{Pachca.CHATS}/{chat_id}/{Pachca.MEMBERS}/{member_id}'
        response = self.call_api(path, 'delete')
        return response

    def get_members(
        self,
        chat_id: int,
        role: Literal['all', 'owner', 'admin', 'editor'] = 'all',
        limit: int = 50
    ) -> list[dict]:
        """
        Get chat members.

        Args:
            chat_id (int): Chat ID.
            role (str): Member role in chat: 'all' (default), 'owner', 'admin', 'editor' (for channels).
            limit (int): Members per page.

        Returns:
            list[dict]: List of members.
        """
        members = []

        payload = {
            'role': role,
            'limit': limit,
            'cursor': None,
        }

        path = f'{Pachca.CHATS}/{chat_id}/members'
        while True:
            response = self.call_api(path, 'get', payload)

            meta: dict = response['meta']
            data = response['data']
            payload['cursor'] = meta['paginate']['next_page']
            members.extend(data)

            if len(data) < limit:
                break

        return members

    def get_member(
        self,
        chat_id: int,
        member_id: int
    ) -> Optional[dict]:
        """
        Get member info from chat.

        Args:
            chat_id (int): Chat ID.
            member_id (int): Member ID.

        Returns:
            dict or None: Member info or None if no member found.
        """
        members = self.get_members(chat_id=chat_id, role='all')
        for member in members:
            if member['id'] == member_id:
                return member
        return None

    def create_message(
        self,
        entity_id: int,
        content: str,
        entity_type: Literal['discussion', 'user', 'thread'] = 'discussion',
        parent_message_id: Optional[int] = None,
        display_avatar_url: Optional[str] = None,
        display_name: Optional[str] = None,
        skip_invite_mentions: bool = False,
        link_preview: bool = False,
        files: Optional[list[File]] = None
    ) -> dict:
        """
        Create message (for discussion, thread and user chat types).

        Args:
            entity_id (int): ID of target entity (chat ID, thread ID, user ID).
            content (str): Message content.
            entity_type (str): Type of target entity: `discussion`, `user`, `thread`.
            parent_message_id (int, optional): Reply to message ID.
            display_avatar_url (str, optional): URL of avatar (only for bot).
            display_name (str, optional): Name of message author (only for bot).
            skip_invite_mentions (bool): `True` will invite mentioned users to thread (only for threads).
            link_preview (bool): Display first link preview or not.
            files (list[File]): Optional list of File objects.

        Returns:
            dict: Created message dict.
        """
        message = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'content': content,
        }
        if parent_message_id is not None:
            message['parent_message_id'] = parent_message_id
        if display_name:
            message['display_name'] = display_name
        if display_avatar_url:
            message['display_avatar_url'] = display_avatar_url
        if entity_type == 'thread':
            message['skip_invite_mentions'] = skip_invite_mentions

        if files is not None:
            message_files = []
            for file in files:
                self.upload_file(file)
                message_files.append(file.as_dict())
            message['files'] = message_files

        payload = {
            'message': message,
            'link_preview': link_preview,
        }
        response = self.call_api(Pachca.MESSAGES, 'post', payload)
        return response['data']

    def update_message(
        self,
        message_id: int,
        content: str
    ) -> dict:
        """
        Update message.

        Args:
            message_id (int): Message ID.
            content (str): Content to update.

        Returns:
            dict: Updated message dict.
        """
        message = {
            'content': content,
        }
        payload = {
            'message': message
        }
        path = f'{Pachca.MESSAGES}/{message_id}'
        response = self.call_api(path, 'put', payload)
        return response['data']

    def get_messages(
            self,
            chat_id: int,
            sort_field: Literal['id'] = 'id',
            sort_direction: Literal['asc', 'desc'] = 'desc',
    ) -> list[dict]:
        """
        Gets available messages according to https://crm.pachca.com/dev/messages/list/

        Args:
            chat_id (int): Chat ID.
            sort_field (str): Sort field: 'id' or 'last_message_at'.
            sort_direction (str): Sort direction: 'asc' or 'desc'.

        Return:
            list[dict]: List of messages.
        """
        messages = []
        limit = 50
        page = 1

        payload = {
            'chat_id': chat_id,
            f'sort[{sort_field}]': sort_direction,
            'per': limit
        }

        while True:
            payload['page'] = page
            response = self.call_api(Pachca.MESSAGES, 'get', payload)

            data = response['data']
            messages.extend(data)

            if len(data) < limit:
                break

            page += 1

        return messages

    def get_message(self, message_id: int) -> dict:
        """Get message info.

        Args:
            message_id (int): message ID.

        Returns:
            dict: Message dict.
        """
        path = f'{Pachca.MESSAGES}/{message_id}'
        response = self.call_api(path, 'get')
        return response['data']

    def pin_message(self, message_id: int) -> dict:
        """Pin message.

        Args:
            message_id (int): message ID.

        Returns:
            dict: Message dict.
        """
        path = f'{Pachca.MESSAGES}/{message_id}/pin'
        response = self.call_api(path, 'post')
        return response

    def unpin_message(self, message_id: int) -> dict:
        """Unpin message.

        Args:
            message_id (int): message ID.

        Returns:
            dict: Message dict.
        """
        path = f'{Pachca.MESSAGES}/{message_id}/pin'
        response = self.call_api(path, 'delete')
        return response

    def delete_message(self, message_id: int) -> dict:
        """
        Delete message.

        Args:
            message_id (int): message ID.

        Returns:
            Nothing on success.
        """
        path = f'{Pachca.MESSAGES}/{message_id}'
        response = self.call_api(path, 'delete')
        return response

    def create_thread(self, message_id: int) -> dict:
        """
        Create new thread for message.

        Args:
            message_id (int): Message ID, where we want to create thread.

        Returns:
            dict: Thread parameters.
        """
        path = f'{Pachca.MESSAGES}/{message_id}/thread'
        response = self.call_api(path, 'post')
        return response['data']

    def get_thread(self, thread_id: int) -> dict:
        """
        Get thread information.

        Args:
            thread_id (int): Thread ID.

        Returns:
            dict: Thread parameters.
        """
        path = f'{Pachca.THREADS}/{thread_id}'
        response = self.call_api(path, 'get')
        return response['data']

    def upload_file(self, file: File) -> dict:
        """
        Upload file.

        Args:
            file (File): Instance of File class.

        Returns:
            File: File object (modified after upload).
        """
        meta = self.call_api(Pachca.UPLOAD, 'post')
        file.update_meta(meta)

        with open(file.path, 'rb') as file_obj:
            files = {'file': file_obj}
            response = self.call_api(
                path=file.url,
                method='post',
                data=file.meta,
                files=files,
            )

        return response