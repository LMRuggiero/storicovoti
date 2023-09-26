import pandas as pd


def estraiEsitiReali(golCasa, golOspiti):
    if golCasa > golOspiti:
        return "1"
    if golCasa < golOspiti:
        return "2"
    return "x"


if __name__ == "__main__":
    stagione = 22
    previsione_esiti = pd.read_csv(f"previsione_esiti_{stagione}{stagione + 1}.csv")
    season = pd.read_excel(f"season\\season-{stagione}{stagione + 1}_csv.xlsx")
    season["esito"] = season[["FTHG", "FTAG"]].apply(lambda x: estraiEsitiReali(x.FTHG, x.FTAG), axis=1)
    merge = pd.merge(previsione_esiti, season, how='inner', left_on=["giornata", "casa", "ospite", "esito"],
                     right_on=["Giornata", "HomeTeam", "AwayTeam", "esito"])
    print(len(merge))
