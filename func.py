import datetime
import random

from aiogram.filters import BaseFilter
from aiogram.types import BotCommand, BotCommandScopeDefault, Message, FSInputFile
from aiogram.utils.markdown import hlink

from loader import bot, crypto, db, scheduler
from string import digits

import asyncio

import pytz
from aiocryptopay.exceptions import CodeErrorFactory
from aiogram import types
from config import *
from keybords import *

async def set_default_commands():
    await bot.set_my_commands([
        BotCommand(command="/start", description="Запустить бота")
    ], scope=BotCommandScopeDefault())



async def scheduler_jobs():
    scheduler.add_job(del_order_day, "cron", day='*', hour=0, minute=0)
    scheduler.add_job(fake_game_adm, 'interval', seconds=TIMER)
    scheduler.add_job(warning_check_day, "cron", day='*', hour=23, minute=55)

async def del_order_day():
    db.del_stats_day()
    print('Обновил день')
    all_cheks = await crypto.get_checks(asset='USDT', status='active')
    if all_cheks is None:
        return await bot.send_message(chat_id=channal_id, text="<b>⌛️ Активные чеки удалены</b>")

    for i in all_cheks:
        try:
            await crypto.delete_check(i.check_id)
        except Exception:
            continue
    await bot.send_message(chat_id=channal_id, text="<b>⌛️ Активные чеки удалены</b>")

async def warning_check_day():
    await bot.send_message(chat_id=channal_id, text='<b>⏳ Через 5 минут будет удаление всех активных чеков</b>')







async def get_transfer_channal():
    info = await crypto.get_transfers(asset='USDT', count=1)
    date = info[0].completed_at
    user_id = info[0].user_id
    amount = info[0].amount
    transfer_id = info[0].transfer_id
    date = date.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S')
    user = str(user_id)[5:]
    return await bot.send_message(chat_id=ID_SEND_TRANSFER, text='💸 <b>Выплата победителю:</b>\n'
                                                          f'<b>┠User_id:</b> <code>*****{user}</code>\n'
                                                          f'<b>┠Идентификатор перевода:</b> <code>{transfer_id}</code>\n'
                                                          f'<b>┠Дата:</b> <code>{date}</code>\n'
                                                          f'<b>┖Сумма:</b> <code>{round(float(amount), 2)}$</code>', reply_markup=send_okey())


async def send_message_win_users(usdt, result_win_amount, message_id, url, status=None):
    photo = FSInputFile('photos/Wins.png')
    if status != 'CHECK':
        return await bot.send_photo(chat_id=channal_id, photo=photo,
                                    caption=f'<b><blockquote>🟢 Победа! \n\n'
                                            f'💸 Выигрыш: {round(float(usdt), 2)}$ ({result_win_amount}₽)\n'
                                            f'🕊 Средства автоматически поступили на ваш кошелек CryptoBot\n'
                                            f'♻️ Удачи в следующих играх!</blockquote></b>',
                                    reply_to_message_id=message_id, reply_markup=send_stavka())
    else:
        return await bot.send_photo(chat_id=channal_id, photo=photo,
                                    caption=f'<b><blockquote>🟢 Победа! \n\n'
                                            f'💸 Выигрыш: {round(float(usdt), 2)}$ ({result_win_amount}₽)\n'
                                            f'🕊 Забрать свой выигрыш вы можете по кнопке ниже\n'
                                            f'♻️ Удачи в следующих играх!</blockquote></b>',
                                    reply_to_message_id=message_id, reply_markup=kb_send_chek(url=url))



async def fake_send_message_win_users(amount, KEF, rubs_price, message_id):
    usdt = float(amount) * KEF

    rub = float(rubs_price) * float(usdt)
    result_win_amount = round(float(rub), 2)
    await asyncio.sleep(5)
    fake_users = "".join(random.choice(digits) for _ in range(0, 5))
    fake_transfer = "".join(random.choice(digits) for _ in range(0, 6))
    date = datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S')

    photo = FSInputFile('photos/Wins.png')
    await bot.send_photo(chat_id=channal_id, photo=photo,
                         caption=f'<b><blockquote>🔵 Победа! \n\n'
                                 f'💸 Выигрыш: {round(float(usdt), 2)}$ ({result_win_amount}₽)\n'
                                 f'🕊 Средства автоматически поступили на ваш кошелек CryptoBot\n'
                                 f'💙 Удачи в следующих играх!</blockquote></b>',
                         reply_to_message_id=message_id, reply_markup=send_stavka())

    return await bot.send_message(chat_id=ID_SEND_TRANSFER, text='💸 <b>Выплата победителю:</b>\n'
                                                                 f'<b>┠User_id:</b> <code>*****{fake_users}</code>\n'
                                                                 f'<b>┠Идентификатор перевода:</b> <code>{fake_transfer}</code>\n'
                                                                 f'<b>┠Дата:</b> <code>{date}</code>\n'
                                                                 f'<b>┖Сумма:</b> <code>{round(float(amount), 2)}$</code>',
                                  reply_markup=send_okey())

async def send_message_lose_users(message_id):

    await asyncio.sleep(5)
    photo = FSInputFile('photos/Lose.jpg')
    await bot.send_photo(chat_id=channal_id, photo=photo,
                         caption=f'<b>🥵 Поражение!\n\n'
                                 f'<blockquote>Попытай свою удачу снова!\n'
                                 f'Желаю удачи в следующих ставках!</blockquote></b>',
                         reply_to_message_id=message_id, reply_markup=send_stavka())

async def fake_send_message_lose_users(message_id, name, stavka):
    cashback_amount = float(stavka) / 100 * CASHBACK_PROCENT

    await asyncio.sleep(5)
    photo = FSInputFile('photos/Lose.jpg')
    await bot.send_photo(chat_id=channal_id, photo=photo,
                         caption=f'<b>🥵 Поражение!\n\n'
                                 f'<blockquote>Попытай свою удачу снова!\n'
                                 f'Желаю удачи в следующих ставках!</blockquote></b>',
                         reply_to_message_id=message_id, reply_markup=send_stavka())
    if float(stavka) > CASHBACK_LIMIT:
        res = await bot.send_message(chat_id=channal_id,
                               text=f'💸 <b>{name} получите ваш кэшбэк в размере {round(float(cashback_amount), 1)}$ от  вашей ставки {float(stavka)}$ [{CASHBACK_PROCENT}%]</b>',
                               reply_to_message_id=message_id,
                               reply_markup=get_fake_cashback(amount=round(float(cashback_amount), 1), status=0))
        await asyncio.sleep(random.randint(4, 9))
        await bot.edit_message_reply_markup(chat_id=channal_id, message_id=res.message_id, reply_markup=get_fake_cashback(amount=round(float(cashback_amount), 1), status=1))


async def send_message_exeption(e, username, user_id, message_win, amount):
    for i in ADMIN:
        await bot.send_message(chat_id=i,
                               text=f'Произошла ошибка: {e} у пользователя @{username} (<code>{user_id}</code>)')
    await bot.send_message(chat_id=channal_id,
                           text=f'⚠️ <b>Платеж на сумму {amount}$ будет зачислен в ручную, напишите {ADMIN_USERNAME} для выдачи чека</b>',
                           reply_to_message_id=message_win)

async def send_message_exeption_comments(e, username, user_id, message_win, amount):
    for i in ADMIN:
        await bot.send_message(chat_id=i,
                               text=f'Произошла ошибка: {e} у пользователя @{username} (<code>{user_id}</code>) на сумму: {amount}')
    await bot.send_message(chat_id=channal_id,
                           text=f'⚠️ <b>Произошла ошибка [Надо пополнить баланс казино], напишите {ADMIN_USERNAME} для выдачи чека</b>',
                           reply_to_message_id=message_win)






async def referal_send_money(user, amount):
    refere = db.select_referi(user)
    order = ''.join(random.choice(digits) for i in range(10))
    if refere != None and float(amount) >= min_stavka_referal:
        amount_lose_ref = float(amount) / 100 * lose_withdraw
        if float(amount_lose_ref) > 1:
            try:
                await crypto.transfer(user_id=refere, asset='USDT', amount=float(amount_lose_ref), spend_id=order)
                db.add_balances_ref(refere, amount_lose_ref)
                await bot.send_message(chat_id=refere, text=f'<b>💸 Начислено {amount_lose_ref}$ [Реферальная программа]</b>')


            except CodeErrorFactory as e:
                for i in ADMIN:
                    await bot.send_message(chat_id=i, text=f'<code>{refere}</code> не получил кэшбэк {float(amount_lose_ref)}$\n\n'
                                                           f'Ошибка: {e}')

            return
        else:
            chek = await crypto.create_check(asset='USDT', amount=amount, pin_to_user_id=user)
            db.add_balances_ref(refere, amount_lose_ref)
            await bot.send_message(chat_id=refere,
                                   text=f'<b>💸 Начислено {amount_lose_ref}$ [Реферальная программа]</b>')
            try:
                await bot.send_message(chat_id=refere, text=f'<b>🎁 Получен новый чек [Реферальная программа]\n\n'
                                                             f'Активация до 00:00 по МСК\n\n'
                                                            f'Чек: {chek.bot_check_url}</b>')
            except Exception:
                pass


async def go_cashback(amount, user_id, message_id, first_name):
    if float(amount) >= CASHBACK_LIMIT:
        await asyncio.sleep(5)
        return await Cashback_send(user=user_id, stavka=amount, message_id=message_id,
                                   name=first_name)



async def Cashback_send(user, name, message_id, stavka):
    cashback_amount = float(stavka) / 100 * CASHBACK_PROCENT
    if float(cashback_amount) > 1:
        await bot.send_message(chat_id=channal_id, text=f'💸 <b>{name} получите ваш кэшбэк в размере {round(float(cashback_amount), 1)}$ от  вашей ставки {float(stavka)}$ [{CASHBACK_PROCENT}%]</b>', reply_to_message_id=message_id, reply_markup=get_cashback(user, round(float(cashback_amount), 1)))
    else:
        chek = await crypto.create_check(asset='USDT', amount=cashback_amount, pin_to_user_id=user)
        res = await bot.send_message(chat_id=channal_id,
                               text=f'💸 <b>{name} получите ваш кэшбэк в размере {round(float(cashback_amount), 1)}$ от  вашей ставки {float(stavka)}$ [{CASHBACK_PROCENT}%]</b>',
                               reply_to_message_id=message_id, reply_markup=get_cashback_check(url=chek.bot_check_url,
                                                                                               amount=round(float(
                                                                                                   cashback_amount),
                                                                                                            2)))
        try:
            await bot.send_message(chat_id=user, text=f'<b>🎁 Получен новый чек\n\n'
                                                         f'Активация до 00:00 по МСК</b>',
                                   reply_markup=kb_viev_post(url=res.get_url(), amount=cashback_amount))
        except Exception:
            pass



async def transfer_wins(KEF, user_id, message_id, username, amount, rubs_price, order):
    usdt = float(amount) * KEF
    res_win_db = float(usdt) - float(amount)

    rub = float(rubs_price) * float(usdt)
    result_win_amount = round(float(rub), 2)
    await asyncio.sleep(5)



    db.add_count_pay(user_id=user_id, text='win', amount=round(float(res_win_db), 2))
    db.add_count_pay_stats_day(text='win', amount=round(float(res_win_db), 2))

    if float(amount) > 1:
        message_win = await send_message_win_users(usdt=usdt, result_win_amount=result_win_amount,
                                                   message_id=message_id, url='')
        try:
            await crypto.transfer(user_id=user_id, asset='USDT', amount=round(float(usdt), 2), spend_id=order)
            await get_transfer_channal()
        except CodeErrorFactory as e:
            await send_message_exeption(e=e, username=username, user_id=user_id,
                                        message_win=message_win.message_id, amount=round(float(usdt), 2))
    else:
        try:
            chek = await crypto.create_check(asset='USDT', amount=round(float(usdt), 2), pin_to_user_id=user_id)
            message_win = await send_message_win_users(usdt=usdt, result_win_amount=result_win_amount,
                                                       message_id=message_id, status='CHECK', url=chek.bot_check_url)
        except CodeErrorFactory as e:
            return await send_message_exeption(e=e, username=username, user_id=user_id,
                                        message_win=message_id, amount=round(float(usdt), 2))

        try:
            await bot.send_message(chat_id=user_id, text=f'<b>🎁 Получен новый чек\n\n'
                                                         f'Активация до 00:00 по МСК</b>',
                                   reply_markup=kb_viev_post(url=message_win.get_url(), amount=round(float(usdt), 2)))
        except Exception:
            pass


async def draw_message(message_id, amount, order, user_id, username):
    await asyncio.sleep(3.5)
    amount = float(amount) - (float(amount) / 100 * PROCENT_DRAW)
    if float(amount) > 1:
        res_vozvrat = await bot.send_message(chat_id=channal_id, text='<b>🏳️ Ничья!\n\n'
                                                                      f'🕊 Возврат средств на кошелек CryptoBot с комиссией {PROCENT_DRAW}%</b>',
                                             reply_to_message_id=message_id, reply_markup=send_stavka())
        try:
            await crypto.transfer(user_id=user_id, asset='USDT', amount=float(amount), spend_id=order)
        except CodeErrorFactory as e:
            await send_message_exeption(e=e, username=username, user_id=user_id,
                                        message_win=res_vozvrat.message_id, amount=round(float(amount), 2))
    else:
        try:
            chek = await crypto.create_check(asset='USDT', amount=amount, pin_to_user_id=user_id)
            res = await bot.send_message(chat_id=channal_id,
                                         text=f'<b>🏳️ Ничья!\n\n'
                                              f'Активируйте ваш чек для возврата ставки с комиссией {PROCENT_DRAW}%</b>',
                                         reply_markup=kb_send_chek(chek.bot_check_url))
        except CodeErrorFactory as e:
            return await send_message_exeption(e=e, username=username, user_id=user_id,
                                        message_win=message_id, amount=round(float(amount), 2))
        try:
            await bot.send_message(chat_id=user_id, text=f'<b>🎁 Получен новый чек\n\n'
                                                         f'Активация до 00:00 по МСК</b>',
                                   reply_markup=kb_viev_post(url=res.get_url(), amount=amount))
        except Exception:
            pass


async def get_name_game(text:str):
    game_dict = {
        'Больше': '🎲 Больше|Меньше',
        'Меньше': '🎲 Больше|Меньше',
        '1': '🎲 Угадай число',
        '2': '🎲 Угадай число',
        '3': '🎲 Угадай число',
        '4': '🎲 Угадай число',
        '5': '🎲 Угадай число',
        '6': '🎲 Угадай число',
        'Пвп': '🎲 Дуэль',
        'Дуэль': '🎲 Дуэль',
        '2М': '🎲 Двойной куб',
        '2Б': '🎲 Двойной куб',
        '2 Больше': '🎲 Двойной куб',
        '2 Меньше': '🎲 Двойной куб',
        'Равно': '🎲 Близнецы',
        'Ничья': '🎲 Близнецы',
        'Чет': '🎲 Чет | Нечет (куб)',
        'Нечет': '🎲 Чет | Нечет (куб)',
        'Баскетбол Гол': '🏀 Баскетбол',
        'Баскет Гол': '🏀 Баскетбол',
        'Баскетбол Мимо': '🏀 Баскетбол',
        'Баскет Мимо': '🏀 Баскетбол',
        'Футбол Гол': '⚽️ Футбол',
        'Фут Гол': '⚽️ Футбол',
        'Футбол Мимо': '⚽️ Футбол',
        'Фут Мимо': '⚽️ Футбол',
        'Слоты': '🎰 Слоты',
        'Камень': '🪨✂️📄Камень Ножницы Бумага',
        'Ножницы': '🪨✂️📄Камень Ножницы Бумага',
        'Бумага': '🪨✂️📄Камень Ножницы Бумага',
        'Зеленое': '🎡 Колесо',
        'Черное': '🎡 Колесо',
        'Красное': '🎡 Колесо',
    }
    return game_dict.get(text, '❓')


class IsAdmin(BaseFilter):
    async def __call__(self, message:Message):
        if message.from_user.id in ADMIN:
            return True
        return False



async def fake_game_adm():
    values_fake = db.get_fake_values()
    if values_fake:
        urls = db.get_URL()
        help_stavka = hlink('Как сделать ставку', urls.get('info_stavka'))
        info_channal = hlink('Новостной канал', urls.get('news'))
        url_viplata = hlink('Выплаты', urls.get('transfer'))
        url_referal_programm = hlink(f'Реферальная программа [{lose_withdraw}%]', URL_BOT)
        text_game = random.choice(["Больше", "Меньше", "Чет", "Нечет"])
        amount = random.uniform(a=DIAPAZONE_AMOUNT[0], b=DIAPAZONE_AMOUNT[1])
        name = random.choice(FAKE_NICKNAME)
        res = await bot.send_message(chat_id=channal_id, text=f'''
🤵🏻‍♂️ Крупье принял новую ставку.
<blockquote>👤 Игрок: {name}
💸 Ставка: {round(float(amount), 1)}$
☁️ Исход: {text_game}
🕹 Игра: ({await get_name_game(text_game)})</blockquote>
<b>{help_stavka} | {info_channal} | {url_viplata}
[ {url_referal_programm} ]</b>''',
                                     reply_markup=send_stavka(), disable_web_page_preview=True)

        game = await bot.send_dice(chat_id=channal_id, emoji='🎲', reply_to_message_id=res.message_id)
        result_game = game.dice.value

        echange = await crypto.get_exchange_rates()
        rubs_price = echange[0].rate

        if text_game == 'Меньше' and result_game <= 3:
            return await fake_send_message_win_users(amount=round(float(amount), 1), KEF=db.get_cur_KEF('KEF1'),
                                                     message_id=res.message_id, rubs_price=rubs_price)

        if text_game == 'Больше' and result_game >= 4:
            return await fake_send_message_win_users(amount=round(float(amount), 1), KEF=db.get_cur_KEF('KEF1'),
                                                     message_id=res.message_id,
                                                     rubs_price=rubs_price)

        if text_game == "Чет" and result_game % 2 == 0:
            return await fake_send_message_win_users(amount=round(float(amount), 1), KEF=db.get_cur_KEF('KEF5'),
                                                     message_id=res.message_id, rubs_price=rubs_price)

        if text_game == "Нечет" and result_game % 2 != 0:
            return await fake_send_message_win_users(amount=round(float(amount), 1), KEF=db.get_cur_KEF('KEF5'),
                                                     message_id=res.message_id, rubs_price=rubs_price)

        else:
            return await fake_send_message_lose_users(message_id=res.message_id, name=name, stavka=round(float(amount), 1))



async def kef_all_text(all_kef):
    text = f'''📊 Текущие коэффициенты:
    
<b>┠1)Больше/Меньше кости: <code>{all_kef["KEF1"]}</code>x
┠2)Кубик угадай число: <code>{all_kef["KEF2"]}</code>x
┠3)ПВП Дуэль кубик: <code>{all_kef["KEF3"]}</code>x
┠4)Два Больше/Меньше кубик: <code>{all_kef["KEF4"]}</code>x
┠5)Чет/Нечет Кубик: <code>{all_kef["KEF5"]}</code>x
┠6)Слоты 3 лимона: <code>{all_kef["KEF6"]}</code>x
┠7)Слоты BAR: <code>{all_kef["KEF7"]}</code>x
┠8)Слоты 3 ягоды: <code>{all_kef["KEF8"]}</code>x
┠9)Слоты 777: <code>{all_kef["KEF9"]}</code>x
┠10)Баскетбол Гол: <code>{all_kef["KEF10"]}</code>x
┠11)Баскетбол мимо: <code>{all_kef["KEF11"]}</code>x
┠12)Футбол гол: <code>{all_kef["KEF12"]}</code>x
┠13)Футбол мимо: <code>{all_kef["KEF13"]}</code>x
┠14)Ничья пвп: <code>{all_kef["KEF14"]}</code>x
┠15)Камень, ножницы, бумага: <code>{all_kef["KEF15"]}</code>x
┠16)Колесо красное/черное: <code>{all_kef["KEF16"]}</code>x
┖17)Колесо зеленое: <code>{all_kef["KEF17"]}</code>x

⚙️ Для изменения коэффициента выберите соответствующую кнопку ниже</b>'''
    return text


async def procent_knb_twist(values):
    data = {1:10, 10:20, 20:30, 30:40, 40:50, 50:60, 60:70, 70:80, 80:90, 90:100, 100:1}
    return data.get(values)


async def urls_admin_text(url):
    text = f"""<b>📎Канал: {url.get('channals')}
📎Счет для оплаты: {url.get('checks')}
📎Правила: {url.get('rules')}
📎Выплаты: {url.get('transfer')}
📎Ключевые слова: {url.get('command_game')}
📎Как сделать ставку: {url.get('info_stavka')}
📎Новости: {url.get('news')}

Для изменения ссылки выберите соответствующую кнопку</b>"""
    return text


async def not_game_func(amount:float, user_id, status:str, first_name, order, username):
    kommision = float(amount) * PROCENT_NOT_GAME / 100
    amount = float(amount) - kommision

    if float(amount) < 1 and status == 'Comments':
        chek = await crypto.create_check(asset='USDT', amount=amount, pin_to_user_id=user_id)
        res = await bot.send_message(chat_id=channal_id, text=f'<b>⚠️ {first_name} Вы не указали комментарий к платежу!\n\n'
                                                        f'Активируйте ваш чек для возврата ставки с комиссией {PROCENT_NOT_GAME}%</b>', reply_markup=kb_send_chek(chek.bot_check_url))
        try:
            await bot.send_message(chat_id=user_id, text=f'<b>🎁 Получен новый чек\n\n'
                                                         f'Активация до 00:00 по МСК</b>', reply_markup=kb_viev_post(url=res.get_url(), amount=amount))
        except Exception:
            pass

    if float(amount) >= 1 and status == 'Comments':
        res = await bot.send_message(chat_id=channal_id,
                                     text=f'<b>⚠️ {first_name} Вы не указали комментарий к платежу!\n\n'
                                          f'Средства автоматически возвращены в ваш кошелек CryptoBot с комиссией {PROCENT_NOT_GAME}%</b>',
                                     reply_markup=send_stavka())
        try:
            return await crypto.transfer(user_id=user_id, asset='USDT', amount=float(amount), spend_id=order)
        except CodeErrorFactory as e:
            return await send_message_exeption_comments(e=e, username=username, user_id=user_id,
                                                        message_win=res.message_id, amount=amount)


    if status == 'LIMIT':
        res = await bot.send_message(chat_id=channal_id,
                                     text=f'<b>⚠️ {first_name} Вы превысили максимальный лимит ставки в\n\n'
                                          f'Средства автоматически возвращены в ваш кошелек CryptoBot с комиссией {PROCENT_NOT_GAME}%</b>',
                                     reply_markup=send_stavka())
        try:
            return await crypto.transfer(user_id=user_id, asset='USDT', amount=float(amount), spend_id=order)
        except CodeErrorFactory as e:
            return await send_message_exeption_comments(e=e, username=username, user_id=user_id,
                                                        message_win=res.message_id, amount=amount)



    if float(amount) < 1 and status == 'Command':
        chek = await crypto.create_check(asset='USDT', amount=amount, pin_to_user_id=user_id)
        res = await bot.send_message(chat_id=channal_id, text='❌ <b>Команда не распознана!\n'
                                          'Убедитесь что вы верно вводите ключевое слово\n\n'
                                          f'Средства автоматически возвращены в ваш кошелек CryptoBot с комиссией {PROCENT_NOT_GAME}%</b>', reply_markup=kb_send_chek(chek.bot_check_url))
        try:
            await bot.send_message(chat_id=user_id, text=f'<b>🎁 Получен новый чек\n\n'
                                                         f'Активация до 00:00 по МСК</b>', reply_markup=kb_viev_post(url=res.get_url(), amount=amount))
        except Exception:
            pass

    if float(amount) >= 1 and status == 'Command':
        res = await bot.send_message(chat_id=channal_id,
                                     text='❌ <b>Команда не распознана!\n'
                                          'Убедитесь что вы верно вводите ключевое слово\n\n'
                                          f'Средства автоматически возвращены в ваш кошелек CryptoBot с комиссией {PROCENT_NOT_GAME}%</b>',
                                     reply_markup=send_stavka())
        try:
            return await crypto.transfer(user_id=user_id, asset='USDT', amount=float(amount), spend_id=order)
        except CodeErrorFactory as e:
            return await send_message_exeption_comments(e=e, username=username, user_id=user_id,
                                                        message_win=res.message_id, amount=amount)









