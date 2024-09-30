from telebot import async_telebot, asyncio_filters, types
from telebot.asyncio_storage import StateMemoryStorage
from telebot.states import State, StatesGroup
from telebot.states.asyncio.context import StateContext
from telebot.types import ReplyParameters

# Initialize the bot
state_storage = StateMemoryStorage()  # don't use this in production; switch to redis
bot = async_telebot.AsyncTeleBot("TOKEN", state_storage=state_storage)


# Define states
class MyStates(StatesGroup):
    name = State()
    age = State()
    color = State()
    hobby = State()


# Start command handler
@bot.message_handler(commands=["start"])
async def start_ex(message: types.Message, state: StateContext):
    await state.set(MyStates.name)
    await bot.send_message(
        message.chat.id,
        "Hello! What is your first name?",
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )


# Cancel command handler
@bot.message_handler(state="*", commands=["cancel"])
async def any_state(message: types.Message, state: StateContext):
    await state.delete()
    await bot.send_message(
        message.chat.id,
        "Your information has been cleared. Type /start to begin again.",
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )


# Handler for name input
@bot.message_handler(state=MyStates.name)
async def name_get(message: types.Message, state: StateContext):
    await state.set(MyStates.age)
    await bot.send_message(
        message.chat.id, "How old are you?",
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )
    await state.add_data(name=message.text)


# Handler for age input
@bot.message_handler(state=MyStates.age, is_digit=True)
async def ask_color(message: types.Message, state: StateContext):
    await state.set(MyStates.color)
    await state.add_data(age=message.text)

    # Define reply keyboard for color selection
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    colors = ["Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Other"]
    buttons = [types.KeyboardButton(color) for color in colors]
    keyboard.add(*buttons)

    await bot.send_message(
        message.chat.id,
        "What is your favorite color? Choose from the options below.",
        reply_markup=keyboard,
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )


# Handler for color input
@bot.message_handler(state=MyStates.color)
async def ask_hobby(message: types.Message, state: StateContext):
    await state.set(MyStates.hobby)
    await state.add_data(color=message.text)

    # Define reply keyboard for hobby selection
    keyboard = types.ReplyKeyboardMarkup(row_width=2)
    hobbies = ["Reading", "Traveling", "Gaming", "Cooking"]
    buttons = [types.KeyboardButton(hobby) for hobby in hobbies]
    keyboard.add(*buttons)

    await bot.send_message(
        message.chat.id,
        "What is one of your hobbies? Choose from the options below.",
        reply_markup=keyboard,
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )


# Handler for hobby input; use filters to ease validation
@bot.message_handler(
    state=MyStates.hobby, text=["Reading", "Traveling", "Gaming", "Cooking"]
)
async def finish(message: types.Message, state: StateContext):
    async with state.data() as data:
        name = data.get("name")
        age = data.get("age")
        color = data.get("color")
        hobby = message.text  # Get the hobby from the message text

        # Provide a fun fact based on color
        color_facts = {
            "Red": "Red is often associated with excitement and passion.",
            "Green": "Green is the color of nature and tranquility.",
            "Blue": "Blue is known for its calming and serene effects.",
            "Yellow": "Yellow is a cheerful color often associated with happiness.",
            "Purple": "Purple signifies royalty and luxury.",
            "Orange": "Orange is a vibrant color that stimulates enthusiasm.",
            "Other": "Colors have various meanings depending on context.",
        }
        color_fact = color_facts.get(
            color, "Colors have diverse meanings, and yours is unique!"
        )

        msg = (
            f"Thank you for sharing! Here is a summary of your information:\n"
            f"First Name: {name}\n"
            f"Age: {age}\n"
            f"Favorite Color: {color}\n"
            f"Fun Fact about your color: {color_fact}\n"
            f"Favorite Hobby: {hobby}"
        )

    await bot.send_message(
        message.chat.id, msg, parse_mode="html",
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )
    await state.delete()


# Handler for incorrect age input
@bot.message_handler(state=MyStates.age, is_digit=False)
async def age_incorrect(message: types.Message):
    await bot.send_message(
        message.chat.id,
        "Please enter a valid number for age.",
        reply_parameters=ReplyParameters(message_id=message.message_id),
    )


# Add custom filters
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())
bot.add_custom_filter(asyncio_filters.TextMatchFilter())

# necessary for state parameter in handlers.
from telebot.states.asyncio.middleware import StateMiddleware

bot.setup_middleware(StateMiddleware(bot))

# Start polling
import asyncio

asyncio.run(bot.polling())
