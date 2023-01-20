import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


def estrai_gol_casa(squadra, risultato):
    if squadra == 'casa':
        if ":" in risultato:
            return "-"
        return risultato.split(" - ")[0]
    if squadra == 'ospite':
        if ":" in risultato:
            return "-"
        return risultato.split(" - ")[1]
    raise ValueError("assegnare 'casa' o 'ospite' al parametro 'squadra'")


def ottieni_giornate_soup(anno_inizio):
    http_stagione_attuale = "https://sport.sky.it/calcio/serie-a/calendario-risultati"
    re_stagione_attuale = requests.get(http_stagione_attuale)
    soup_stagione_attuale = BeautifulSoup(re_stagione_attuale.text, "html.parser")
    data_stagione_corrente_soup = soup_stagione_attuale.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-16 ftbl__match-data-row__date-long"})
    anno_inizio_stagione_corrente = int(data_stagione_corrente_soup.text.split(" ")[-1][-2:])
    anno = f"20{anno_inizio}/" if anno_inizio < anno_inizio_stagione_corrente else ""
    http = f"https://sport.sky.it/calcio/serie-a/{anno}calendario-risultati"
    re = requests.get(http)
    soup = BeautifulSoup(re.text, "html.parser")
    giornate_soup = soup.find_all("div", attrs={"data-intersect": "true"})
    return giornate_soup


def costruisci_excel(anno_inizio):
    giornate_soup = ottieni_giornate_soup(anno_inizio)
    dataframe = pd.DataFrame([], columns=["Giornata", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    for giornata_soup in giornate_soup:
        giornata = giornata_soup.find("h2", attrs={
            "class": "ftbl__text ftbl__text--h2 ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__results-title__heading"}).text
        n_giornata = giornata.lower().split("giornata ")[1]
        squadre_soup = giornata_soup.find_all("span", attrs={"class": "ftbl__match-row__team--desktop"})
        casa_soup_coi_none = [el.find("span", attrs={
            "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--right"})
                              for el in squadre_soup]
        ospiti_soup_coi_none = [el.find("span", attrs={
            "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--left"})
                                for el in squadre_soup]
        squadre_casa = [el.text for el in casa_soup_coi_none if el is not None]
        squadre_ospiti = [el.text for el in ospiti_soup_coi_none if el is not None]
        risultati_soup = giornata_soup.find_all("td", attrs={"class": "ftbl__match-row__result"})
        risultati = [el.text for el in risultati_soup]
        gol_squadre_casa = [estrai_gol_casa("casa", r) for r in risultati]
        gol_squadre_ospite = [estrai_gol_casa("ospite", r) for r in risultati]
        array = [[n_giornata, c, o, g_c, g_o] for c, o, g_c, g_o in
                 list(zip(squadre_casa, squadre_ospiti, gol_squadre_casa, gol_squadre_ospite)) if g_c != '-']
        df = pd.DataFrame(array, columns=["Giornata", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])
        dataframe = pd.concat([dataframe, df])
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
