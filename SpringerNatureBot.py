import logging
import requests
from telegram import ParseMode
from telegram.ext import Updater
from datetime import date, timedelta, datetime

from config import (
    SPRINGER_API_KEY,
    BOT_API_KEY,
    USER_CHAT_ID
)

from Vars import (
    JID,
    SPRINGER_URL,
    JCHANNEL,
    HEADERS
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_current_articles(context, current_date, journal_id, journal_name) -> dict:
    """
    Action: Send API request for Meta data to Springer Nature API Portal
    :param context: special python-telegram-bot object
    :param current_date: datetime object with current date
    :param journal_id: journal id from Springer Nature database (from JID dict)
    :param journal_name: journal name from JID dict
    :return: json with list of articles from specified journal for specified time
    """
    try:
        only_for_reviews = '' if journal_name in ['NatureGenetics',
                                                  'NatureMachineIntelligence'] else '"Review Article" OR "Perspective"'
        response = requests.get(SPRINGER_URL,
                                params={'q': only_for_reviews +
                                             f'onlinedate:{current_date} ' +
                                             f'journalid:{journal_id}',
                                        'api_key': SPRINGER_API_KEY},
                                headers=HEADERS)
        return response.json()['records']
    except requests.exceptions.Timeout:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Timeout!")
    except requests.exceptions.TooManyRedirects:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Too Many Redirects!")
    except requests.exceptions.RequestException:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Parental Request Exception!")


def make_message(article: dict, hashtags: str) -> str:
    """
    Action: make Telegram message from API response
    :param article: dictionary from API response with individual article data
    :param hashtags: list of hashtags, inserted at the end of the channel message
    :return: string with assembled individual article info (title, abstract, hashtags, web link)
    """
    title = article['title']
    abstract = article['abstract']
    link_web = article['url'][0]['value']
    return f'\n*{title}*\n\n{abstract}\n\n{hashtags}\n\n*Link:*\n{link_web}'


def send_messages_job(context) -> None:
    """
    Action: send messages to specified channels (see JID) every N seconds (e.g. 3600; 1 hour)
    :param context: special python-telegram-bot object
    :return: None
    """

    current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    desired_date = (datetime.today() - timedelta(days=2))
    for journal_name, journal_id in JID.items():
        chat_id = JCHANNEL[journal_name]
        hashtags = f'#{journal_name} ' + desired_date.strftime('#Nature%B%Y')
        response = get_current_articles(context,
                                        current_date=desired_date.strftime('%Y-%m-%d'),
                                        # date.today().strftime('%Y-%m-%d'),
                                        journal_id=journal_id,
                                        journal_name=journal_name)
        if response:
            for article in response:
                context.bot.send_message(chat_id=chat_id,
                                         text=make_message(article, hashtags),
                                         parse_mode=ParseMode.MARKDOWN)
                context.bot.send_message(chat_id=USER_CHAT_ID,
                                         text=f"Non-Empty Response for {journal_name}: {current_time}!")


def main() -> None:
    """
    Action: Run bot.
    :return: None
    """
    updater = Updater(token=BOT_API_KEY, use_context=True)
    job = updater.job_queue

    # Start the Bot
    job.run_repeating(send_messages_job, interval=timedelta(days=1), first=3)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
