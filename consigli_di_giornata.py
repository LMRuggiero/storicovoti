from SeasonDf import *
from modello_fantacalcio import *


def maiuscolo(el):
    return el.upper()


def estrai_sfidante(
        df,
        squadra
):
    if df.HomeTeam.apply(maiuscolo).values[0] == squadra:
        return df.AwayTeam.apply(maiuscolo).values[0]
    return df.HomeTeam.apply(maiuscolo).values[0]


def estrai_voti(
        df,
        squadra
):
    df_all = df.loc[df["Ruolo"] == "ALL"]
    index_start = df.loc[df["Cod."] == squadra].index[0]
    index_end = list(filter(lambda x: x > index_start + 1, df_all.index.tolist()))[0]
    return df.iloc[index_start + 2:index_end].loc[df.Voto.apply(voto_valido) == True]


def voto_valido(x):
    if isinstance(x, str):
        return False
    return True


def ottieni_fantavoto(row):
    return 3 * (row[1] + row[3] - row[4] + row[5]) - 2 * row[6] + row[0] - row[2] - row[8] + row[9] - 0.5 * row[7]


def inserisci(
        diz,
        col_media,
        squadra,
        media_voto
):
    try:
        diz[col_media][squadra] += media_voto
    except KeyError:
        diz[col_media][squadra] = media_voto


def voto_con_modificatore(lista_v_fv):
    a = 2
    b = -21
    c = 55
    return [(a * v ** 2 + b * v + c) / 4 + fv for v, fv in lista_v_fv]


def voto_potenziale(
        voto,
        fanta_voto,
        ruolo
):
    if ruolo in ["D", "P"]:
        return (2 * voto ** 2 - 21 * voto + 55) / 4 + fanta_voto
    return fanta_voto


def consigli_di_giornata(
        ultima_giornata,
        n_giornate,
        salva_consigli=False,
        salva_modello=False,
        create_season_df=True,
        perc_presenze=0.375,
        file_quotazioni="Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    lista_excel, risultato_finale = modello_fantacalcio(
        ultima_giornata,
        n_giornate,
        salva_modello,
        perc_presenze,
        file_quotazioni
    )
    sub_excels = lista_excel[-n_giornate:]
    stagioni = list(
        set([int([x[-2:] for x in ex.split("_") if "20" in x and "xlsx" not in x][0]) for ex in sub_excels]))

    diz = {x: {} for x in
           ["Voti_P", "Voti_D", "Voti_C", "Voti_A", "FantaVoti_P", "FantaVoti_D", "FantaVoti_C", "FantaVoti_A"]}

    for stagione in stagioni:
        df_season = leggi(stagione, create=create_season_df)
        for ex in sub_excels:
            giornata = int(ex.split(".")[0].split("_")[-1])
            s = int([x[-2:] for x in ex.split("_") if "20" in x and "xlsx" not in x][0])
            if s == stagione:
                df_voti = pd.read_excel(ex, usecols="A:M",
                                        names=["Cod.", "Ruolo", "Nome", "Voto", "Gf", "Gs", "Rp", "Rs", "Rf", "Au",
                                               "Amm", "Esp", "Ass"])
                df_voti["Cod."] = df_voti["Cod."].str.upper()
                df_voti["Nome"] = df_voti["Nome"].str.upper()
                for line in df_voti.values:
                    el = line[0]
                    if isinstance(el, str) and el != "COD." and len(el.split(" ")) == 1:
                        squadra = el.upper()
                        df_partita = df_season.loc[
                            (df_season.Giornata == giornata) & ((df_season.HomeTeam.apply(maiuscolo) == squadra) | (
                                    df_season.AwayTeam.apply(maiuscolo) == squadra))]
                        squadra_sfidante = estrai_sfidante(df_partita, squadra)
                        df_voti_sfidante = estrai_voti(df_voti, squadra_sfidante)
                        df_voti_sfidante["FantaVoto"] = [ottieni_fantavoto(row) for row in df_voti_sfidante[
                            ["Voto", "Gf", "Gs", "Rp", "Rs", "Rf", "Au", "Amm", "Esp", "Ass"]].values]
                        media_sfidante_p = df_voti_sfidante.loc[df_voti_sfidante.Ruolo == "P"].Voto.tolist()
                        media_sfidante_d = df_voti_sfidante.loc[df_voti_sfidante.Ruolo == "D"].Voto.tolist()
                        media_sfidante_c = df_voti_sfidante.loc[df_voti_sfidante.Ruolo == "C"].Voto.tolist()
                        media_sfidante_a = df_voti_sfidante.loc[df_voti_sfidante.Ruolo == "A"].Voto.tolist()
                        inserisci(diz, "Voti_P", squadra, media_sfidante_p)
                        inserisci(diz, "Voti_D", squadra, media_sfidante_d)
                        inserisci(diz, "Voti_C", squadra, media_sfidante_c)
                        inserisci(diz, "Voti_A", squadra, media_sfidante_a)
                        fantamedia_sfidante_p = df_voti_sfidante.loc[
                            df_voti_sfidante.Ruolo == "P"].FantaVoto.tolist()
                        fantamedia_sfidante_d = df_voti_sfidante.loc[
                            df_voti_sfidante.Ruolo == "D"].FantaVoto.tolist()
                        fantamedia_sfidante_c = df_voti_sfidante.loc[
                            df_voti_sfidante.Ruolo == "C"].FantaVoto.tolist()
                        fantamedia_sfidante_a = df_voti_sfidante.loc[
                            df_voti_sfidante.Ruolo == "A"].FantaVoto.tolist()
                        inserisci(diz, "FantaVoti_P", squadra, fantamedia_sfidante_p)
                        inserisci(diz, "FantaVoti_D", squadra, fantamedia_sfidante_d)
                        inserisci(diz, "FantaVoti_C", squadra, fantamedia_sfidante_c)
                        inserisci(diz, "FantaVoti_A", squadra, fantamedia_sfidante_a)

    a = pd.DataFrame.from_dict(diz)

    voti_contro = pd.DataFrame([])
    for c in a.columns:
        new_c = f"Media{c}"
        voti_contro[new_c] = a[c].apply(media)
    voti_contro["MediaConMod_P"] = voto_con_modificatore(
        list(zip(voti_contro.MediaVoti_P, voti_contro.MediaFantaVoti_P)))
    voti_contro["MediaConMod_D"] = voto_con_modificatore(
        list(zip(voti_contro.MediaVoti_D, voti_contro.MediaFantaVoti_D)))

    voti_contro.to_excel(f"voti_contro.xlsx")

    giornate_soup = ottieni_giornate_soup(22)
    giornata_soup = [g_s for g_s in giornate_soup if f"GIORNATA {giornata}<" in str(g_s).upper()][0]
    squadre_soup = giornata_soup.find_all("span", attrs={"class": "ftbl__match-row__team--desktop"})
    casa_soup_coi_none = [el.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--right"})
                          for el in squadre_soup]
    ospiti_soup_coi_none = [el.find("span", attrs={
        "class": "ftbl__text ftbl__text--span ftbl__text--color-blue ftbl__text--font-size-14 ftbl__text--weight-500 ftbl__team__name ftbl__team__name--left"})
                            for el in squadre_soup]
    squadre_casa = [el.text.upper() for el in casa_soup_coi_none if el is not None]
    squadre_ospiti = [el.text.upper() for el in ospiti_soup_coi_none if el is not None]
    lista_incontri = {}
    for casa, ospite in zip(squadre_casa, squadre_ospiti):
        lista_incontri[casa] = ospite
        lista_incontri[ospite] = casa

    voti_potenziali = []
    fantavoti_potenziali = []
    voti = []
    fantavoti = []
    for ruolo, nome, squad, partite, med, fantaMedia, voto_piu_probabile, fantavoto_piu_probabile, posizione in risultato_finale.values:
        squadra = squad.upper()
        squadra_avversaria = lista_incontri[squadra]
        # ruolo = row[0]
        lista = voti_contro.loc[voti_contro.index != squadra][f"MediaVoti_{ruolo}"]
        fanta_lista = voti_contro.loc[voti_contro.index != squadra][f"MediaFantaVoti_{ruolo}"]
        voto_medio = sum(lista) / len(lista)
        fantavoto_medio = sum(fanta_lista) / len(fanta_lista)
        voto_previsto = med / voto_medio * voti_contro.loc[squadra_avversaria][f"MediaVoti_{ruolo}"]
        fantavoto_previsto = fantaMedia / fantavoto_medio * voti_contro.loc[squadra_avversaria][
            f"MediaFantaVoti_{ruolo}"]
        voto_previsto_t = 0.5 * int((voto_previsto + 0.25) / 0.5)
        voti.append(voto_previsto_t)
        fantavoto_previsto_t = 0.5 * int((fantavoto_previsto + 0.25) / 0.5)
        fantavoti.append(fantavoto_previsto_t)
        voti_potenziali.append(voto_previsto)
        fantavoti_potenziali.append(fantavoto_previsto)

    risultato_finale["VotoPotenziale"] = voti_potenziali
    risultato_finale["Voto"] = voti
    risultato_finale["FantaVotoPotenziale"] = fantavoti_potenziali
    risultato_finale["FantaVoto"] = fantavoti

    risultato_finale = risultato_finale[
        ["R", "Nome", "Squadra", "VotoPotenziale", "FantaVotoPotenziale", "Voto", "FantaVoto"]]
    p = risultato_finale.loc[risultato_finale.R == "P"]
    d = risultato_finale.loc[risultato_finale.R == "D"]
    c = risultato_finale.loc[risultato_finale.R == "C"]
    a = risultato_finale.loc[risultato_finale.R == "A"]

    p = p.sort_values("VotoPotenziale", ascending=False)
    p["Posizione"] = range(1, len(p) + 1)
    d = d.sort_values("VotoPotenziale", ascending=False)
    d["Posizione"] = range(1, len(d) + 1)
    c = c.sort_values("VotoPotenziale", ascending=False)
    c["Posizione"] = range(1, len(c) + 1)
    a = a.sort_values("VotoPotenziale", ascending=False)
    a["Posizione"] = range(1, len(a) + 1)

    consigli_giornata = pd.concat([p, d, c, a])
    print(f"creato consigli di giornata {ultima_giornata + 1} considerando le precedenti {n_giornate}")

    if salva_consigli:
        path_consigli_di_giornata = f"consigli_giornata/giornata_{ultima_giornata + 1}"
        file_consigli_di_giornata = f"consigli_ultime_{n_giornate}.xlsx"
        if not os.path.exists(path_consigli_di_giornata):
            os.makedirs(path_consigli_di_giornata)

        path_finale_consigli_di_giornata = os.path.join(path_consigli_di_giornata, file_consigli_di_giornata)
        consigli_giornata.to_excel(path_finale_consigli_di_giornata)
        print(
            f"salvato consigli di giornata {ultima_giornata + 1} considerando le precedenti {n_giornate} in {path_finale_consigli_di_giornata}")

    return consigli_giornata
