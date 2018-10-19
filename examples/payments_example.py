import telebot
from telebot.types import LabeledPrice, ShippingOption

token = '1234567890:AAAABBBBCCCCDDDDeeeeFFFFgggGHHHH'
provider_token = '1234567890:TEST:AAAABBBBCCCCDDDD'  # @BotFather -> Bot Settings -> Payments
bot = telebot.TeleBot(token)

# More about Payments: https://core.telegram.org/bots/payments

prices = [LabeledPrice(label='Working Time Machine', amount=5750), LabeledPrice('Gift wrapping', 500)]

shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 1000)),
    ShippingOption(id='pickup', title='Local pickup').add_price(LabeledPrice('Pickup', 300))]


@bot.message_handler(commands=['start'])
def command_start(message):
    bot.send_message(message.chat.id,
                     "Hello, I'm the demo merchant bot."
                     " I can sell you a Time Machine."
                     " Use /buy to order one, /terms for Terms and Conditions")


@bot.message_handler(commands=['terms'])
def command_terms(message):
    bot.send_message(message.chat.id,
                     'Thank you for shopping with our demo bot. We hope you like your new time machine!\n'
                     '1. If your time machine was not delivered on time, please rethink your concept of time and try again.\n'
                     '2. If you find that your time machine is not working, kindly contact our future service workshops on Trappist-1e.'
                     ' They will be accessible anywhere between May 2075 and November 4000 C.E.\n'
                     '3. If you would like a refund, kindly apply for one yesterday and we will have sent it to you immediately.')


@bot.message_handler(commands=['buy'])
def command_pay(message):
    bot.send_message(message.chat.id,
                     "Real cards won't work with me, no money will be debited from your account."
                     " Use this test card number to pay for your Time Machine: `4242 4242 4242 4242`"
                     "\n\nThis is your demo invoice:", parse_mode='Markdown')
    bot.send_invoice(message.chat.id, title='Working Time Machine',
                     description='Want to visit your great-great-great-grandparents?'
                                 ' Make a fortune at the races?'
                                 ' Shake hands with Hammurabi and take a stroll in the Hanging Gardens?'
                                 ' Order our Working Time Machine today!',
                     provider_token=provider_token,
                     currency='usd',
                     photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',
                     photo_height=512,  # !=0/None or picture won't be shown
                     photo_width=512,
                     photo_size=512,
                     is_flexible=False,  # True If you need to set up Shipping Fee
                     prices=prices,
                     start_parameter='time-machine-example',
                     invoice_payload='HAPPY FRIDAYS COUPON')


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id,
                     'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
                     'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
                         message.successful_payment.total_amount / 100, message.successful_payment.currency),
                     parse_mode='Markdown')


bot.skip_pending = True
bot.polling(none_stop=True, interval=0)
