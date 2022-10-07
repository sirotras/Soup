from bs4 import BeautifulSoup
update_url = 'https://ccsportscarclub.org/autocross/schedule/'

soup = BeautifulSoup(update_url, 'html.parser')

print(soup.prettify())