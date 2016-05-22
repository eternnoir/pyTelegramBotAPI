# -*- coding: utf-8 -*-
import pytest
import mock

from telebot import types
from telebot import apihelper


class TestTelegramApiInterface:

    def test_make_request(self):
        api = self.create_mocked_instance()
        api.request_executor = mock.MagicMock()
        api.request_executor.return_value = 'return value'

        response = api.make_request(
            'methodName',
            params={'param': 'value'},
            files={'file': 'value'},
            method='method',
            response_type='response_type'
        )
        api.request_executor.assert_called_with(
            'token=TOKEN&method=methodName',
            method='method',
            params={'param': 'value'},
            files={'file': 'value'},
            response_type='response_type'
        )
        assert response == 'return value'

    def test_make_request_exception(self):
        api = self.create_mocked_instance()
        api.request_executor = mock.MagicMock()
        api.request_executor.side_effect = Exception('abc')

        with pytest.raises(apihelper.ApiException) as e:
            api.make_request('methodName')
        assert e.value.function_name == 'methodName'

    def test_get_updates(self):
        api = self.create_mocked_instance()
        
        kwargs = {'offset': 100, 'limit': 200, 'timeout': 300}
        api.get_updates(**kwargs)
        api.make_json_request.assert_called_with('getUpdates', params=kwargs)

    def test_get_me(self):
        api = self.create_mocked_instance()
        
        api.get_me()
        api.make_json_request.assert_called_with('getMe', return_type=types.User)

    def test_get_file(self):
        api = self.create_mocked_instance()
        
        api.get_file(100)
        api.make_json_request.assert_called_with('getFile', params={'file_id': 100}, return_type=types.File)

    def test_download_file(self):
        api = self.create_mocked_instance()
        
        api.make_request = mock.MagicMock()
        api.download_file('fp')
        api.make_request.assert_called_with('token=TOKEN&file_path=fp', response_type='binary')

    def test_send_message(self):
        api = self.create_mocked_instance()
        
        kwargs = {
            'reply_markup': 1,
        }
        api.send_message(1, 'text', **kwargs)
        api.make_json_request.assert_called_with(
            'sendMessage', params={'chat_id': '1', 'text': 'text', 'reply_markup': 1}, return_type=types.Message
        )

    def test_set_webhook(self):
        api = self.create_mocked_instance()
        
        api.set_webhook(url='abc123', certificate='certificate')
        api.make_json_request.assert_called_with(
            'setWebhook', params={'url': 'abc123'}, files={'certificate': 'certificate'}
        )

    def test_get_user_profile_photos(self):
        api = self.create_mocked_instance()
        
        api.get_user_profile_photos(1, offset=2, limit=3)
        api.make_json_request.assert_called_with(
            'getUserProfilePhotos', params={'user_id': 1, 'offset': 2, 'limit': 3}, return_type=types.UserProfilePhotos
        )

    def test_forward_message(self):
        api = self.create_mocked_instance()
        
        api.forward_message(1, 2, 3, disable_chat_notification=True)
        api.make_json_request.assert_called_with(
            'forwardMessage',
            params={'chat_id': 1, 'from_chat_id': 2, 'message_id': 3, 'disable_chat_notification': True},
            return_type=types.Message
        )

    def test_send_location(self):
        api = self.create_mocked_instance()
        
        api.send_location(1, 2, 3)
        api.make_json_request.assert_called_with(
            'sendLocation',
            params={'chat_id': 1, 'latitude': 2, 'longitude': 3},
            return_type=types.Message
        )

    def test_send_venue(self):
        api = self.create_mocked_instance()
        
        api.send_venue(1, 2, 3, 'title', 'address', foursquare_id=3)
        api.make_json_request.assert_called_with(
            'sendVenue',
            params={'chat_id': 1, 'latitude': 2, 'longitude': 3,
                    'title': 'title', 'address': 'address', 'foursquare_id': 3
                    },
            return_type=types.Message
        )

    def test_send_contact(self):
        api = self.create_mocked_instance()
        
        api.send_contact(1, '123456', 'first_name')
        api.make_json_request.assert_called_with(
            'sendContact',
            params={'chat_id': 1, 'phone_number': '123456', 'first_name': 'first_name'},
            return_type=types.Message
        )

    def test_send_chat_action(self):
        api = self.create_mocked_instance()
        
        api.send_chat_action(1, 2)
        api.make_json_request.assert_called_with(
            'sendChatAction',
            params={'chat_id': 1, 'action': 2},
        )

    def test_send_data_string(self):
        api = self.create_mocked_instance()
        
        api.send_data('photo', 1, 'data', optional=True)
        api.make_json_request.assert_called_with(
            'sendPhoto',
            params={'chat_id': 1, 'photo': 'data', 'optional': True},
            files=None,
            return_type=types.Message
        )

    def test_send_data_file(self):
        f = True  # should not be a string
        api = self.create_mocked_instance()
        
        api.send_data('audio', 1, f, optional=True)
        api.make_json_request.assert_called_with(
            'sendAudio',
            params={'chat_id': 1, 'optional': True},
            files={'audio': f},
            return_type=types.Message
        )

    def test_kick_chat_member(self):
        api = self.create_mocked_instance()
        
        api.kick_chat_member(1, 2)
        api.make_json_request.assert_called_with('kickChatMember', params={'chat_id': 1, 'user_id': 2})

    def test_leave_chat(self):
        api = self.create_mocked_instance()
        api.leave_chat(1)
        api.make_json_request.assert_called_with('leaveChat', params={'chat_id': 1})
        

    def test_unban_chat_member(self):
        api = self.create_mocked_instance()
        
        api.unban_chat_member(1, 2)
        api.make_json_request.assert_called_with('unbanChatMember', params={'chat_id': 1, 'user_id': 2})

    def test_get_chat(self):
        api = self.create_mocked_instance()

        api.get_chat(1)
        api.make_json_request.assert_called_with('getChat', params={'chat_id': 1})

    def test_get_chat_administrators(self):
        api = self.create_mocked_instance()

        api.get_chat_administrators(1)
        api.make_json_request.assert_called_with('getChatAdministrators', params={'chat_id': 1})

    def test_get_chat_members_count(self):
        api = self.create_mocked_instance()

        api.get_chat_members_count(1)
        api.make_json_request.assert_called_with('getChatMembersCount', params={'chat_id': 1})

    def test_get_chat_member(self):
        api = self.create_mocked_instance()

        api.get_chat_member(1, 2)
        api.make_json_request.assert_called_with(
            'getChatMember',
            params={'chat_id': 1, 'user_id': 2},
            return_type=types.ChatMember
        )

    def test_edit_message_text(self):
        api = self.create_mocked_instance()
        
        api.make_json_request.return_value = True
        api.edit_message_text('new_text', optional=True)
        api.make_json_request.assert_called_with('editMessageText', params={'text': 'new_text', 'optional': True})

    def test_answer_callback_query(self):
        api = self.create_mocked_instance()
        
        api.answer_callback_query(1, optional=True)
        api.make_json_request.assert_called_with('answerCallbackQuery', params={'callback_query_id': 1, 'optional': True})

    def test_answer_inline_query(self):
        api = self.create_mocked_instance()
        
        api.answer_inline_query(1, ['a', 'b'], optional=True)
        api.make_json_request.assert_called_with(
            'answerInlineQuery',
            params={'inline_query_id': 1, 'results': '[a,b]', 'optional': True}
        )

    def create_mocked_instance(self):
        instance = apihelper.TelegramApiInterface('TOKEN', None,
                                                  api_url='token={0}&method={1}', file_url='token={0}&file_path={1}')
        instance.make_json_request = mock.MagicMock()
        return instance


