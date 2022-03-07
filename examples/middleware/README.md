# Middlewares

## Type of middlewares in pyTelegramBotAPI
Currently, synchronous version of pyTelegramBotAPI has two types of middlewares:

- Class-based middlewares
- Function-based middlewares

## Purpose of middlewares
Middlewares are designed to get update before handler's execution.

## Class-based middlewares
This type of middleware has more functionality compared to function-based one.

Class based middleware should be instance of `telebot.handler_backends.BaseMiddleware.`

Each middleware should have 2 main functions:

`pre_process` -> is a method of class which receives update, and data.

Data - is a dictionary, which could be passed right to handler, and `post_process` function.

`post_process` -> is a function of class which receives update, data, and exception, that happened in handler. If handler was executed correctly - then exception will equal to None.

## Function-based middlewares
To use function-based middleware, you should set `apihelper.ENABLE_MIDDLEWARE = True`.
This type of middleware is created by using a decorator for middleware.
With this type middleware, you can retrieve update immediately after update came. You should set update_types as well.

## Why class-based middlewares are better?
- You can pass data between post, pre_process functions, and handler.
- If there is an exception in handler, you will get exception parameter with exception class in post_process.
- Has post_process -> method which works after the handler's execution.

## Take a look at examples for more.
