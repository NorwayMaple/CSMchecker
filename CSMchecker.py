from urllib.request import urlopen
from bs4 import BeautifulSoup
import datetime
import sendgrid
import os
from sendgrid.helpers.mail import *
import pytz
from pytz import timezone

minutesRange = 62
articleSearchesPresent = []
def getArticleTime(article):
    articleTimestamp = article.find("time").attrs['data_timestamp']
    return pytz.utc.localize(datetime.datetime.utcfromtimestamp(int(articleTimestamp)))
def getArticles(searchText):
    searchURL = "http://www.csmonitor.com/content/search?SearchText=" + searchText.lower() + "&sort="
    html = urlopen(searchURL)
    bsObj = BeautifulSoup(html, 'html.parser')
    articleList = bsObj.find("div", {"id":"content-listing"}).findAll("div", {"class":"story_list_item ezv-listing"})
    recentArticles = []
    articleFound = False
    articleText = ""
    for article in articleList:
        UTCarticleTime = getArticleTime(article)
        if datetime.datetime.now(timezone("UTC")) - UTCarticleTime < (datetime.timedelta(minutes=minutesRange)):
            articleFound = True
            recentArticles.append(article)
    if articleFound:
        articleSearchesPresent.append(searchText)
        articleText += "Articles about " + searchText + ":\n\n"
    for article in recentArticles:
        articleTitle = article.find("span", {"class":"story_link"}).get_text()
        UTCarticleTime = getArticleTime(article)
        ETarticleTime = UTCarticleTime.astimezone(timezone("US/Eastern"))
        articleTimeStr = ETarticleTime.strftime("%A, %B %d, %Y %-H:%M")
        articleShortURL = article.find("h3", {"class":"story_headline"}).find("a").attrs["href"]
        articleURL = "http://www.csmonitor.com" + articleShortURL
        articleText += "\n".join([articleTitle.strip(), articleTimeStr, articleURL, "\n"])
    return articleText
    
emailContent = "To whom it may concern,\n\n"
emailContent += "The following is an automated email that checks the Christian Science "
emailContent += "Monitor every hour for new articles that have the keyword \"Taiwan"
emailContent += "\" and \"China\".  It was created by Abe Polk in order to eliminate the need "
emailContent += "to check the website regularly by hand.\n\n"
emailContent += getArticles("Taiwan")
emailContent += getArticles("China")
emailContent += "Note: Please do not reply to this email.  You can contact me at abepolk@gmail.com\n\n"
emailContent += "Best,\n\nAbe Polk"
  
recipients = []
shouldSendEmail = False
ccFlag = False
if ("China" in articleSearchesPresent or "China" in articleSearchesPresent):
    recipients.append(os.environ.get('EMAIL_1'))
    recipients.append(os.environ.get('EMAIL_2'))
    shouldSendEmail = True
if "Taiwan" in articleSearchesPresent:
    ccFlag = True
    recipients.append(os.environ.get('EMAIL_3'))

if shouldSendEmail:
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("AbePolkDoNotReply@example.com")
    subject = "Automated new article notification"
    to_email = Email(recipients[0])
    to_email2 = Email(recipients[1])
    content = Content("text/plain", emailContent)
    mail = Mail(from_email, subject, to_email, content)
    mail.personalizations[0].add_to(to_email2)
    ## cc can not be put in the Mail constructor, so it has to be
    ## added to the personalization object within the Mail class
    if ccFlag:
        cc_email = Email(recipients[2])
        mail.personalizations[0].add_cc(cc_email)
    try:
        response = sg.client.mail.send.post(request_body=mail.get())
        print("Email sent")
    except Exception as e:
        print(e.read())
else:
    print("No email sent")
