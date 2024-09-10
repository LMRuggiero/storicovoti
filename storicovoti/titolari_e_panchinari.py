from math import isnan

import duckdb
import pandas as pd
import requests
from bs4 import BeautifulSoup

import utils.metodi as me


def non_schierabili():
    re = requests.get("https://www.fantacalcio.it/indisponibili-serie-a", verify=False)
    soup = BeautifulSoup(re.text, "html.parser")

    info_squadre = soup.find_all("div", attrs={"class": "row row-responsive"})
    squalificati = []
    indisponibili = []
    in_dubbio = []
    for info_squadra in info_squadre:
        for giocatore in info_squadra.find_all("li"):
            nome = giocatore.find("strong", attrs={"class": "item-name"}).contents[0].upper()
            squalificato = "squalificato" in str(giocatore).lower()
            squalificati.append(nome) if squalificato else indisponibili.append(nome) if len(giocatore) > 3 else None
    return squalificati, indisponibili, in_dubbio


def inv_varianza(lista, mu):
    if lista.count(mu) == len(lista):
        return 9999999
    return 1 / sum([(el - mu) ** 2 for el in lista])


def modificatore(x):
    if x < 6 or isnan(x):
        return 0
    if x < 6.25:
        return 1
    if x < 6.5:
        return 2
    if x < 6.75:
        return 3
    if x < 7:
        return 4
    return 6


def to_string_list(lista_giocatori):
    return f"""("{'", "'.join(lista_giocatori)}")"""


def ottieniTitolari(formazione, df):
    n_dif, n_cen, n_att = [int(n) for n in formazione.split("-")]
    return n_dif, n_cen, n_att, pd.concat(
        [df.loc[df.R == "P"].head(1),
         df.loc[df.R == "D"].head(n_dif),
         df.loc[df.R == "C"].head(n_cen),
         df.loc[df.R == "A"].head(n_att)])


def unicita(formazioni):
    lista_totale = pd.DataFrame()
    for formazione in formazioni:
        lista_totale = pd.concat([lista_totale, formazione])
    l_tot_grouped = lista_totale.groupby(["R", "Nome", "Squadra"]).size().reset_index(name='counts').sort_values(
        ["R", "Nome"], ascending=(False, True))
    dubbi = l_tot_grouped[l_tot_grouped.counts < len(formazioni)]
    titolari = l_tot_grouped[l_tot_grouped.counts == len(formazioni)]
    return dubbi, titolari


def dubbi_per_ruolo(squadra_titolare, modulo):
    mod = f"1-{modulo}"
    numero_titolari_per_ruolo = squadra_titolare.groupby("R").size().to_frame().reset_index()
    ruoli_presenti = numero_titolari_per_ruolo.R.tolist()
    ruoli_possibili = ["P", "D", "C", "A"]
    d_p_r = {key: 0 for key in ruoli_possibili}
    for r, k in zip(ruoli_possibili, [int(j) for j in mod.split("-")]):
        if r in ruoli_presenti:
            n = k - numero_titolari_per_ruolo[numero_titolari_per_ruolo.R == r][0].values[0]
        else:
            n = k
        d_p_r[r] = n
    return d_p_r


def troncato(x):
    return 0.5 * round(int(x / 0.25) / 2 + 0.25000001)


def titolari_e_panchinari(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None,
                          modulo=None):
    if aggiunte is None:
        aggiunte = []
    if esclusioni is None:
        esclusioni = []
    formazioni = [
        "3-5-2",
        "3-4-3",
        "4-5-1",
        "4-4-2",
        "4-3-3",
        "5-3-2",
        "5-4-1"
    ] if modulo is None else modulo
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    non_schierabili_default = pd.DataFrame([], columns=["NOME"])
    lista_esclusi = pd.DataFrame([], columns=["NOME"])
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = pd.DataFrame(
            [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte], columns=["NOME"])
        esclusi = pd.DataFrame(esclusioni, columns=["NOME"])
        lista_esclusi = pd.concat([non_schierabili_default, esclusi])
        sub_dfs_complete = [
            duckdb.query(f"""
            select df.*
            from df
            left join non_schierabili_default l
              on df.nome = l.nome
            where l.nome is null
            order by R desc, FantaVoto desc, Voto desc, FantaVotoPotenziale desc, VotoPotenziale desc
            """).df() for df in dfs[:num_df]
        ]
    else:
        lista_giocatori_titolari = pd.DataFrame(lista_giocatori_titolari, columns=["NOME"])
        sub_dfs_complete = [
            duckdb.query(f"""
            select df.*
            from df
            left join lista_giocatori_titolari l
              on df.nome = l.nome
            where l.nome is not null
            order by R desc, FantaVoto desc, FantaVotoPotenziale desc
            """).df() for df in dfs[:num_df]]
    quotazioni = pd.read_csv("sorgenti/Quotazioni_Fantacalcio_Stagione_2024_25.csv", sep=";")
    t = pd.concat(sub_dfs_complete)
    listone = duckdb.query("""
    select
        q.R,
        upper(q.nome) Nome,
        q.Squadra,
        avg(FantaVotoPotenziale) as FantaVotoPotenziale,
        avg(VotoPotenziale) as VotoPotenziale
    from t
    join quotazioni q
      on t.cod = q.id
    left join non_schierabili_default n
      on t.nome = n.nome
    where n.nome is null
    group by q.R, q.Squadra, q.Nome
    """).df()
    listone["FantaVoto"] = listone.FantaVotoPotenziale.apply(troncato)
    listone["Voto"] = listone.VotoPotenziale.apply(troncato)
    listone = listone.sort_values(by=["FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
                                  ascending=(False, False, False, False))
    listone_per_squadra_titolare = duckdb.query("""
    select l.*
    from listone l
    left join lista_esclusi le
      on l.nome = le.nome
    where le.nome is null
    order by FantaVoto desc, Voto desc, FantaVotoPotenziale desc, VotoPotenziale desc
    """).df()
    for formazione in formazioni:
        punteggi = []
        n_dif, n_cen, n_att, squadra_prescelta = ottieniTitolari(formazione, listone_per_squadra_titolare)
        if n_dif < 4:
            punteggio = squadra_prescelta.FantaVoto.sum()
        else:
            punteggio = squadra_prescelta.FantaVoto.sum() + modificatore(squadra_prescelta.head(4).Voto.mean())
        punteggi.append(punteggio)
        dizionario_titolari_per_modulo[formazione].append(squadra_prescelta)
        medie_punteggi.append([me.media(punteggi), inv_varianza(punteggi, me.media(punteggi)), formazione])
    punteggio_medio, _, modulo_migliore = max(medie_punteggi)
    multi_formazione = [p for p, inv_var, mod in medie_punteggi].count(punteggio_medio) > 1
    if multi_formazione:
        print(f"scegli un modulo tra {', '.join([modulo for p, _, modulo in medie_punteggi if p == punteggio_medio])}")
        return None, None, None
    print(modulo_migliore, punteggio_medio)

    tit = [sq[["R", "Nome", "Squadra"]] for sq in dizionario_titolari_per_modulo[modulo_migliore]]

    dubbi, squadra_titolare = unicita(tit)
    n = 11 - len(squadra_titolare)
    if lista_giocatori_titolari is None:
        if n != 0:
            merge = listone.merge(dubbi, on=["R", "Nome"])[
                ["R", "Nome", "Squadra", "counts", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale",
                 "VotoPotenziale"]]
            merge = merge.sort_values(
                by=['R', 'counts', 'FantaVotoTroncato', 'VotoTroncato', 'FantaVotoPotenziale', 'VotoPotenziale'],
                ascending=(False, False, False, False, False, False))
            d_p_r = dubbi_per_ruolo(squadra_titolare, modulo_migliore)
            ultimi_titolari = pd.DataFrame()
            for ruolo in d_p_r:
                ultimi_titolari = pd.concat(
                    [ultimi_titolari, merge[merge.R == ruolo][:d_p_r[ruolo]][["R", "Nome", "Squadra", "counts"]]])
            squadra_titolare = pd.concat([squadra_titolare, ultimi_titolari]).sort_values("R", ascending=False)
        squadra_titolare = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
        squadra_titolare = squadra_titolare[squadra_titolare['_merge'] == 'both'][listone.columns.tolist()]
        squadra_titolare = squadra_titolare.sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False))
        merged = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
        merged = merged[merged['_merge'] == 'left_only'][listone.columns.tolist()].sort_values(
            ["FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"], ascending=(False, False, False, False))
        return squadra_titolare, merged, listone
    return squadra_titolare, None, None


def titolari_e_panchinari_modello(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None,
                                  modulo=None):
    if aggiunte is None:
        aggiunte = []
    if esclusioni is None:
        esclusioni = []
    formazioni = [
        "3-5-2",
        "3-4-3",
        "4-5-1",
        "4-4-2",
        "4-3-3",
        "5-3-2",
        "5-4-1"
    ] if modulo is None else modulo
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    non_schierabili_default = [""]
    lista_esclusi = [""]
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte]
        lista_esclusi = non_schierabili_default + esclusioni
        sub_dfs_complete = [df.query(f"""Nome not in {to_string_list(non_schierabili_default)}""").sort_values(
            ["R", "FantaMedia", "Media"],
            ascending=(False, False, False)) for df in dfs[:num_df]]
    else:
        sub_dfs_complete = [df.query(f"""Nome in {to_string_list(lista_giocatori_titolari)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale"], ascending=(False, False, False)) for df in dfs[:num_df]]
    t = pd.concat(sub_dfs_complete)
    listone = t.groupby(["R", "Nome", "Squadra"])[["FantaMedia", "Media"]].mean().query(
        f"Nome not in {to_string_list(non_schierabili_default)}").reset_index()
    listone["FantaVoto"] = listone.FantaMedia.apply(troncato)
    listone["Voto"] = listone.Media.apply(troncato)
    listone = listone.sort_values(["FantaVoto", "Voto", "FantaMedia", "Media"],
                                  ascending=(False, False, False, False))
    listone_per_squadra_titolare = listone.query(f"""Nome not in {to_string_list(lista_esclusi)}""")
    for formazione in formazioni:
        punteggi = []
        n_dif, n_cen, n_att, squadra_prescelta = ottieniTitolari(formazione, listone_per_squadra_titolare)
        if n_dif < 4:
            punteggio = squadra_prescelta.FantaVoto.sum()
        else:
            punteggio = squadra_prescelta.FantaVoto.sum() + modificatore(squadra_prescelta.head(4).Voto.mean())
        punteggi.append(punteggio)
        dizionario_titolari_per_modulo[formazione].append(squadra_prescelta)
        medie_punteggi.append([me.media(punteggi), inv_varianza(punteggi, me.media(punteggi)), formazione])
    punteggio_medio, _, modulo_migliore = max(medie_punteggi)
    multi_formazione = [p for p, inv_var, mod in medie_punteggi].count(punteggio_medio) > 1
    if multi_formazione:
        print(f"scegli un modulo tra {', '.join([modulo for p, _, modulo in medie_punteggi if p == punteggio_medio])}")
        return None, None, None
    print(modulo_migliore, punteggio_medio)

    tit = [sq[["R", "Nome", "Squadra"]] for sq in dizionario_titolari_per_modulo[modulo_migliore]]

    dubbi, squadra_titolare = unicita(tit)
    n = 11 - len(squadra_titolare)
    if lista_giocatori_titolari is None:
        if n != 0:
            merge = listone.merge(dubbi, on=["R", "Nome"])[
                ["R", "Nome", "Squadra", "counts", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale",
                 "VotoPotenziale"]]
            merge = merge.sort_values(
                by=['R', 'counts', 'FantaVotoTroncato', 'VotoTroncato', 'FantaVotoPotenziale', 'VotoPotenziale'],
                ascending=(False, False, False, False, False, False))
            d_p_r = dubbi_per_ruolo(squadra_titolare, modulo_migliore)
            ultimi_titolari = pd.DataFrame()
            for ruolo in d_p_r:
                ultimi_titolari = pd.concat(
                    [ultimi_titolari, merge[merge.R == ruolo][:d_p_r[ruolo]][["R", "Nome", "Squadra", "counts"]]])
            squadra_titolare = pd.concat([squadra_titolare, ultimi_titolari]).sort_values("R", ascending=False)
        squadra_titolare = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
        squadra_titolare = squadra_titolare[squadra_titolare['_merge'] == 'both'][listone.columns.tolist()]
        squadra_titolare = squadra_titolare.sort_values(
            ["R", "FantaVoto", "Voto", "FantaMedia", "Media"],
            ascending=(False, False, False, False, False))
        merged = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
        merged = merged[merged['_merge'] == 'left_only'][listone.columns.tolist()]
        return squadra_titolare, merged, listone
    return squadra_titolare, None, None
