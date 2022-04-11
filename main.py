import os
import telebot
from telebot.types import InputMediaPhoto
import command_low_price
import command_history
from datetime import date
from dotenv import load_dotenv
from loguru import logger
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


load_dotenv()
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
command_history.init_hotels()
users = {}


class User:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.num_hotel = 0
        self.num_foto = 0
        self.price_min = 0
        self.price_max = 0
        self.command = 0
        self.image = False
        self.checkIn = 0
        self.checkOut = 0


@bot.message_handler(commands=['start'])
def greetings(message) -> None:
    users[message.chat.id] = User(message.chat.id)
    logger.info(f'user: {message.chat.id} enter command "start"')
    bot.send_message(message.from_user.id, "Напишите /help")


@bot.message_handler(commands=['history'])
def get_history(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter command "history"')
    new_result = command_history.read_hotels_info(my_user.chat_id)
    for i in new_result:
        com = ''
        if i['name_command'] == 1:
            com = "/lowprice"
        elif i['name_command'] == 2:
            com = "/highprice"
        elif i['name_command'] == 3:
            com = "/bestdeal"
        check_in = i['checkIn'].split('-')
        check_out = i['checkOut'].split('-')
        check_in = date(int(check_in[0]), int(check_in[1]), int(check_in[2]))
        check_out = date(int(check_out[0]), int(check_out[1]), int(check_out[2]))
        total_day = check_out - check_in
        text = f"command: {com}\ntime: {i['data']}\nname: {i['name']}\nstar_rating: {i['star_rating']}\n" \
               f"address: {i['address']}\nguest_reviews: {i['guest_reviews']}\ndistance: {i['distance']}\n" \
               f"price: {i['price']}\ncheckIn: {i['checkIn']}\ncheckOut: {i['checkOut']}"
        if i['price']:
            price_per_night = float(i['price']) / total_day.days
            price_per_night = round(price_per_night, 2)
            text += f'\nprice per night: {price_per_night}\n'
        else:
            text += '\n'
        text += f"site: https://ru.hotels.com/ho{i['hotel_id']}\n"
        bot.send_message(message.from_user.id, text, disable_web_page_preview=True)
        if i['exists_photo'] == 2:
            names_photo = command_history.read_photo(i['hotel_id'])
            medias = list()
            for i_photo in names_photo:
                medias.append(InputMediaPhoto(i_photo))
            bot.send_media_group(message.from_user.id, medias)
    else:
        bot.send_message(message.from_user.id, "История поиска закончилась.")


def data_in(message) -> None:
    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today()).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    bot.register_next_step_handler(message, data_check)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal1(c) -> None:
    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected check in {result}\nДанные введены корректно (Да/Нет)?",
                              c.message.chat.id,
                              c.message.message_id)
        my_user = users[c.message.chat.id]
        my_user.checkIn = result
        logger.info(f'user: {c.message.chat.id} enter check in: "{my_user.checkIn}"')


def data_check(message) -> None:
    logger.info(f'user: {message.chat.id} verification data check in? "{message.text}"')
    if message.text.lower() == 'да' or message.text.lower() == 'yes':
        data_out(message)
    else:
        data_in(message)


def data_out(message) -> None:
    calendar, step = DetailedTelegramCalendar(calendar_id=2).build()
    bot.send_message(message.chat.id,
                     f"Select {LSTEP[step]}",
                     reply_markup=calendar)
    bot.register_next_step_handler(message, get_num_hotel)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal2(c) -> None:
    my_user = users[c.message.chat.id]
    result, key, step = DetailedTelegramCalendar(calendar_id=2, min_date=my_user.checkIn).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Select {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"You selected check out {result}\nКоличество отелей, которое необходимо вывести?",
                              c.message.chat.id,
                              c.message.message_id)
        my_user = users[c.message.chat.id]
        my_user.checkOut = result
        logger.info(f'user: {c.message.chat.id} enter data check out: "{my_user.checkOut}"')


@bot.message_handler(content_types=['text', 'photo'])
def get_text_messages(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter: "{message.text}"')
    if message.text == "/lowprice":
        my_user.command = 1
        bot.send_message(message.from_user.id, "В каком городе будем искать?")
        bot.register_next_step_handler(message, get_city)
    elif message.text == "/highprice":
        my_user.command = 2
        bot.send_message(message.from_user.id, "В каком городе будем искать?")
        bot.register_next_step_handler(message, get_city)
    elif message.text == "/bestdeal":
        my_user.command = 3
        bot.send_message(message.from_user.id, "В каком городе будем искать?")
        bot.register_next_step_handler(message, get_city)
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "/help - список команд"
                                               "\n/lowprice - Узнать топ самых дешёвых отелей в городе"
                                               "\n/highprice - Узнать топ самых дорогих отелей в городе"
                                               "\n/bestdeal - Узнать топ отелей, наиболее подходящих по цене"
                                               " и расположению от центра"
                                               "\n/history - Узнать историю поиска отелей")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


def get_city(message) -> None:
    logger.info(f'user: {message.chat.id} enter city: "{message.text}"')
    my_user = users[message.chat.id]
    my_user.city = message.text
    data_in(message)


def get_num_hotel(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter number hotels: "{message.text}"')
    if message.text.isdigit():
        my_user.num_hotel = int(message.text)
        bot.send_message(message.from_user.id, "Необходим показ фотографий для каждого отеля (“Да/Нет”)")
        bot.register_next_step_handler(message, get_choice_foto)
    else:
        bot.send_message(message.from_user.id, "Введите количество отелей правильно.")
        bot.register_next_step_handler(message, get_num_hotel)


def get_choice_foto(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter need photo? "{message.text}"')
    if message.text.lower() == 'да' or message.text.lower() == 'yes':
        bot.send_message(message.from_user.id, "Максимальное количество фотографий?")
        my_user.image = True
        bot.register_next_step_handler(message, get_num_foto)
    else:
        my_user.image = False
        if my_user.command == 3:
            bot.send_message(message.from_user.id, "Укажите минимальную цену поиска:")
            bot.register_next_step_handler(message, get_min_price)
        else:
            bot.send_message(message.from_user.id, "Фотографий не будет")
            get_res_low(message)


def get_num_foto(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter number photo: "{message.text}"')
    if message.text.isdigit():
        my_user.num_foto = int(message.text)
        if my_user.command == 3:
            bot.send_message(message.from_user.id, "Укажите минимальную цену поиска:")
            bot.register_next_step_handler(message, get_min_price)
        else:
            get_res_low(message)
    else:
        bot.send_message(message.from_user.id, "Введите максимальное количество фотографий правильно.")
        bot.register_next_step_handler(message, get_num_foto)


def get_min_price(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter min price: "{message.text}"')
    if message.text.isdigit():
        my_user.price_min = int(message.text)
        bot.send_message(message.from_user.id, "Укажите максимальную цену:")
        bot.register_next_step_handler(message, get_max_price)
    else:
        bot.send_message(message.from_user.id, "Укажите минимальную цену правильно.")
        bot.register_next_step_handler(message, get_min_price)


def get_max_price(message) -> None:
    my_user = users[message.chat.id]
    logger.info(f'user: {message.chat.id} enter max price: "{message.text}"')
    if message.text.isdigit():
        my_user.price_max = int(message.text)
        get_res_low(message)
    else:
        bot.send_message(message.from_user.id, "Укажите максимальную цену правильно.")
        bot.register_next_step_handler(message, get_max_price)


def get_res_low(message) -> None:
    my_user = users[message.chat.id]
    result_list = command_low_price.command(my_user.chat_id, my_user.command, my_user.city, my_user.num_hotel,
                                            my_user.checkIn, my_user.checkOut, my_user.image, my_user.num_foto,
                                            my_user.price_min, my_user.price_max)
    if not result_list:
        bot.send_message(message.from_user.id, f'Отели в городе {my_user.city} c заданными параметрами не найдены')
    else:
        for i, i_data in enumerate(result_list):
            text = ''
            for i_key, i_val in i_data.items():
                if i_key != 'hotel_id' and i_key != 'photo' and i_key != 'exists_photo' \
                        and i_key != 'data' and i_key != 'name_command' and i_key != 'user_id':
                    text += f'{i_key}: {i_val}\n'
            if 'hotel_id' in i_data:
                text += f'site: https://ru.hotels.com/ho{i_data["hotel_id"]}\n'
            if 'price' in i_data:
                check_in = i_data['checkIn']
                check_out = i_data['checkOut']
                total_day = check_out - check_in
                price_per_night = float(i_data['price']) / total_day.days
                price_per_night = round(price_per_night, 2)
                text += f'price per night: {price_per_night}\n'
            else:
                text += '\n'
            bot.send_message(message.from_user.id, text, disable_web_page_preview=True)
            if 'photo' in i_data:
                medias = list()
                for i_url in i_data['photo']:
                    medias.append(InputMediaPhoto(i_url))
                bot.send_media_group(message.from_user.id, medias)


logger.add("file.log", format="{time} {level} {message}", filter="", level="INFO", rotation="1 week")
bot.polling(none_stop=True, interval=0)
