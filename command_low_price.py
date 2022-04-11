import json
import requests
import os
import command_history
import time
import re
from dotenv import load_dotenv
from loguru import logger
from typing import List, Dict
from datetime import date


def search_city(user_id: int, city: str, lang: str, headers: Dict) -> int:
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": city, "locale": lang, "currency": "USD"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    try:
        data = json.loads(response.text)
        city_group = list(filter(lambda x: x["group"] == 'CITY_GROUP', data["suggestions"]))
        list_city = list(filter(lambda x: x['type'] == 'CITY', city_group[0]['entities']))
        city_id = list_city[0]['destinationId']
        logger.info(f'user: {user_id} find id city "{city_id}"')
    except Exception as err:
        with open('error.log', 'a', encoding='utf-8') as file:
            cur_time = time.ctime(time.time())
            file.write(f'{cur_time}, пользователь: {user_id} - ошибка поиска города {err}.\nДанные поиска:'
                       f'\nгород: {city}')
            logger.info(f'user: {user_id} no find id city')
            city_id = None
    finally:
        return city_id


def search_hotels(user_id: int, var: int, city_id: int, max_num: int, check_in: date, check_out: date, headers: Dict,
                  price_min: int = 0, price_max: int = 0) -> List[Dict]:
    url = "https://hotels4.p.rapidapi.com/properties/list"
    querystring = {}
    if var == 1:
        querystring = {"destinationId": f'{city_id}', "pageNumber": "1", "pageSize": f'{max_num}',
                       "checkIn": f'{check_in}', "checkOut": f'{check_out}', "adults1": "1",
                       "sortOrder": "PRICE", "locale": 'ru_RU', "currency": 'RUB'}
    elif var == 2:
        querystring = {"destinationId": f'{city_id}', "pageNumber": "1", "pageSize": f'{max_num}',
                       "checkIn": f'{check_in}', "checkOut": f'{check_out}', "adults1": "1",
                       "sortOrder": "PRICE_HIGHEST_FIRST", "locale": 'ru_RU', "currency": 'RUB'}
    elif var == 3:
        querystring = {"destinationId": f'{city_id}', "pageNumber": "1", "pageSize": f'{max_num}',
                       "checkIn": f'{check_in}', "checkOut": f'{check_out}', "adults1": "1", "priceMin": f'{price_min}',
                       "priceMax": f'{price_max}', "sortOrder": "BEST_SELLER", "locale": 'ru_RU', "currency": 'RUB'}

    response2 = requests.request("GET", url, headers=headers, params=querystring)
    result = []
    try:
        data2 = json.loads(response2.text)
        result = data2['data']['body']['searchResults']['results']
        if result:
            logger.info(f'user: {user_id} find hotels')
        else:
            logger.info(f'user: {user_id} no find hotels')
    except Exception as err:
        with open('error.log', 'a', encoding='utf-8') as file:
            cur_time = time.ctime(time.time())
            file.write(f'{cur_time}, пользователь: {user_id} - ошибка поиска отелей в городе {err}.\nДанные поиска:'
                       f'\nгород: {city_id}'
                       f'\nколичество отелей: {max_num}'
                       f'\nдаты прибытия/отбытия: {check_in} {check_out}'
                       f'\nминимальная/максимальная цена (если указано): {price_min} / {price_max}')
            logger.info(f'user: {user_id} no find hotels')
    finally:
        return result


def search_photos(user_id, hotel_id, max_num_image, headers, querystring) -> List[Dict]:
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    response = requests.request("GET", url, headers=headers, params=querystring)
    list_photos = list()
    try:
        data = json.loads(response.text)
        list_photos = data['hotelImages']
        logger.info(f'user: {user_id} find photos hotel "{hotel_id}"')
    except Exception as err:
        with open('error.log', 'a', encoding='utf-8') as file:
            cur_time = time.ctime(time.time())
            file.write(f'{cur_time}, пользователь: {user_id} - ошибка поиска фотографий {err}.\nДанные поиска:'
                       f'\nотель: {hotel_id}'
                       f'\nколичество фотографий: {max_num_image}')
            logger.info(f'user: {user_id} no find photos hotel "{hotel_id}"')
    finally:
        return list_photos


def parsing_data(data_list: Dict) -> Dict:
    my_dict = dict()
    for i_key, i_val in data_list.items():
        if i_key == 'name':
            my_dict['name'] = i_val
        elif i_key == 'starRating':
            my_dict['star_rating'] = i_val
        elif i_key == 'address':
            if 'streetAddress' in i_val:
                adr = i_val['streetAddress']
            else:
                adr = 'Нет адреса на сайте'
            my_dict['address'] = adr
        elif i_key == 'guestReviews':
            if 'unformattedRating' in i_val:
                rating = i_val['unformattedRating']
            else:
                rating = None
            my_dict['guest_reviews'] = rating
        elif i_key == 'ratePlan':
            if 'current' in i_val['price']:
                price = str(i_val['price']['exactCurrent'])
            else:
                price = None
            my_dict['price'] = price
        elif i_key == 'landmarks':
            if 'distance' in i_val[0]:
                dist = i_val[0]['distance']
            else:
                dist = None
            my_dict['distance'] = dist
        elif i_key == 'id':
            my_dict['hotel_id'] = i_val
    else:
        if not ('name' in my_dict):
            my_dict['name'] = 'Нет информации'
        if not ('hotel_id' in my_dict):
            my_dict['hotel_id'] = None
        if not ('distance' in my_dict):
            my_dict['distance'] = None
        if not ('price' in my_dict):
            my_dict['price'] = None
        if not ('guest_reviews' in my_dict):
            my_dict['guest_reviews'] = None
        if not ('address' in my_dict):
            my_dict['address'] = 'Нет информации'
        if not ('star_rating' in my_dict):
            my_dict['star_rating'] = None
    return my_dict


@logger.catch
def command(user_id: int, var: int, city_search: str, max_num: int, check_in: date, check_out: date, image=False,
            max_num_image: int = 0, price_min: int = 0, price_max: int = 0) -> List[Dict]:
    load_dotenv()
    headers = {
        'x-rapidapi-host': os.getenv('HOST_SITE'),
        'x-rapidapi-key': os.getenv('HOST_KEY')
    }
    list_result = []
    match = re.fullmatch(r'[а-яА-ЯёЁ -]+', f'{city_search}')
    if match:
        lang = "ru_RU"
    else:
        lang = "en_US"

    destination_id = search_city(user_id, city_search, lang, headers)
    if not destination_id:
        list_result = [{'Не нашелся город': city_search}]
        return list_result
    data_hotels = search_hotels(user_id, city_id=destination_id, headers=headers, max_num=max_num, var=var,
                                check_in=check_in, check_out=check_out, price_min=price_min, price_max=price_max)

    if not data_hotels:
        list_result = [{'Нет отелей': f'Отели в городе {city_search} c заданными параметрами не найдены'}]
        return list_result

    for i, i_data in enumerate(data_hotels):
        list_result.append(dict())
        list_result[i] = parsing_data(i_data)
        if image:
            list_result[i]['exists_photo'] = 2
        else:
            list_result[i]['exists_photo'] = 1
        list_result[i]['name_command'] = var
        list_result[i]['user_id'] = user_id
        list_result[i]['checkIn'] = check_in
        list_result[i]['checkOut'] = check_out
        command_history.add_hotel_info(list_result[i])

    if image:
        for i, i_dict in enumerate(list_result):
            id_hotel = i_dict['hotel_id']
            querystring = {"id": id_hotel}
            data_photos = search_photos(user_id=user_id, hotel_id=id_hotel, max_num_image=max_num_image,
                                        headers=headers, querystring=querystring)
            if not data_photos:
                value = 'https://upload.wikimedia.org/wikipedia/commons/9/9a/' \
                        '%D0%9D%D0%B5%D1%82_%D1%84%D0%BE%D1%82%D0%BE.png'
                list_result[i]['photo'] = value
                command_history.add_photo(value, id_hotel)
                break
            hotel_image = list()
            for i_cnt, i_data in enumerate(data_photos):
                if i_cnt == max_num_image:
                    list_result[i]['photo'] = hotel_image
                    break
                for key, value in i_data.items():
                    if key == 'baseUrl':
                        value = value.replace('{size}', 'b')
                        hotel_image.append(value)
                        command_history.add_photo(value, id_hotel)

    return list_result
