import requests
from bs4 import BeautifulSoup
import csv
import json
import tkinter as tk
from tkinter import filedialog


with open('account.json', 'r') as f:
    account = json.load(f)

email = account["email"]
password = account["password"]

data = []

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://restocks.net",
    "pragma": "no-cache",
    "referer": "https://restocks.net/de/login",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}
def flow():
    # --- login
    s = requests.session()
    print("Generating Session...")
    r = s.get("https://restocks.net/de/login", headers = headers)
    sp = BeautifulSoup(r.text, 'html.parser')
    token = sp.find('meta', {'name': 'csrf-token'})['content']
    payload = {'_token': token,
            'email': email,
            'password': password
            }
    print("Submitting login...")
    r = s.post("https://restocks.net/de/login", data = payload, headers = headers)
    r = s.get("https://restocks.net/de/account")
    sp = BeautifulSoup(r.text, 'html.parser')
    name_tag = sp.find('h1')
    name = name_tag.text.split()[-1]
    if name.lower() == "einloggen":
        print("Login failed, check data.")
        return

    else:
        print("Successfully logged in as " + name + "!")
    # --- get listings
    n = 0
    i = 1
    while n == 0:
        r = s.get("https://restocks.net/de/account/sales/history?page="+str(i), headers = headers)
        if("no__listings__notice" in r.text):
            n = 1
            print("stopped at page " + str(i) + ". No more sales found.")
        else:
            soup = BeautifulSoup(json.loads(r.text)["products"], 'html.parser')
            rows = ""
            if i == 1 :
                table = soup.find('table', class_='listings')
                rows = table.find('tbody').find_all('tr')
            else:
                rows = soup.find_all('tr')[1:]

            for row in rows:
                image = row.find('img')['src']
                name = row.find('span').text
                size = row.find_all('br')[0].next_sibling.strip()
                id = row.find_all('br')[1].next_sibling.strip().replace("ID: ", "")
                price = row.find_all('span')[-1].text.strip()
                date = row.find_all('td')[-1].text.strip()
                data.append({'image': image, 'name': name, 'size': size, 'id': id, 'price': price, 'date': date})
            i = i + 1
    print("Found " + str(len(data)) + " sales!")
    print("Please select the path of your Bank-CSV-File")
    #---get csv path
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    #---read csv
    rawcsv = ""
    with open(file_path, 'r') as csv_file:
        csv_text = csv_file.read()
        rawcsv = csv_text
    #check if paid
    unpaid = 0
    paid = 0
    listpaid = []
    for d in data:
        if d["id"] in rawcsv:
            print(d["id"] + " - " + d["name"] + " - " +  d["price"] + " - PAID")
            paid += int(d["price"].replace("€ ",""))
            listpaid.append("true")
        else:
            unpaid += int(d["price"].replace("€ ",""))
            print(d["id"] + " - " + d["name"] + " - " +  d["price"] + " - UNPAID")
            listpaid.append("false")
    #save to csv
    with open('items.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ['image', 'name', 'size', 'id', 'price', 'date','paid']
        writer.writerow(header)
        c = 0
        for item in data:
            row = [item['image'], item['name'], item['size'], item['id'], item['price'], item['date'], listpaid[c]]
            c = c + 1
            writer.writerow(row)

    print("PAID: " + str(paid) + " | UNPAID: " + str(unpaid))
    input()
flow()
input()