import requests
from bs4 import BeautifulSoup
import pandas as pd

headers = {'User-Agent': 'Chrome'}


# def estrai_gol_casa(squadra, risultato):
#     if squadra == 'casa':
#         if ":" in risultato or risultato == "LIVE":
#             return "-"
#         return risultato.split(" - ")[0]
#     if squadra == 'ospite':
#         if ":" in risultato or risultato == "LIVE":
#             return "-"
#         return risultato.split(" - ")[1]
#     raise ValueError("assegnare 'casa' o 'ospite' al parametro 'squadra'")


def ottieni_giornate_soup(anno_inizio):
    http_stagione_attuale = "https://sport.sky.it/calcio/serie-a/calendario-risultati"
    re_stagione_attuale = requests.get(http_stagione_attuale)
    soup_stagione_attuale = BeautifulSoup(re_stagione_attuale.text, "html.parser")
    data_stagione_corrente_soup = soup_stagione_attuale.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14--16 ftbl__match-data-row__date-long"})
    anno_inizio_stagione_corrente = int(data_stagione_corrente_soup.text.split(" ")[-1][-2:])
    anno = f"20{anno_inizio}/" if anno_inizio < anno_inizio_stagione_corrente else ""
    http = f"https://sport.sky.it/calcio/serie-a/{anno}calendario-risultati"
    re = requests.get(http)
    soup = BeautifulSoup(re.text, "html.parser")
    giornate_soup = soup.find_all("div", attrs={"data-intersect": "true"})
    return giornate_soup


def costruisci_excel(anno_inizio):
    url_serie_a = f"https://www.transfermarkt.it/serie-a/gesamtspielplan/wettbewerb/IT1/saison_id/20{anno_inizio}"
    serie_a_res = requests.get(url_serie_a, headers=headers)
    serie_a_soup = BeautifulSoup(serie_a_res.content, 'html.parser')
    giornate_soup = serie_a_soup.findAll("div", "large-6 columns")
    giornate_soup.append(serie_a_soup.find("div", "large-6 columns end"))
    dataframe = pd.DataFrame([], columns=["Giornata", "Data", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    for giornata_soup in giornate_soup:
        giornata = giornata_soup.find("div", "content-box-headline").text
        n_giornata = giornata.split(".")[0]
        soupDate = [el for el in giornata_soup.findAll("td", "hide-for-small") if
                    el not in giornata_soup.findAll("td", "zentriert hide-for-small")]
        date = []
        ultimaData = "01/01/01"
        for soupData in soupDate:
            data = ultimaData if soupData.find("a") is None else soupData.find("a").text
            ultimaData = data
            giorno, mese, anno = data.split("/")
            dataCorretta = f"20{anno}-{mese}-{giorno}"
            date.append(dataCorretta)
        casa_soup = giornata_soup.findAll("td", "text-right no-border-rechts hauptlink")
        ospiti_soup = giornata_soup.findAll("td", "no-border-links hauptlink")
        squadre_casa = [el.find("a").text for el in casa_soup]
        squadre_ospiti = [el.find("a").text for el in ospiti_soup]
        risultati_soup = giornata_soup.findAll("a", "ergebnis-link")
        risultati = [el.text for el in risultati_soup]
        gol_squadre_casa = [r.split(":")[0] for r in risultati]
        gol_squadre_ospite = [r.split(":")[1] for r in risultati]
        array = [[n_giornata, d, c, o, g_c, g_o] for d, c, o, g_c, g_o in
                 list(zip(date, squadre_casa, squadre_ospiti, gol_squadre_casa, gol_squadre_ospite)) if g_c != '-']
        df = pd.DataFrame(array, columns=["Giornata", "Data", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        dataframe = pd.concat([dataframe, df])
    dataframe["Stagione"] = f"{anno_inizio}{anno_inizio + 1}"
    path = f"season/season-{anno_inizio}{anno_inizio + 1}_csv"
    dataframe.to_excel(f"{path}.xlsx", index=False)
    return f"{path}.xlsx"


def leggi(anno_inizio, create=True):
    path = f"season/season-{anno_inizio}{anno_inizio + 1}_csv"
    if not create:
        try:
            return pd.read_excel(f"{path}.xlsx")
        except FileNotFoundError:
            print(f"{path}.xlsx not exists\ncreating it")
    return pd.read_excel(costruisci_excel(anno_inizio))
