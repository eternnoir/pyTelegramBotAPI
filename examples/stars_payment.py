# Import required libraries
import telebot 
from telebot import types  

bot = telebot.TeleBot('TOKEN')

# Product prices in stars
PRICES = {
    '10 Stars': 10,   # $1.00 - Entry level package
    '50 Stars': 45,   # $4.50 - Medium package with 10% discount
    '100 Stars': 80,  # $8.00 - Large package with 20% discount
    '500 Stars': 350  # $35.00 - Bulk package with 30% discount
}

# Handler for /start command - Then the bot will send amount stars to purchase
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a custom keyboard with 2 buttons per row
    markup = types.ReplyKeyboardMarkup(row_width=2)
    # Generate buttons for each product in our PRICES dictionary
    buttons = [types.KeyboardButton(product) for product in PRICES.keys()]
    # Add all buttons to the markup
    markup.add(*buttons)
    
    # Send welcome message with the custom keyboard
    bot.reply_to(message, 
                 "Welcome to Stars Payment Bot!\nPlease select amount of stars to purchase:",
                 reply_markup=markup)

# Handler for when user selects a product from the keyboard
@bot.message_handler(func=lambda message: message.text in PRICES.keys())
def handle_product_selection(message):
    # Get selected product and its price
    product = message.text
    price = PRICES[product]
    
    # Create invoice with product details
    prices = [types.LabeledPrice(label=product, amount=price)]
    
    # Send payment invoice to user
    bot.send_invoice(
        message.chat.id,  # Chat ID to send invoice to
        title=f"Purchase {product}",  # Title of the invoice
        description=f"Buy {product} for your account",  # Description shown on invoice
        provider_token='',  # Payment provider token (empty for testing)
        currency='XTR',  # Currency code
        prices=prices,  # List of prices (we only have one item)
        start_parameter='stars-payment',  # Deep-linking parameter
        invoice_payload=product  # Payload to identify the product after payment
    )

# Pre-checkout handler - Called before payment is completed
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# Handler for successful payments
@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    # Get the product that was purchased from the invoice payload
    product = message.successful_payment.invoice_payload
    bot.reply_to(message, 
                 f"Payment for {product} successful!")
bot.polling()
