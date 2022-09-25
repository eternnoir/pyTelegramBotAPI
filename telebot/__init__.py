import asyncio
import functools
import json
import logging
import re
from asyncio.exceptions import TimeoutError
from datetime import datetime
from inspect import signature
from typing import Any, Callable, Coroutine, List, Optional, TypeVar, Union, cast

from telebot import api, callback_data, filters, types, util
from telebot.types import constants
from telebot.types import service as service_types

logger = logging.getLogger("telebot")


_UpdateContentT = TypeVar("_UpdateContentT", bound=service_types.UpdateContent)


class AsyncTeleBot:
    """
    This is the main asynchronous class for Bot.

    It allows you to add handlers for different kind of updates.

    Usage:

    .. code-block:: python

        from telebot import AsyncTeleBot
        bot = AsyncTeleBot('token') # get token from @BotFather

    See more examples in examples/ directory:
    https://github.com/eternnoir/pyTelegramBotAPI/tree/master/examples
    """

    def __init__(
        self,
        token: str,
        parse_mode: Optional[str] = None,
        offset: Optional[int] = None,
        custom_filters: Optional[list[filters.AnyCustomFilter]] = None,
        force_allowed_updates: Optional[list[constants.UpdateType]] = None,
    ):
        self.token = token
        self.offset = offset
        self.parse_mode = parse_mode

        self.update_listeners: list[Callable[[types.Update], service_types.NoneCoro]] = []

        self.message_handlers: list[service_types.Handler] = []
        self.edited_message_handlers: list[service_types.Handler] = []
        self.channel_post_handlers: list[service_types.Handler] = []
        self.edited_channel_post_handlers: list[service_types.Handler] = []
        self.inline_query_handlers: list[service_types.Handler] = []
        self.chosen_inline_handlers: list[service_types.Handler] = []
        self.callback_query_handlers: list[service_types.Handler] = []
        self.shipping_query_handlers: list[service_types.Handler] = []
        self.pre_checkout_query_handlers: list[service_types.Handler] = []
        self.poll_handlers: list[service_types.Handler] = []
        self.poll_answer_handlers: list[service_types.Handler] = []
        self.my_chat_member_handlers: list[service_types.Handler] = []
        self.chat_member_handlers: list[service_types.Handler] = []
        self.chat_join_request_handlers: list[service_types.Handler] = []

        DEFAULT_CUSTOM_FILTERS: list[filters.AnyCustomFilter] = [
            filters.TextMatchFilter(),
            filters.ChatFilter(),
            filters.IsForwardedFilter(),
            filters.IsReplyFilter(),
        ]

        if custom_filters is None:
            custom_filters = []

        self.custom_filters = {cf.key: cf for cf in DEFAULT_CUSTOM_FILTERS + custom_filters}

        # updated automatically from added handlers
        self.allowed_updates: set[constants.UpdateType] = set(force_allowed_updates) if force_allowed_updates else set()

    async def close_session(self):
        """
        Closes existing session of aiohttp.
        Use this function if you stop polling.
        """
        await api.session_manager.close_session()

    # polling-related methods

    async def get_updates(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        timeout: Optional[int] = None,
        request_timeout: Optional[int] = None,
    ) -> list[types.Update]:
        json_updates = await api.get_updates(
            self.token,
            offset,
            limit,
            timeout,
            [ut.value for ut in self.allowed_updates],
            request_timeout,
        )
        maybe_updates = [types.Update.de_json(ju) for ju in json_updates]
        return [u for u in maybe_updates if u is not None]

    async def infinity_polling(
        self,
        interval: float = 1,
        timeout: int = 30,
        skip_pending: bool = False,
        request_timeout: int = 60,
    ):
        interval = max(interval, 0.3)
        try:
            logger.info("Running polling")
            if skip_pending:
                await self.skip_updates()
            while True:
                try:
                    updates = await self.get_updates(
                        offset=self.offset,
                        timeout=timeout,
                        request_timeout=request_timeout,
                    )
                    if updates:
                        self.offset = updates[-1].update_id + 1
                        asyncio.create_task(self.process_new_updates(updates))
                except TimeoutError:
                    logger.debug("Long polling timed out, sending new request")
                except Exception:
                    logger.exception("Unexpected exception while processing updates")
                    logger.info("Resuming polling")
                finally:
                    await asyncio.sleep(interval)

        finally:
            await self.close_session()
            logger.info("Stopping polling")

    # update handling

    async def process_new_updates(self, updates: list[types.Update]):
        upd_count = len(updates)
        if upd_count == 0:
            return

        try:
            update_dumps = [json.dumps(u._json_dict, ensure_ascii=False, sort_keys=False, indent=2) for u in updates]
            logger.debug(f"{upd_count} update(s) received:\n" + "\n\n".join(update_dumps) + "\n")
        except Exception:
            logger.exception(f"{upd_count} update(s) received, but error occured trying to dump them")

        coroutines: list[Coroutine[None, None, None]] = []
        for update in updates:
            for listener in self.update_listeners:
                asyncio.create_task(listener(update))

            if update.message:
                coroutines.append(self._process_update(self.message_handlers, update.message))
            if update.edited_message:
                coroutines.append(self._process_update(self.edited_message_handlers, update.edited_message))
            if update.channel_post:
                coroutines.append(self._process_update(self.channel_post_handlers, update.channel_post))
            if update.edited_channel_post:
                coroutines.append(self._process_update(self.edited_channel_post_handlers, update.edited_channel_post))
            if update.inline_query:
                coroutines.append(self._process_update(self.inline_query_handlers, update.inline_query))
            if update.chosen_inline_result:
                coroutines.append(self._process_update(self.chosen_inline_handlers, update.chosen_inline_result))
            if update.callback_query:
                coroutines.append(self._process_update(self.callback_query_handlers, update.callback_query))
            if update.shipping_query:
                coroutines.append(self._process_update(self.shipping_query_handlers, update.shipping_query))
            if update.pre_checkout_query:
                coroutines.append(self._process_update(self.pre_checkout_query_handlers, update.pre_checkout_query))
            if update.poll:
                coroutines.append(self._process_update(self.poll_handlers, update.poll))
            if update.poll_answer:
                coroutines.append(self._process_update(self.poll_answer_handlers, update.poll_answer))
            if update.my_chat_member:
                coroutines.append(self._process_update(self.my_chat_member_handlers, update.my_chat_member))
            if update.chat_member:
                coroutines.append(self._process_update(self.chat_member_handlers, update.chat_member))
            if update.chat_join_request:
                coroutines.append(self._process_update(self.chat_join_request_handlers, update.chat_join_request))

        await asyncio.gather(*coroutines, return_exceptions=True)

    async def _process_update(self, handlers: list[service_types.Handler], update_content: service_types.UpdateContent):
        try:
            update_content_log = f"{update_content.__class__.__name__} {update_content}"
        except Exception:
            update_content_log = f"{update_content.__class__.__name__}"

        for handler in handlers:
            handler_name = handler.get("name", "<anonymous>")

            try:
                is_match = await self._test_handler(handler, update_content)
            except Exception:
                logger.exception(f"Error testing handler {handler_name!r} for {update_content_log}")
                is_match = False

            if is_match:
                logger.debug(f"Using handler {handler_name!r} to process {update_content_log}")
                try:
                    return await invoke_handler(handler["function"], update_content, self)
                except Exception:
                    logger.exception(f"Error processing update with handler '{handler_name}': {update_content}")
                    return
        else:
            logger.debug(f"No matching handler found for {update_content_log}, ignoring")

    async def _test_handler(self, handler: service_types.Handler, content: service_types.UpdateContent) -> bool:
        for filter_key, filter_value in handler["filters"].items():
            if filter_value is None:
                continue
            if not await self._test_filter(filter_key, filter_value, content):
                return False
        return True

    def update_listener(self, decorated: Callable[[types.Update], service_types.NoneCoro]):
        self.update_listeners.append(decorated)

    def add_custom_filter(self, custom_filter: filters.AnyCustomFilter):
        self.custom_filters[custom_filter.key] = custom_filter

    async def _test_filter(
        self, filter_key: str, filter_value: service_types.FilterValue, update_content: service_types.UpdateContent
    ) -> bool:
        def update_content_as_message() -> types.Message:
            if not isinstance(update_content, types.Message):
                raise TypeError(f"{filter_key} filter can be used only with message updates")
            return update_content

        if filter_key == "content_types":
            ct = constants.content_type_from_str(update_content_as_message().content_type)
            return ct in util.validated_list_content_type(filter_value, name="content types filter")
        elif filter_key == "regexp":
            message = update_content_as_message()
            return message.content_type == "text" and bool(
                re.search(util.validated_str(filter_value), message.text or message.caption or "", re.IGNORECASE)
            )
        elif filter_key == "commands":
            message = update_content_as_message()
            command = util.extract_command(message.text_content)
            return (
                message.content_type == "text"
                and command is not None
                and command in util.validated_list_str(filter_value, name="commands filter")
            )
        elif filter_key == "chat_types":
            return constants.ChatType(update_content_as_message().chat.type) in util.validated_list_chat_type(
                filter_value, name="chat types filter"
            )
        elif filter_key == "func":
            if not callable(filter_value):
                raise TypeError("func filter must be callable")
            filter_value = cast(service_types.FilterFunc, filter_value)
            filter_func_return = filter_value(update_content)
            if isinstance(filter_func_return, bool):
                return filter_func_return
            else:
                return await filter_func_return
        elif filter_key == "callback_data":
            try:
                filter_value = cast(callback_data.CallbackData, filter_value)
                update_content = cast(types.CallbackQuery, update_content)
                filter_value.parse(update_content.data)
                return True
            except ValueError:
                return False
        else:
            return await self._test_custom_filters(filter_key, filter_value, update_content)

    async def _test_custom_filters(
        self, filter_key: str, filter_value: service_types.FilterValue, update_content: service_types.UpdateContent
    ):
        try:
            custom_filter = self.custom_filters.get(filter_key)
            if custom_filter is None:
                logger.error(
                    f"Invalid filter key: {filter_key!r}. Did you forgot to add your custom filter to the bot?"
                )
                return False
            elif isinstance(custom_filter, filters.SimpleCustomFilter):
                return filter_value == await custom_filter.check(update_content)
            elif isinstance(custom_filter, filters.AdvancedCustomFilter):
                return await custom_filter.check(update_content, filter_value)
            else:
                logger.error(
                    "Invalid custom filter type, expected either SimpleCustomFilter "
                    + f"or AdvancedCustomFilter, got {custom_filter!r}."
                )
                return False
        except Exception as e:
            logger.exception(f"Unexpected error testing custom filters")
            return False

    # handlers building decorators and methods

    def message_handler(
        self,
        commands: Optional[list[str]] = None,
        regexp: str = None,
        func: Optional[service_types.FilterFunc[types.Message]] = None,
        content_types: Optional[list[constants.ContentType]] = None,
        chat_types: Optional[list[constants.ChatType]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        """
        Message handler decorator.
        This decorator can be used to decorate functions that must handle certain types of messages.
        All message handlers are tested in the order they were added.

        Example:

        .. code-block:: python

            bot = TeleBot('TOKEN')

            # Handles all messages which text matches regexp.
            @bot.message_handler(regexp='someregexp')
            async def command_help(message):
                bot.send_message(message.chat.id, 'Did someone call for help?')

            # Handles messages in private chat
            @bot.message_handler(chat_types=['private']) # You can add more chat types
            async def command_help(message):
                bot.send_message(message.chat.id, 'Private chat detected, sir!')

            # Handle all sent documents of type 'text/plain'.
            @bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain',
                content_types=['document'])
            async def command_handle_document(message):
                bot.send_message(message.chat.id, 'Document received, sir!')

            # Handle all other messages.
            @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                'text', 'location', 'contact', 'sticker'])
            async def async default_command(message):
                bot.send_message(message.chat.id, "This is the async default command handler.")

        :param commands: Optional list of strings (commands to handle).
        :param regexp: Optional regular expression.
        :param func: Optional lambda function. The lambda receives the message to test as the first parameter.
            It must return True if the command should handle the message.
        :param content_types: Supported message content types. Must be a list. async defaults to ['text'].
        :param chat_types: list of chat types
        """

        if content_types is None:
            content_types = list(constants.MediaContentType)

        def decorator(decorated: service_types.HandlerFunction[types.Message]):
            self.allowed_updates.add(constants.UpdateType.message)
            self.message_handlers.append(
                service_types.Handler(
                    function=util.ensure_async(decorated),
                    filters={
                        "commands": commands,
                        "regexp": regexp,
                        "content_types": content_types,
                        "chat_types": chat_types,
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(self.message_handlers)
            return decorated

        return decorator

    def edited_message_handler(
        self,
        commands: Optional[list[str]] = None,
        regexp: str = None,
        func: Optional[service_types.FilterFunc[types.Message]] = None,
        content_types: Optional[list[constants.ContentType]] = None,
        chat_types: Optional[list[constants.ChatType]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        if content_types is None:
            content_types = list(constants.MediaContentType)

        def decorator(decorated: service_types.HandlerFunction[types.Message]):
            self.allowed_updates.add(constants.UpdateType.edited_message)
            self.edited_message_handlers.append(
                service_types.Handler(
                    function=util.ensure_async(decorated),
                    filters={
                        "commands": commands,
                        "regexp": regexp,
                        "content_types": content_types,
                        "chat_types": chat_types,
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(self.edited_message_handlers)
            return decorated

        return decorator

    def channel_post_handler(
        self,
        commands: Optional[list[str]] = None,
        regexp: str = None,
        func: Optional[service_types.FilterFunc[types.Message]] = None,
        content_types: Optional[list[str]] = None,
        chat_types: Optional[list[constants.ChatType]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        if content_types is None:
            content_types = list(constants.MediaContentType)

        def decorator(decorated: service_types.HandlerFunction[types.Message]):
            self.allowed_updates.add(constants.UpdateType.channel_post)
            self.channel_post_handlers.append(
                service_types.Handler(
                    function=util.ensure_async(decorated),
                    filters={
                        "commands": commands,
                        "regexp": regexp,
                        "content_types": content_types,
                        "chat_types": chat_types,
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(self.channel_post_handlers)
            return decorated

        return decorator

    def edited_channel_post_handler(
        self,
        commands: Optional[list[str]] = None,
        regexp: str = None,
        func: Optional[service_types.FilterFunc[types.Message]] = None,
        content_types: Optional[list[constants.ContentType]] = None,
        chat_types: Optional[list[constants.ChatType]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        if content_types is None:
            content_types = list(constants.MediaContentType)

        def decorator(decorated: service_types.HandlerFunction[types.Message]):
            self.allowed_updates.add(constants.UpdateType.edited_channel_post)
            self.edited_channel_post_handlers.append(
                service_types.Handler(
                    function=util.ensure_async(decorated),
                    filters={
                        "commands": commands,
                        "regexp": regexp,
                        "content_types": content_types,
                        "chat_types": chat_types,
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(self.edited_channel_post_handlers)
            return decorated

        return decorator

    def callback_query_handler(
        self,
        callback_data: callback_data.CallbackData,
        func: Optional[service_types.FilterFunc[types.CallbackQuery]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        auto_answer: bool = False,
        **kwargs,
    ):
        def decorator(decorated: service_types.HandlerFunction[types.CallbackQuery]):
            decorated = util.ensure_async(decorated)
            if auto_answer:

                @functools.wraps(decorated)
                async def handler_func(cq: types.CallbackQuery, *args):
                    try:
                        await invoke_handler(decorated, cq, self)
                    finally:
                        await self.answer_callback_query(cq.id)

            else:
                handler_func = decorated
            self.allowed_updates.add(constants.UpdateType.callback_query)
            self.callback_query_handlers.append(
                service_types.Handler(
                    function=cast(service_types.HandlerFunction[types.CallbackQuery], handler_func),
                    filters={
                        "callback_data": callback_data,
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(self.callback_query_handlers)
            return decorated

        return decorator

    def _simple_handler(
        self,
        handler_list: list[service_types.Handler],
        func: Optional[service_types.FilterFunc[_UpdateContentT]],
        priority: Optional[int],
        name: Optional[str],
        **kwargs,
    ):
        def decorator(decorated: service_types.HandlerFunction[_UpdateContentT]):
            handler_list.append(
                service_types.Handler(
                    function=util.ensure_async(decorated),
                    filters={
                        "func": func,
                        **kwargs,
                    },
                    name=name or util.qualified_name(decorated),
                    priority=priority,
                )
            )
            sort_by_priority(handler_list)
            return decorated

        return decorator

    def inline_query_handler(
        self,
        func: Optional[service_types.FilterFunc[types.InlineQuery]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.inline_query)
        return self._simple_handler(self.inline_query_handlers, func, priority=priority, name=name, **kwargs)

    def chosen_inline_result_handler(
        self,
        func: Optional[service_types.FilterFunc[types.ChosenInlineResult]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.chosen_inline_result)
        return self._simple_handler(self.chosen_inline_handlers, func, priority=priority, name=name, **kwargs)

    def shipping_query_handler(
        self,
        func: Optional[service_types.FilterFunc[types.ShippingQuery]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.shipping_query)
        return self._simple_handler(self.shipping_query_handlers, func, priority=priority, name=name, **kwargs)

    def pre_checkout_query_handler(
        self,
        func: Optional[service_types.FilterFunc[types.PreCheckoutQuery]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.pre_checkout_query)
        return self._simple_handler(self.pre_checkout_query_handlers, func, priority=priority, name=name, **kwargs)

    def poll_handler(
        self,
        func: Optional[service_types.FilterFunc[types.Poll]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.poll)
        return self._simple_handler(self.poll_handlers, func, priority=priority, name=name, **kwargs)

    def poll_answer_handler(
        self,
        func: Optional[service_types.FilterFunc[types.PollAnswer]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.poll_answer)
        return self._simple_handler(self.poll_answer_handlers, func, priority=priority, name=name, **kwargs)

    def my_chat_member_handler(
        self,
        func: Optional[service_types.FilterFunc[types.ChatMemberUpdated]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.my_chat_member)
        return self._simple_handler(self.my_chat_member_handlers, func, priority=priority, name=name, **kwargs)

    def chat_member_handler(
        self,
        func: Optional[service_types.FilterFunc[types.ChatMemberUpdated]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.chat_member)
        return self._simple_handler(self.chat_member_handlers, func, priority=priority, name=name, **kwargs)

    def chat_join_request_handler(
        self,
        func: Optional[service_types.FilterFunc[types.ChatJoinRequest]] = None,
        priority: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.allowed_updates.add(constants.UpdateType.chat_join_request)
        return self._simple_handler(self.chat_join_request_handlers, func, priority=priority, name=name, **kwargs)

    async def skip_updates(self):
        """
        Skip existing updates.
        Only last update will remain on server.
        """
        await self.get_updates(-1)

    # user-facing methods

    async def get_me(self) -> types.User:
        """
        Returns basic information about the bot in form of a User object.

        Telegram documentation: https://core.telegram.org/bots/api#getme
        """
        result = await api.get_me(self.token)
        return types.User.de_json(result)

    async def get_file(self, file_id: str) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
        For the moment, bots can download files of up to 20MB in size.
        On success, a File object is returned.
        It is guaranteed that the link will be valid for at least 1 hour.
        When the link expires, a new one can be requested by calling get_file again.

        Telegram documentation: https://core.telegram.org/bots/api#getfile
        """
        return types.File.de_json(await api.get_file(self.token, file_id))

    async def get_file_url(self, file_id: str) -> str:
        return await api.get_file_url(self.token, file_id)

    async def download_file(self, file_path: str) -> bytes:
        return await api.download_file(self.token, file_path)

    async def log_out(self) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally.
        You MUST log out the bot before running it locally, otherwise there is no guarantee
        that the bot will receive updates.
        After a successful call, you can immediately log in on a local server,
        but will not be able to log in back to the cloud Bot API server for 10 minutes.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#logout
        """
        return await api.log_out(self.token)

    async def close(self) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another.
        You need to delete the webhook before calling this method to ensure that the bot isn't launched again
        after server restart.
        The method will return error 429 in the first 10 minutes after the bot is launched.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#close
        """
        return await api.close(self.token)

    async def set_webhook(
        self,
        url: str,
        certificate: Optional[api.FileObject] = None,
        max_connections: Optional[int] = None,
        ip_address: Optional[str] = None,
        drop_pending_updates: Optional[bool] = None,
        timeout: Optional[float] = None,
    ):
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an
        update for the bot, we will send an HTTPS POST request to the specified url,
        containing a JSON-serialized Update.
        In case of an unsuccessful request, we will give up after a reasonable amount of attempts.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setwebhook

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook integration
        :param certificate: Upload your public key certificate so that the root certificate in use can be checked.
            See our self-signed guide for details.
        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the webhook
            for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot's server,
            and higher values to increase your bot's throughput.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates
            of these types. See Update for a complete list of available update types.
            Specify an empty list to receive all updates regardless of type (default).
            If not specified, the previous setting will be used.
        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address
            resolved through DNS
        :param drop_pending_updates: Pass True to drop all pending updates
        :param timeout: Integer. Request connection timeout
        :return:
        """
        return await api.set_webhook(
            self.token,
            url,
            certificate,
            max_connections,
            [ut.value for ut in self.allowed_updates],
            ip_address,
            drop_pending_updates,
            timeout,
        )

    async def delete_webhook(self, drop_pending_updates: Optional[bool] = None, timeout: Optional[float] = None):
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.

        Telegram documentation: https://core.telegram.org/bots/api#deletewebhook

        :param drop_pending_updates: Pass True to drop all pending updates
        :param timeout: Integer. Request connection timeout
        :return: bool
        """
        return await api.delete_webhook(self.token, drop_pending_updates, timeout)

    async def get_webhook_info(self, timeout=None) -> types.WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters.
        If the bot is using getUpdates, will return an object with the url field empty.

        Telegram documentation: https://core.telegram.org/bots/api#getwebhookinfo

        :param timeout: Integer. Request connection timeout
        :return: On success, returns a WebhookInfo object.
        """
        result = await api.get_webhook_info(self.token, timeout)
        return types.WebhookInfo.de_json(result)

    async def get_user_profile_photos(
        self, user_id: int, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> types.UserProfilePhotos:
        """
        Retrieves the user profile photos of the person with 'user_id'

        Telegram documentation: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id:
        :param offset:
        :param limit:
        :return: API reply.
        """
        result = await api.get_user_profile_photos(self.token, user_id, offset, limit)
        return types.UserProfilePhotos.de_json(result)

    async def get_chat(self, chat_id: Union[int, str]) -> types.Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.

        Telegram documentation: https://core.telegram.org/bots/api#getchat

        :param chat_id:
        :return:
        """
        result = await api.get_chat(self.token, chat_id)
        return types.Chat.de_json(result)

    async def leave_chat(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#leavechat

        :param chat_id:
        :return:
        """
        result = await api.leave_chat(self.token, chat_id)
        return result

    async def get_chat_administrators(self, chat_id: Union[int, str]) -> List[types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat.
        On success, returns an Array of ChatMember objects that contains
        information about all chat administrators except other bots.

        Telegram documentation: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :return: API reply.
        """
        result = await api.get_chat_administrators(self.token, chat_id)
        return [types.ChatMember.de_json(r) for r in result]

    async def get_chat_member_count(self, chat_id: Union[int, str]) -> int:
        """
        Use this method to get the number of members in a chat. Returns Int on success.

        Telegram documentation: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id:
        :return:
        """
        result = await api.get_chat_member_count(self.token, chat_id)
        return result

    async def set_chat_sticker_set(self, chat_id: Union[int, str], sticker_set_name: str) -> types.StickerSet:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Use the field can_set_sticker_set optionally returned in getChat requests to check
        if the bot can use this method. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :return: API reply.
        """
        result = await api.set_chat_sticker_set(self.token, chat_id, sticker_set_name)
        return result

    async def delete_chat_sticker_set(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat
        for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set
        optionally returned in getChat requests to check if the bot can use this method. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletechatstickerset

        :param chat_id:	Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)
        :return: API reply.
        """
        result = await api.delete_chat_sticker_set(self.token, chat_id)
        return result

    async def answer_web_app_query(
        self, web_app_query_id: str, result: types.InlineQueryResultBase
    ) -> types.SentWebAppMessage:
        """
        Use this method to set the result of an interaction with a Web App and
        send a corresponding message on behalf of the user to the chat from which
        the query originated.
        On success, a SentWebAppMessage object is returned.

        Telegram Documentation: https://core.telegram.org/bots/api#answerwebappquery

        :param web_app_query_id: Unique identifier for the query to be answered
        :param result: A JSON-serialized object describing the message to be sent
        :return:
        """

        return await api.answer_web_app_query(self.token, web_app_query_id, result)

    async def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.

        Telegram documentation: https://core.telegram.org/bots/api#getchatmember

        :param chat_id:
        :param user_id:
        :return: API reply.
        """
        result = await api.get_chat_member(self.token, chat_id, user_id)
        return types.ChatMember.de_json(result)

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        entities: Optional[List[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to send text messages.

        Warning: Do not send more than about 4000 characters each message, otherwise you'll risk an HTTP 414 error.
        If you must send more than 4000 characters,
        use the `split_string` or `smart_split` function in util.py.

        Telegram documentation: https://core.telegram.org/bots/api#sendmessage

        :param chat_id:
        :param text:
        :param disable_web_page_preview:
        :param reply_to_message_id:
        :param reply_markup:
        :param parse_mode:
        :param disable_notification: Boolean, Optional. Sends the message silently.
        :param timeout:
        :param entities:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_message(
                self.token,
                chat_id,
                text,
                disable_web_page_preview,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                disable_notification,
                timeout,
                entities,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to forward messages of any kind.

        Telegram documentation: https://core.telegram.org/bots/api#forwardmessage

        :param disable_notification:
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :param protect_content:
        :param timeout:
        :return: API reply.
        """
        return types.Message.de_json(
            await api.forward_message(
                self.token,
                chat_id,
                from_chat_id,
                message_id,
                disable_notification,
                timeout,
                protect_content,
            )
        )

    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.MessageID:
        """
        Use this method to copy messages of any kind.

        Telegram documentation: https://core.telegram.org/bots/api#copymessage

        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :param caption:
        :param parse_mode:
        :param caption_entities:
        :param disable_notification:
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :param timeout:
        :param protect_content:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.MessageID.de_json(
            await api.copy_message(
                self.token,
                chat_id,
                from_chat_id,
                message_id,
                caption,
                parse_mode,
                caption_entities,
                disable_notification,
                reply_to_message_id,
                allow_sending_without_reply,
                reply_markup,
                timeout,
                protect_content,
            )
        )

    async def delete_message(self, chat_id: Union[int, str], message_id: int, timeout: Optional[int] = None) -> bool:
        """
        Use this method to delete message. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: in which chat to delete
        :param message_id: which message to delete
        :param timeout:
        :return: API reply.
        """
        return await api.delete_message(self.token, chat_id, message_id, timeout)

    async def send_dice(
        self,
        chat_id: Union[int, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send dices.

        Telegram documentation: https://core.telegram.org/bots/api#senddice

        :param chat_id:
        :param emoji:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: Message
        """
        return types.Message.de_json(
            await api.send_dice(
                self.token,
                chat_id,
                emoji,
                disable_notification,
                reply_to_message_id,
                reply_markup,
                timeout,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_photo(
        self,
        chat_id: Union[int, str],
        photo: Union[Any, str],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to send photos.

        Telegram documentation: https://core.telegram.org/bots/api#sendphoto

        :param chat_id:
        :param photo:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param caption_entities:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_photo(
                self.token,
                chat_id,
                photo,
                caption,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                disable_notification,
                timeout,
                caption_entities,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[Any, str],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.

        Telegram documentation: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Unique identifier for the message recipient
        :param audio: Audio file to send.
        :param caption:
        :param duration: Duration of the audio in seconds
        :param performer: Performer
        :param title: Track name
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup:
        :param parse_mode:
        :param disable_notification:
        :param timeout:
        :param thumb:
        :param caption_entities:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: Message
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_audio(
                self.token,
                chat_id,
                audio,
                caption,
                duration,
                performer,
                title,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                disable_notification,
                timeout,
                thumb,
                caption_entities,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_voice(
        self,
        chat_id: Union[int, str],
        voice: Union[Any, str],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.

        Telegram documentation: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Unique identifier for the message recipient.
        :param voice:
        :param caption:
        :param duration: Duration of sent audio in seconds
        :param reply_to_message_id:
        :param reply_markup:
        :param parse_mode:
        :param disable_notification:
        :param timeout:
        :param caption_entities:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: Message
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_voice(
                self.token,
                chat_id,
                voice,
                caption,
                duration,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                disable_notification,
                timeout,
                caption_entities,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[Any, str],
        reply_to_message_id: Optional[int] = None,
        caption: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        visible_file_name: Optional[str] = None,
        disable_content_type_detection: Optional[bool] = None,
        data: Optional[Union[Any, str]] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send general files.

        Telegram documentation: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param document: (document) File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param caption: Document caption (may also be used when resending documents by file_id), 0-1024 characters after entities parsing
        :param reply_markup:
        :param parse_mode: Mode for parsing entities in the document caption
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>
        :param caption_entities:
        :param allow_sending_without_reply:
        :param visible_file_name: allows to async define file name that will be visible in the Telegram instead of original file name
        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :param data: function typo compatibility: do not use it
        :param protect_content:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        if data and not (document):
            # function typo miss compatibility
            document = data

        return types.Message.de_json(
            await api.send_data(
                self.token,
                chat_id,
                document,
                "document",
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                timeout=timeout,
                caption=caption,
                thumb=thumb,
                caption_entities=caption_entities,
                allow_sending_without_reply=allow_sending_without_reply,
                disable_content_type_detection=disable_content_type_detection,
                visible_file_name=visible_file_name,
                protect_content=protect_content,
            )
        )

    async def send_sticker(
        self,
        chat_id: Union[int, str],
        sticker: Union[Any, str],
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send .webp stickers.

        Telegram documentation: https://core.telegram.org/bots/api#sendsticker

        :param chat_id:
        :param sticker:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification: to disable the notification
        :param timeout: timeout
        :param allow_sending_without_reply:
        :param protect_content:
        :param data: deprecated, for backward compatibility
        :return: API reply.
        """

        return types.Message.de_json(
            await api.send_data(
                self.token,
                chat_id,
                sticker,
                "sticker",
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                disable_notification=disable_notification,
                timeout=timeout,
                allow_sending_without_reply=allow_sending_without_reply,
                protect_content=protect_content,
            )
        )

    async def send_video(
        self,
        chat_id: Union[int, str],
        video: Union[Any, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        supports_streaming: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as Document).

        Telegram documentation: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param video: Video to send. You can either pass a file_id as String to resend a video that is already on the Telegram servers, or upload a new video file using multipart/form-data.
        :param duration: Duration of sent video in seconds
        :param width: Video width
        :param height: Video height
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the video caption
        :param caption_entities:
        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param protect_content:
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply:
        :param reply_markup:
        :param timeout:
        :param data: deprecated, for backward compatibility
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_video(
                self.token,
                chat_id,
                video,
                duration,
                caption,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                supports_streaming,
                disable_notification,
                timeout,
                thumb,
                width,
                height,
                caption_entities,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[Any, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).

        Telegram documentation: https://core.telegram.org/bots/api#sendanimation

        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param animation: InputFile or String : Animation to send. You can either pass a file_id as String to resend an
            animation that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param width: Integer : Video width
        :param height: Integer : Video height
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param caption: String : Animation caption (may also be used when resending animation by file_id).
        :param parse_mode:
        :param protect_content:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param caption_entities:
        :param allow_sending_without_reply:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            await api.send_animation(
                self.token,
                chat_id,
                animation,
                duration,
                caption,
                reply_to_message_id,
                reply_markup,
                parse_mode,
                disable_notification,
                timeout,
                thumb,
                caption_entities,
                allow_sending_without_reply,
                width,
                height,
                protect_content,
            )
        )

    async def send_video_note(
        self,
        chat_id: Union[int, str],
        data: Union[Any, str],
        duration: Optional[int] = None,
        length: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send
            video messages.

        Telegram documentation: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video note to send. You can either pass a file_id as String to resend
            a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param length: Integer : Video width and height, Can't be None and should be in range of (0, 640)
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param allow_sending_without_reply:
        :param protect_content:
        :return:
        """
        return types.Message.de_json(
            await api.send_video_note(
                self.token,
                chat_id,
                data,
                duration,
                length,
                reply_to_message_id,
                reply_markup,
                disable_notification,
                timeout,
                thumb,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: List[
            Union[
                types.InputMediaAudio,
                types.InputMediaDocument,
                types.InputMediaPhoto,
                types.InputMediaVideo,
            ]
        ],
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
    ) -> List[types.Message]:
        """
        send a group of photos or videos as an album. On success, an array of the sent Messages is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id:
        :param media:
        :param disable_notification:
        :param reply_to_message_id:
        :param timeout:
        :param allow_sending_without_reply:
        :param protect_content:
        :return:
        """
        result = await api.send_media_group(
            self.token,
            chat_id,
            media,
            disable_notification,
            reply_to_message_id,
            timeout,
            allow_sending_without_reply,
            protect_content,
        )
        return [types.Message.de_json(msg) for msg in result]

    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:

        """
        Use this method to send point on the map.

        Telegram documentation: https://core.telegram.org/bots/api#sendlocation

        :param chat_id:
        :param latitude:
        :param longitude:
        :param live_period:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param horizontal_accuracy:
        :param heading:
        :param proximity_alert_radius:
        :param allow_sending_without_reply:
        :param protect_content:
        :return: API reply.
        """
        return types.Message.de_json(
            await api.send_location(
                self.token,
                chat_id,
                latitude,
                longitude,
                live_period,
                reply_to_message_id,
                reply_markup,
                disable_notification,
                timeout,
                horizontal_accuracy,
                heading,
                proximity_alert_radius,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def edit_message_live_location(
        self,
        latitude: float,
        longitude: float,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to edit live location.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude:
        :param longitude:
        :param chat_id:
        :param message_id:
        :param reply_markup:
        :param timeout:
        :param inline_message_id:
        :param horizontal_accuracy:
        :param heading:
        :param proximity_alert_radius:
        :return:
        """
        return types.Message.de_json(
            await api.edit_message_live_location(
                self.token,
                latitude,
                longitude,
                chat_id,
                message_id,
                inline_message_id,
                reply_markup,
                timeout,
                horizontal_accuracy,
                heading,
                proximity_alert_radius,
            )
        )

    async def stop_message_live_location(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Use this method to stop updating a live location message sent by the bot
        or via the bot (for inline bots) before live_period expires.

        Telegram documentation: https://core.telegram.org/bots/api#stopmessagelivelocation

        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :param timeout:
        :return:
        """
        return types.Message.de_json(
            await api.stop_message_live_location(
                self.token,
                chat_id,
                message_id,
                inline_message_id,
                reply_markup,
                timeout,
            )
        )

    async def send_venue(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        foursquare_id: Optional[str] = None,
        foursquare_type: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        google_place_id: Optional[str] = None,
        google_place_type: Optional[str] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send information about a venue.

        Telegram documentation: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Integer or String : Unique identifier for the target chat or username of the target channel
        :param latitude: Float : Latitude of the venue
        :param longitude: Float : Longitude of the venue
        :param title: String : Name of the venue
        :param address: String : Address of the venue
        :param foursquare_id: String : Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, “arts_entertainment/async default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :param google_place_id:
        :param google_place_type:
        :param protect_content:
        :return:
        """
        return types.Message.de_json(
            await api.send_venue(
                self.token,
                chat_id,
                latitude,
                longitude,
                title,
                address,
                foursquare_id,
                foursquare_type,
                disable_notification,
                reply_to_message_id,
                reply_markup,
                timeout,
                allow_sending_without_reply,
                google_place_id,
                google_place_type,
                protect_content,
            )
        )

    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Use this method to send phone contacts.

        Telegram documentation: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Integer or String : Unique identifier for the target chat or username of the target channel
        :param phone_number: String : Contact's phone number
        :param first_name: String : Contact's first name
        :param last_name: String : Contact's last name
        :param vcard: String : Additional data about the contact in the form of a vCard, 0-2048 bytes
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :param protect_content:
        """
        return types.Message.de_json(
            await api.send_contact(
                self.token,
                chat_id,
                phone_number,
                first_name,
                last_name,
                vcard,
                disable_notification,
                reply_to_message_id,
                reply_markup,
                timeout,
                allow_sending_without_reply,
                protect_content,
            )
        )

    async def send_chat_action(self, chat_id: Union[int, str], action: str, timeout: Optional[int] = None) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear
        its typing status).

        Telegram documentation: https://core.telegram.org/bots/api#sendchataction

        :param chat_id:
        :param action:  One of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
                        'record_audio', 'upload_audio', 'upload_document', 'find_location', 'record_video_note',
                        'upload_video_note'.
        :param timeout:
        :return: API reply. :type: boolean
        """
        return await api.send_chat_action(self.token, chat_id, action, timeout)

    async def ban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[int, datetime]] = None,
        revoke_messages: Optional[bool] = None,
    ) -> bool:
        """
        Use this method to ban a user in a group, a supergroup or a channel.
        In the case of supergroups and channels, the user will not be able to return to the chat on their
        own using invite links, etc., unless unbanned first.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#banchatmember

        :param chat_id: Int or string : Unique identifier for the target group or username of the target supergroup
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or
               less than 30 seconds from the current time they are considered to be banned forever
        :param revoke_messages: Bool: Pass True to delete all messages from the chat for the user that is being removed.
                If False, the user will be able to see messages in the group that were sent before the user was removed.
                Always True for supergroups and channels.
        :return: boolean
        """
        return await api.ban_chat_member(self.token, chat_id, user_id, until_date, revoke_messages)

    async def unban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        only_if_banned: Optional[bool] = False,
    ) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or channel.
        The user will not return to the group or channel automatically, but will be able to join via link, etc.
        The bot must be an administrator for this to work. By async default, this method guarantees that after the call
        the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat
        they will also be removed from the chat. If you don't want this, use the parameter only_if_banned.

        Telegram documentation: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel
            (in the format @username)
        :param user_id: Unique identifier of the target user
        :param only_if_banned: Do nothing if the user is not banned
        :return: True on success
        """
        return await api.unban_chat_member(self.token, chat_id, user_id, only_if_banned)

    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[int, datetime]] = None,
        can_send_messages: Optional[bool] = None,
        can_send_media_messages: Optional[bool] = None,
        can_send_polls: Optional[bool] = None,
        can_send_other_messages: Optional[bool] = None,
        can_add_web_page_previews: Optional[bool] = None,
        can_change_info: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup.
        The bot must be an administrator in the supergroup for this to work and must have
        the appropriate admin rights. Pass True for all boolean parameters to lift restrictions from a user.

        Telegram documentation: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Int or String : Unique identifier for the target group or username of the target supergroup or channel (in the format @channelusername)
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :param can_send_messages: Pass True, if the user can send text messages, contacts, locations and venues
        :param can_send_media_messages: Pass True, if the user can send audios, documents, photos, videos, video notes
            and voice notes, implies can_send_messages
        :param can_send_polls: Pass True, if the user is allowed to send polls, implies can_send_messages
        :param can_send_other_messages: Pass True, if the user can send animations, games, stickers and
            use inline bots, implies can_send_media_messages
        :param can_add_web_page_previews: Pass True, if the user may add web page previews to their messages, implies can_send_media_messages
        :param can_change_info: Pass True, if the user is allowed to change the chat title, photo and other settings. Ignored in public supergroups
        :param can_invite_users: Pass True, if the user is allowed to invite new users to the chat, implies can_invite_users
        :param can_pin_messages: Pass True, if the user is allowed to pin messages. Ignored in public supergroups
        :return: True on success
        """
        return await api.restrict_chat_member(
            self.token,
            chat_id,
            user_id,
            until_date,
            can_send_messages,
            can_send_media_messages,
            can_send_polls,
            can_send_other_messages,
            can_add_web_page_previews,
            can_change_info,
            can_invite_users,
            can_pin_messages,
        )

    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        can_change_info: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
        is_anonymous: Optional[bool] = None,
        can_manage_chat: Optional[bool] = None,
        can_manage_video_chats: Optional[bool] = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.

        Telegram documentation: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel (
            in the format @channelusername)
        :param user_id: Int : Unique identifier of the target user
        :param can_change_info: Bool: Pass True, if the administrator can change chat title, photo and other settings
        :param can_post_messages: Bool : Pass True, if the administrator can create channel posts, channels only
        :param can_edit_messages: Bool : Pass True, if the administrator can edit messages of other users, channels only
        :param can_delete_messages: Bool : Pass True, if the administrator can delete messages of other users
        :param can_invite_users: Bool : Pass True, if the administrator can invite new users to the chat
        :param can_restrict_members: Bool: Pass True, if the administrator can restrict, ban or unban chat members
        :param can_pin_messages: Bool: Pass True, if the administrator can pin messages, supergroups only
        :param can_promote_members: Bool: Pass True, if the administrator can add new administrators with a subset
            of his own privileges or demote administrators that he has promoted, directly or indirectly
            (promoted by administrators that were appointed by him)
        :param is_anonymous: Bool: Pass True, if the administrator's presence in the chat is hidden
        :param can_manage_chat: Bool: Pass True, if the administrator can access the chat event log, chat statistics,
            message statistics in channels, see channel members,
            see anonymous administrators in supergroups and ignore slow mode.
            Implied by any other administrator privilege
        :param can_manage_video_chats: Bool: Pass True, if the administrator can manage voice chats
            For now, bots can use this privilege only for passing to other administrators.
        :param can_manage_voice_chats: Deprecated, use can_manage_video_chats
        :return: True on success.
        """

        return await api.promote_chat_member(
            self.token,
            chat_id,
            user_id,
            can_change_info,
            can_post_messages,
            can_edit_messages,
            can_delete_messages,
            can_invite_users,
            can_restrict_members,
            can_pin_messages,
            can_promote_members,
            is_anonymous,
            can_manage_chat,
            can_manage_video_chats,
        )

    async def set_chat_administrator_custom_title(
        self, chat_id: Union[int, str], user_id: int, custom_title: str
    ) -> bool:
        """
        Use this method to set a custom title for an administrator
        in a supergroup promoted by the bot.

        Telegram documentation: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator;
            0-16 characters, emoji are not allowed
        :return: True on success.
        """
        return await api.set_chat_administrator_custom_title(self.token, chat_id, user_id, custom_title)

    async def ban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: Union[int, str]) -> bool:
        """
        Use this method to ban a channel chat in a supergroup or a channel.
        The owner of the chat will not be able to send messages and join live
        streams on behalf of the chat, unless it is unbanned first.
        The bot must be an administrator in the supergroup or channel
        for this to work and must have the appropriate administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#banchatsenderchat

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param sender_chat_id: Unique identifier of the target sender chat
        :return: True on success.
        """
        return await api.ban_chat_sender_chat(self.token, chat_id, sender_chat_id)

    async def unban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: Union[int, str]) -> bool:
        """
        Use this method to unban a previously banned channel chat in a supergroup or channel.
        The bot must be an administrator for this to work and must have the appropriate
        administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unbanchatsenderchat

        :params:
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param sender_chat_id: Unique identifier of the target sender chat
        :return: True on success.
        """
        return await api.unban_chat_sender_chat(self.token, chat_id, sender_chat_id)

    async def set_chat_permissions(self, chat_id: Union[int, str], permissions: types.ChatPermissions) -> bool:
        """
        Use this method to set async default chat permissions for all members.
        The bot must be an administrator in the group or a supergroup for this to work
        and must have the can_restrict_members admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#setchatpermissions

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param permissions: New async default chat permissions
        :return: True on success
        """
        return await api.set_chat_permissions(self.token, chat_id, permissions)

    async def create_chat_invite_link(
        self,
        chat_id: Union[int, str],
        name: Optional[str] = None,
        expire_date: Optional[Union[int, datetime]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
    ) -> types.ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#createchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param name: Invite link name; 0-32 characters
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: Maximum number of users that can be members of the chat simultaneously
        :param creates_join_request: True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified
        :return:
        """
        return types.ChatInviteLink.de_json(
            await api.create_chat_invite_link(
                self.token,
                chat_id,
                name,
                expire_date,
                member_limit,
                creates_join_request,
            )
        )

    async def edit_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: Optional[str] = None,
        name: Optional[str] = None,
        expire_date: Optional[Union[int, datetime]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
    ) -> types.ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#editchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param name: Invite link name; 0-32 characters
        :param invite_link: The invite link to edit
        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :param member_limit: Maximum number of users that can be members of the chat simultaneously
        :param creates_join_request: True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified
        :return:
        """
        return types.ChatInviteLink.de_json(
            await api.edit_chat_invite_link(
                self.token,
                chat_id,
                name,
                invite_link,
                expire_date,
                member_limit,
                creates_join_request,
            )
        )

    async def revoke_chat_invite_link(self, chat_id: Union[int, str], invite_link: str) -> types.ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot.
        Note: If the primary link is revoked, a new link is automatically generated The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#revokechatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel(in the format @channelusername)
        :param invite_link: The invite link to revoke
        :return: API reply.
        """
        return types.ChatInviteLink.de_json(await api.revoke_chat_invite_link(self.token, chat_id, invite_link))

    async def export_chat_invite_link(self, chat_id: Union[int, str]) -> str:
        """
        Use this method to export an invite link to a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return: exported invite link as String on success.
        """
        return await api.export_chat_invite_link(self.token, chat_id)

    async def approve_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        """
        Use this method to approve a chat join request.
        The bot must be an administrator in the chat for this to work and must have
        the can_invite_users administrator right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#approvechatjoinrequest

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :return: True on success.
        """
        return await api.approve_chat_join_request(self.token, chat_id, user_id)

    async def decline_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        """
        Use this method to decline a chat join request.
        The bot must be an administrator in the chat for this to work and must have
        the can_invite_users administrator right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#declinechatjoinrequest

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :return: True on success.
        """
        return await api.decline_chat_join_request(self.token, chat_id, user_id)

    async def set_chat_photo(self, chat_id: Union[int, str], photo: Any) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’ setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :param photo: InputFile: New chat photo, uploaded using multipart/form-data
        :return:
        """
        return await api.set_chat_photo(self.token, chat_id, photo)

    async def delete_chat_photo(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        """
        return await api.delete_chat_photo(self.token, chat_id)

    async def get_my_commands(
        self, scope: Optional[types.BotCommandScope], language_code: Optional[str]
    ) -> List[types.BotCommand]:
        """
        Use this method to get the current list of the bot's commands.
        Returns List of BotCommand on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmycommands

        :param scope: The scope of users for which the commands are relevant.
            async defaults to BotCommandScopeasync default.
        :param language_code: A two-letter ISO 639-1 language code. If empty,
            commands will be applied to all users from the given scope,
            for whose language there are no dedicated commands
        """
        result = await api.get_my_commands(self.token, scope, language_code)
        return [types.BotCommand.de_json(cmd) for cmd in result]

    async def set_chat_menu_button(self, chat_id: Union[int, str] = None, menu_button: types.MenuButton = None) -> bool:
        """
        Use this method to change the bot's menu button in a private chat,
        or the default menu button.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setchatmenubutton

        :param chat_id: Unique identifier for the target private chat.
            If not specified, default bot's menu button will be changed.
        :param menu_button: A JSON-serialized object for the new bot's menu button. Defaults to MenuButtonDefault

        """
        return await api.set_chat_menu_button(self.token, chat_id, menu_button)

    async def get_chat_menu_button(self, chat_id: Union[int, str] = None) -> types.MenuButton:
        """
        Use this method to get the current value of the bot's menu button
        in a private chat, or the default menu button.
        Returns MenuButton on success.

        Telegram Documentation: https://core.telegram.org/bots/api#getchatmenubutton

        :param chat_id: Unique identifier for the target private chat.
            If not specified, default bot's menu button will be returned.
        :return: types.MenuButton

        """
        return types.MenuButton.de_json(await api.get_chat_menu_button(self.token, chat_id))

    async def set_my_default_administrator_rights(
        self, rights: types.ChatAdministratorRights = None, for_channels: bool = None
    ) -> bool:
        """
        Use this method to change the default administrator rights requested by the bot
        when it's added as an administrator to groups or channels.
        These rights will be suggested to users, but they are are free to modify
        the list before adding the bot.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmydefaultadministratorrights

        :param rights: A JSON-serialized object describing new default administrator rights. If not specified, the default administrator rights will be cleared.
        :param for_channels: Pass True to change the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.
        """

        return await api.set_my_default_administrator_rights(self.token, rights, for_channels)

    async def get_my_default_administrator_rights(self, for_channels: bool = None) -> types.ChatAdministratorRights:
        """
        Use this method to get the current default administrator rights of the bot.
        Returns ChatAdministratorRights on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmydefaultadministratorrights

        :param for_channels: Pass True to get the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be returned.
        :return: types.ChatAdministratorRights
        """

        return types.ChatAdministratorRights.de_json(
            await api.get_my_default_administrator_rights(self.token, for_channels)
        )

    async def set_my_commands(
        self,
        commands: List[types.BotCommand],
        scope: Optional[types.BotCommandScope] = None,
        language_code: Optional[str] = None,
    ) -> bool:
        """
        Use this method to change the list of the bot's commands.

        Telegram documentation: https://core.telegram.org/bots/api#setmycommands

        :param commands: List of BotCommand. At most 100 commands can be specified.
        :param scope: The scope of users for which the commands are relevant.
            async defaults to BotCommandScopeasync default.
        :param language_code: A two-letter ISO 639-1 language code. If empty,
            commands will be applied to all users from the given scope,
            for whose language there are no dedicated commands
        :return:
        """
        return await api.set_my_commands(self.token, commands, scope, language_code)

    async def delete_my_commands(
        self,
        scope: Optional[types.BotCommandScope] = None,
        language_code: Optional[int] = None,
    ) -> bool:
        """
        Use this method to delete the list of the bot's commands for the given scope and user language.
        After deletion, higher level commands will be shown to affected users.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletemycommands

        :param scope: The scope of users for which the commands are relevant.
            async defaults to BotCommandScopeasync default.
        :param language_code: A two-letter ISO 639-1 language code. If empty,
            commands will be applied to all users from the given scope,
            for whose language there are no dedicated commands
        """
        return await api.delete_my_commands(self.token, scope, language_code)

    async def set_chat_title(self, chat_id: Union[int, str], title: str) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param title: New chat title, 1-255 characters
        :return:
        """
        return await api.set_chat_title(self.token, chat_id, title)

    async def set_chat_description(self, chat_id: Union[int, str], description: Optional[str] = None) -> bool:
        """
        Use this method to change the description of a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param description: Str: New chat description, 0-255 characters
        :return: True on success.
        """
        return await api.set_chat_description(self.token, chat_id, description)

    async def pin_chat_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = False,
    ) -> bool:
        """
        Use this method to pin a message in a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Int: Identifier of a message to pin
        :param disable_notification: Bool: Pass True, if it is not necessary to send a notification
            to all group members about the new pinned message
        :return:
        """
        return await api.pin_chat_message(self.token, chat_id, message_id, disable_notification)

    async def unpin_chat_message(self, chat_id: Union[int, str], message_id: Optional[int] = None) -> bool:
        """
        Use this method to unpin specific pinned message in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Int: Identifier of a message to unpin
        :return:
        """
        return await api.unpin_chat_message(self.token, chat_id, message_id)

    async def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to unpin a all pinned messages in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinallchatmessages

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return:
        """
        return await api.unpin_all_chat_messages(self.token, chat_id)

    async def edit_message_text(
        self,
        text: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        entities: Optional[List[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        """
        Use this method to edit text and game messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagetext

        :param text:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param parse_mode:
        :param entities:
        :param disable_web_page_preview:
        :param reply_markup:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = await api.edit_message_text(
            self.token,
            text,
            chat_id,
            message_id,
            inline_message_id,
            parse_mode,
            entities,
            disable_web_page_preview,
            reply_markup,
        )
        if type(result) == bool:  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    async def edit_message_media(
        self,
        media: Any,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages.
        If a message is a part of a message album, then it can be edited only to a photo or a video.
        Otherwise, message type can be changed arbitrarily. When inline message is edited, new file can't be uploaded.
        Use previously uploaded file via its file_id or specify a URL.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagemedia

        :param media:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
        """
        result = await api.edit_message_media(self.token, media, chat_id, message_id, inline_message_id, reply_markup)
        if type(result) == bool:  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    async def edit_message_reply_markup(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        """
        Use this method to edit only the reply markup of messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagetypes.ReplyMarkup

        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
        """
        result = await api.edit_message_reply_markup(self.token, chat_id, message_id, inline_message_id, reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    async def send_game(
        self,
        chat_id: Union[int, str],
        game_short_name: str,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Used to send the game.

        Telegram documentation: https://core.telegram.org/bots/api#sendgame

        :param chat_id:
        :param game_short_name:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :param protect_content:
        :return:
        """
        result = await api.send_game(
            self.token,
            chat_id,
            game_short_name,
            disable_notification,
            reply_to_message_id,
            reply_markup,
            timeout,
            allow_sending_without_reply,
            protect_content,
        )
        return types.Message.de_json(result)

    async def set_game_score(
        self,
        user_id: Union[int, str],
        score: int,
        force: Optional[bool] = None,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        disable_edit_message: Optional[bool] = None,
    ) -> Union[types.Message, bool]:
        """
        Sets the value of points in the game to a specific user.

        Telegram documentation: https://core.telegram.org/bots/api#setgamescore

        :param user_id:
        :param score:
        :param force:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param disable_edit_message:
        :return:
        """
        result = await api.set_game_score(
            self.token,
            user_id,
            score,
            force,
            disable_edit_message,
            chat_id,
            message_id,
            inline_message_id,
        )
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    async def get_game_high_scores(
        self,
        user_id: int,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
    ) -> List[types.GameHighScore]:
        """
        Gets top points and game play.

        Telegram documentation: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :return:
        """
        result = await api.get_game_high_scores(self.token, user_id, chat_id, message_id, inline_message_id)
        return [types.GameHighScore.de_json(r) for r in result]

    async def send_invoice(
        self,
        chat_id: Union[int, str],
        title: str,
        description: str,
        invoice_payload: str,
        provider_token: str,
        currency: str,
        prices: List[types.LabeledPrice],
        start_parameter: Optional[str] = None,
        photo_url: Optional[str] = None,
        photo_size: Optional[int] = None,
        photo_width: Optional[int] = None,
        photo_height: Optional[int] = None,
        need_name: Optional[bool] = None,
        need_phone_number: Optional[bool] = None,
        need_email: Optional[bool] = None,
        need_shipping_address: Optional[bool] = None,
        send_phone_number_to_provider: Optional[bool] = None,
        send_email_to_provider: Optional[bool] = None,
        is_flexible: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        provider_data: Optional[str] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        max_tip_amount: Optional[int] = None,
        suggested_tip_amounts: Optional[List[int]] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Sends invoice.

        Telegram documentation: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Unique identifier for the target private chat
        :param title: Product name
        :param description: Product description
        :param invoice_payload: Bot-async defined invoice payload, 1-128 bytes. This will not be displayed to the user,
            use for your internal processes.
        :param provider_token: Payments provider token, obtained via @Botfather
        :param currency: Three-letter ISO 4217 currency code,
            see https://core.telegram.org/bots/payments#supported-currencies
        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param start_parameter: Unique deep-linking parameter that can be used to generate this invoice
            when used as a start parameter
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods
            or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass True, if you require the user's full name to complete the order
        :param need_phone_number: Pass True, if you require the user's phone number to complete the order
        :param need_email: Pass True, if you require the user's email to complete the order
        :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
        :param is_flexible: Pass True, if the final price depends on the shipping method
        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
        :param send_email_to_provider: Pass True, if user's email address should be sent to provider
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty,
            one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button
        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider.
            A detailed description of required fields should be provided by the payment provider.
        :param timeout:
        :param allow_sending_without_reply:
        :param max_tip_amount: The maximum accepted amount for tips in the smallest units of the currency
        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the smallest
            units of the currency.  At most 4 suggested tip amounts can be specified. The suggested tip
            amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
        :param protect_content:
        :return:
        """
        result = await api.send_invoice(
            self.token,
            chat_id,
            title,
            description,
            invoice_payload,
            provider_token,
            currency,
            prices,
            start_parameter,
            photo_url,
            photo_size,
            photo_width,
            photo_height,
            need_name,
            need_phone_number,
            need_email,
            need_shipping_address,
            send_phone_number_to_provider,
            send_email_to_provider,
            is_flexible,
            disable_notification,
            reply_to_message_id,
            reply_markup,
            provider_data,
            timeout,
            allow_sending_without_reply,
            max_tip_amount,
            suggested_tip_amounts,
            protect_content,
        )
        return types.Message.de_json(result)

    # noinspection PyShadowingBuiltins
    async def send_poll(
        self,
        chat_id: Union[int, str],
        question: str,
        options: List[str],
        is_anonymous: Optional[bool] = None,
        type: Optional[str] = None,
        allows_multiple_answers: Optional[bool] = None,
        correct_option_id: Optional[int] = None,
        explanation: Optional[str] = None,
        explanation_parse_mode: Optional[str] = None,
        open_period: Optional[int] = None,
        close_date: Optional[Union[int, datetime]] = None,
        is_closed: Optional[bool] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        allow_sending_without_reply: Optional[bool] = None,
        timeout: Optional[int] = None,
        explanation_entities: Optional[List[types.MessageEntity]] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        """
        Send polls.

        Telegram documentation: https://core.telegram.org/bots/api#sendpoll

        :param chat_id:
        :param question:
        :param options: array of str with answers
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
        :param explanation:
        :param explanation_parse_mode:
        :param open_period:
        :param close_date:
        :param is_closed:
        :param disable_notification:
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :param timeout:
        :param explanation_entities:
        :param protect_content:
        :return:
        """

        if isinstance(question, types.Poll):
            raise RuntimeError("The send_poll signature was changed, please see send_poll function details.")

        explanation_parse_mode = self.parse_mode if (explanation_parse_mode is None) else explanation_parse_mode

        return types.Message.de_json(
            await api.send_poll(
                self.token,
                chat_id,
                question,
                options,
                is_anonymous,
                type,
                allows_multiple_answers,
                correct_option_id,
                explanation,
                explanation_parse_mode,
                open_period,
                close_date,
                is_closed,
                disable_notification,
                reply_to_message_id,
                allow_sending_without_reply,
                reply_markup,
                timeout,
                explanation_entities,
                protect_content,
            )
        )

    async def stop_poll(
        self,
        chat_id: Union[int, str],
        message_id: int,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> types.Poll:
        """
        Stops poll.

        Telegram documentation: https://core.telegram.org/bots/api#stoppoll

        :param chat_id:
        :param message_id:
        :param reply_markup:
        :return:
        """
        return types.Poll.de_json(await api.stop_poll(self.token, chat_id, message_id, reply_markup))

    async def answer_shipping_query(
        self,
        shipping_query_id: str,
        ok: bool,
        shipping_options: Optional[List[types.ShippingOption]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Asks for an answer to a shipping question.

        Telegram documentation: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id:
        :param ok:
        :param shipping_options:
        :param error_message:
        :return:
        """
        return await api.answer_shipping_query(self.token, shipping_query_id, ok, shipping_options, error_message)

    async def answer_pre_checkout_query(
        self, pre_checkout_query_id: int, ok: bool, error_message: Optional[str] = None
    ) -> bool:
        """
        Response to a request for pre-inspection.

        Telegram documentation: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id:
        :param ok:
        :param error_message:
        :return:
        """
        return await api.answer_pre_checkout_query(self.token, pre_checkout_query_id, ok, error_message)

    async def edit_message_caption(
        self,
        caption: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[List[types.MessageEntity]] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        """
        Use this method to edit captions of messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagecaption

        :param caption:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param parse_mode:
        :param caption_entities:
        :param reply_markup:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = await api.edit_message_caption(
            self.token,
            caption,
            chat_id,
            message_id,
            inline_message_id,
            parse_mode,
            caption_entities,
            reply_markup,
        )
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    async def reply_to(
        self,
        message: types.Message,
        text: str,
        parse_mode: Optional[str] = None,
        entities: Optional[List[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`

        :param message:
        :param text:
        :param kwargs:
        :return:
        """
        return await self.send_message(
            message.chat.id,
            text,
            reply_to_message_id=message.message_id,
            parse_mode=parse_mode,
            entities=entities,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            protect_content=protect_content,
            allow_sending_without_reply=allow_sending_without_reply,
            reply_markup=reply_markup,
            timeout=timeout,
        )

    async def answer_inline_query(
        self,
        inline_query_id: str,
        results: List[Any],
        cache_time: Optional[int] = None,
        is_personal: Optional[bool] = None,
        next_offset: Optional[str] = None,
        switch_pm_text: Optional[str] = None,
        switch_pm_parameter: Optional[str] = None,
    ) -> bool:
        """
        Use this method to send answers to an inline query. On success, True is returned.
        No more than 50 results per query are allowed.

        Telegram documentation: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :param results: Array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query
            may be cached on the server.
        :param is_personal: Pass True, if results may be cached on the server side only for
            the user that sent the query.
        :param next_offset: Pass the offset that a client should send in the next query with the same text
            to receive more results.
        :param switch_pm_parameter: If passed, clients will display a button with specified text that switches the user
            to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter
        :param switch_pm_text: 	Parameter for the start message sent to the bot when user presses the switch button
        :return: True means success.
        """
        return await api.answer_inline_query(
            self.token,
            inline_query_id,
            results,
            cache_time,
            is_personal,
            next_offset,
            switch_pm_text,
            switch_pm_parameter,
        )

    async def answer_callback_query(
        self,
        callback_query_id: int,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> bool:
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.

        Telegram documentation: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id:
        :param text:
        :param show_alert:
        :param url:
        :param cache_time:
        :return:
        """
        return await api.answer_callback_query(self.token, callback_query_id, text, show_alert, url, cache_time)

    async def set_sticker_set_thumb(self, name: str, user_id: int, thumb: Union[Any, str] = None):
        """
        Use this method to set the thumbnail of a sticker set.
        Animated thumbnails can be set for animated sticker sets only. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setstickersetthumb

        :param name: Sticker set name
        :param user_id: User identifier
        :param thumb: A PNG image with the thumbnail, must be up to 128 kilobytes in size and have width and height
            exactly 100px, or a TGS animation with the thumbnail up to 32 kilobytes in size;
            see https://core.telegram.org/animated_stickers#technical-requirements

        """
        return await api.set_sticker_set_thumb(self.token, name, user_id, thumb)

    async def get_sticker_set(self, name: str) -> types.StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.

        Telegram documentation: https://core.telegram.org/bots/api#getstickerset

        :param name:
        :return:
        """
        result = await api.get_sticker_set(self.token, name)
        return types.StickerSet.de_json(result)

    async def upload_sticker_file(self, user_id: int, png_sticker: Union[Any, str]) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
        methods (can be used multiple times). Returns the uploaded File on success.


        Telegram documentation: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id:
        :param png_sticker:
        :return:
        """
        result = await api.upload_sticker_file(self.token, user_id, png_sticker)
        return types.File.de_json(result)

    async def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        emojis: str,
        png_sticker: Union[Any, str] = None,
        tgs_sticker: Union[Any, str] = None,
        webm_sticker: Union[Any, str] = None,
        contains_masks: Optional[bool] = None,
        mask_position: Optional[types.MaskPosition] = None,
    ) -> bool:
        """
        Use this method to create new sticker set owned by a user.
        The bot will be able to edit the created sticker set.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id:
        :param name:
        :param title:
        :param emojis:
        :param png_sticker:
        :param tgs_sticker:
        :webm_sticker:
        :param contains_masks:
        :param mask_position:
        :return:
        """
        return await api.create_new_sticker_set(
            self.token,
            user_id,
            name,
            title,
            emojis,
            png_sticker,
            tgs_sticker,
            contains_masks,
            mask_position,
            webm_sticker,
        )

    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Optional[Union[Any, str]] = None,
        tgs_sticker: Optional[Union[Any, str]] = None,
        webm_sticker: Optional[Union[Any, str]] = None,
        mask_position: Optional[types.MaskPosition] = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot.
        It's required to pass `png_sticker` or `tgs_sticker`.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#addstickertoset

        :param user_id:
        :param name:
        :param emojis:
        :param png_sticker: Required if `tgs_sticker` is None
        :param tgs_sticker: Required if `png_sticker` is None
        :webm_sticker:
        :param mask_position:
        :return:
        """
        return await api.add_sticker_to_set(
            self.token,
            user_id,
            name,
            emojis,
            png_sticker,
            tgs_sticker,
            mask_position,
            webm_sticker,
        )

    async def set_sticker_position_in_set(self, sticker: str, position: int) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position . Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker:
        :param position:
        :return:
        """
        return await api.set_sticker_position_in_set(self.token, sticker, position)

    async def delete_sticker_from_set(self, sticker: str) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker:
        :return:
        """
        return await api.delete_sticker_from_set(self.token, sticker)


def sort_by_priority(handlers: list[service_types.Handler]):
    handlers.sort(key=lambda h: h.get("priority") or 1, reverse=True)


async def invoke_handler(
    handler_func: service_types.HandlerFunction,
    update_content: service_types.UpdateContent,
    bot: "AsyncTeleBot",
) -> None:
    handler_signature = signature(handler_func)
    arg_count = len(list(handler_signature.parameters.keys()))
    if arg_count == 1:
        await handler_func(update_content)
        return
    elif arg_count == 2:
        await handler_func(update_content, bot)
        return
    else:
        raise TypeError(
            "Handler function must have one (update content) or two (update content and bot) parameters, "
            + f"but found function with {arg_count} params: {handler_signature}"
        )
