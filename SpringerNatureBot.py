import logging
import requests
from telegram import ParseMode
from telegram.ext import Updater
from datetime import date, datetime

from config import (
    SPRINGER_API_KEY,
    BOT_API_KEY,    
    USER_CHAT_ID
)

from Vars import (,
    JID,
    SPRINGER_URL
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_current_articles(context, current_date, journal_id, journal_name) -> dict:
    """TODO: description"""
    try:
        only_for_reviews = '' if journal_name in ['NatureGenetics'] else '"Review Article"'
        response = requests.get(SPRINGER_URL, params={'q': only_for_reviews +
                                                           f'onlinedate:{current_date} ' +
                                                           f'journalid:{journal_id}',
                                                      'api_key': SPRINGER_API_KEY})
        return response.json()['records']
    except requests.exceptions.Timeout:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Timeout!")
    except requests.exceptions.TooManyRedirects:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Too Many Redirects!")
    except requests.exceptions.RequestException:
        context.bot.send_message(chat_id=USER_CHAT_ID, text="Request error: Parental Request Exception!")


def make_message(article: dict, hashtags: str) -> str:
    """TODO: description"""
    title = article['title']
    abstract = article['abstract']
    link_web = article['url'][0]['value']
    return f'\n*{title}*\n\n{abstract}\n\n{hashtags}\n\n*Link:*\n{link_web}'


def send_messages_job(context) -> None:
    """TODO: description"""
    current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    for journal_name, journal_id in JID.items():
        hashtags = f'#{journal_name} ' + date.today().strftime('#Nature%B%Y')
        response = get_current_articles(context,
                                        current_date="2021-06-10",  # date.today().strftime('%Y-%m-%d'),  # "2021-04-12"
                                        journal_id=journal_id,
                                        journal_name=journal_name)
        if response:
            for article in response:
                chat_id = f'@{journal_name}' if journal_name in ['NatureGenetics'] else f'@NatureReviewsJournal'
                context.bot.send_message(chat_id=chat_id,
                                         text=make_message(article, hashtags),
                                         parse_mode=ParseMode.MARKDOWN)
            context.bot.send_message(chat_id=USER_CHAT_ID,
                                     text=f"Non-Empty Response for {journal_name}: {current_time}!")


def main() -> None:
    """Run bot."""
    updater = Updater(token=BOT_API_KEY, use_context=True)
    job = updater.job_queue

    daily_articles = list()  # TODO: clear article set at 00:00

    # Start the Bot
    job.run_repeating(send_messages_job, interval=3600, first=3)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
