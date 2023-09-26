import pandas as pd
import requests
from bs4 import BeautifulSoup


def estraiTitolariPerStagione(stagione):
    headers = {'User-Agent': 'Chrome'}
    df = pd.read_excel(f"season\\season-{stagione}{stagione + 1}_csv.xlsx")
    partiteDf = df[["Giornata", "HomeTeam", "AwayTeam"]]
    linkBase = [f"https://www.fantacalcio.it/serie-a/calendario/{giornata}/20{stagione}-{stagione + 1}".lower() for
                giornata in range(1, 39)]

    soupLinkBase = [BeautifulSoup(requests.get(lb, headers=headers).content, 'html.parser') for lb in linkBase]
    linkPartitePerGiornata = [[f"{lb}/{'-'.join(el['value'].split('/')[:2])}/{el['value'].split('/')[-1]}" for el in
                               slb.find("select", {"id": "matchControl"}).findAll("option")] for lb, slb in
                              zip(linkBase, soupLinkBase)]
    array = []
    for numero, lppg in enumerate(linkPartitePerGiornata):
        for linkPartita in lppg:
            request = requests.get(linkPartita, headers=headers)
            soup = BeautifulSoup(request.content, 'html.parser')
            titolari = [el.text.strip() for el in soup.find("section", {"class": "mt-4", "id": "pitch"}).findAll("a", {
                "class": "player-name player-link"})[:22]]
            squadra_casa, squadra_ospite = linkPartita.split("/")[-2].split("-")
            [array.append([numero + 1, squadra_casa, giocatore.upper()]) for giocatore in titolari[:11]]
            [array.append([numero + 1, squadra_ospite, giocatore.upper()]) for giocatore in titolari[11:]]

    df = pd.DataFrame(array, columns=["giornata", "squadra", "titolare"])
    df.to_csv(f"titolari_{stagione}{stagione + 1}.csv", index=False)


if __name__ == '__main__':
    stagione = 22
    estraiTitolariPerStagione(stagione)
