import pandas as pd

from storicovoti.consigli_di_giornata import consigli_di_giornata


# def estraiEsito(punteggioCasa, punteggioOspiti):
#     delta = punteggioCasa - punteggioOspiti
#     if delta >= 4 and punteggioCasa > 66:
#         return "1"
#     if delta <= -4 and punteggioOspiti > 66:
#         return "2"
#     return "x"


def estraiEsito(punteggioCasa, punteggioOspiti):
    delta = punteggioCasa - punteggioOspiti
    if delta > 30:
        return "1"
    if delta < -30:
        return "2"
    return "x"


if __name__ == "__main__":
    range_giornate = 5
    stagione = 22
    titolari = pd.read_csv(f"titolari_{stagione}{stagione + 1}.csv")
    season = pd.read_excel(f"season\\season-{stagione}{stagione + 1}_csv.xlsx")
    array = []
    for giornata in range(6, 39):
        try:
            consigliDiGiornata = pd.read_excel(
                f"estrazioni/consigli_giornata/giornata_{giornata}/consigli_ultime_{range_giornate}.xlsx")
        except FileNotFoundError:
            consigliDiGiornata = consigli_di_giornata(giornata - 1, range_giornate, stagione, True)
        titolari = titolari.loc[titolari.giornata == giornata]
        merge = pd.merge(titolari, consigliDiGiornata, how="left", left_on="titolare", right_on="Nome")
        merge = merge[["giornata", "squadra", "titolare", "R", "Nome", "VotoPotenziale", "FantaVotoPotenziale"]]
        partite = season.loc[season.Giornata == giornata][["HomeTeam", "AwayTeam"]].values.tolist()
        for casa, ospite in partite:
            voti_titolari_casa = merge.loc[merge.squadra == casa].FantaVotoPotenziale.sum()
            voti_titolari_ospite = merge.loc[merge.squadra == ospite].FantaVotoPotenziale.sum()
            giocatori_titolari_casa_nan = merge.loc[merge.squadra == casa].FantaVotoPotenziale.count()
            giocatori_titolari_ospite_nan = merge.loc[merge.squadra == ospite].FantaVotoPotenziale.count()
            somma_voti_titolari_casa = voti_titolari_casa + 6 * (11 - giocatori_titolari_casa_nan)
            somma_voti_titolari_ospite = voti_titolari_ospite + 6 * (11 - giocatori_titolari_ospite_nan)
            array.append(
                [giornata, casa, ospite, estraiEsito(somma_voti_titolari_casa, somma_voti_titolari_ospite)])
    pd.DataFrame(array, columns=["giornata", "casa", "ospite", "esito"]).to_csv(
        f"previsione_esiti_{stagione}{stagione + 1}.csv", index=False)
