from math import isnan

from modello_fantacalcio import *
from SeasonDf import *


def remove_all(lista, el):
    if el not in lista:
        return lista
    lista.remove(el)
    return remove_all(lista, el)


def non_schierabili():
    re = requests.get("https://www.fantacalcio.it/indisponibili-serie-a")
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
    if x < 6.5:
        return 1
    if x < 7:
        return 3
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
    dubbi = []
    numero_titolari_sicuri = 0
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


def titolari_e_panchinari(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None, modulo=None):
    if aggiunte is None:
        aggiunte = []
    if esclusioni is None:
        esclusioni = []
    formazioni_prescelte = []
    formazioni_nomi_prescelti = []
    tit = []
    formazioni = [
        "3-5-2",
        "3-4-3",
        "4-5-1",
        "4-4-2",
        "4-3-3",
        "5-3-2",
        "5-4-1"
    ] if modulo is None else modulo
    i = 0
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte]
        lista_esclusi = non_schierabili_default + esclusioni
        sub_dfs = [df.query(f"""Nome not in {to_string_list(lista_esclusi)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = [df.query(f"""Nome not in {to_string_list(non_schierabili_default)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
    else:
        sub_dfs = [df.query(f"""Nome in {to_string_list(lista_giocatori_titolari)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale"], ascending=(False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = sub_dfs
    for formazione in formazioni:
        punteggi = []
        for df in sub_dfs:
            i += 1
            n_dif, n_cen, n_att, squadra_prescelta = ottieniTitolari(formazione, df)
            if n_dif < 4:
                punteggio = squadra_prescelta.FantaVoto.sum()
            else:
                punteggio = squadra_prescelta.FantaVoto.sum() + modificatore(squadra_prescelta.head(4).Voto.mean())
            punteggi.append(punteggio)
            dizionario_titolari_per_modulo[formazione].append(squadra_prescelta)
        medie_punteggi.append([media(punteggi), inv_varianza(punteggi, media(punteggi)), formazione])
    punteggio_medio, _, modulo_migliore = max(medie_punteggi)
    multi_formazione = [p for p, inv_var, mod in medie_punteggi].count(punteggio_medio) > 1
    if multi_formazione:
        print(f"scegli un modulo tra {', '.join([modulo for p, _, modulo in medie_punteggi if p == punteggio_medio])}")
        return None, None, None
    print(modulo_migliore, punteggio_medio)

    tit = [sq[["R", "Nome", "Squadra"]] for sq in dizionario_titolari_per_modulo[modulo_migliore]]

    dubbi, squadra_titolare = unicita(tit)
    n = 11 - len(squadra_titolare)
    t = pd.concat(sub_dfs_complete)
    if lista_giocatori_titolari is None:
        listone = t.groupby(["R", "Nome"])[["FantaVotoPotenziale", "VotoPotenziale"]].mean().query(
            f"Nome not in {to_string_list(non_schierabili_default)}").reset_index()
        listone["FantaVotoTroncato"] = listone.FantaVotoPotenziale.apply(troncato)
        listone["VotoTroncato"] = listone.VotoPotenziale.apply(troncato)
        listone = listone.sort_values(["FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"],
                                      ascending=(False, False, False, False))
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
        merged = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
        merged = merged[merged['_merge'] == 'left_only'][
            ["R", "Nome", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"]]
        return squadra_titolare, merged, listone
    return squadra_titolare, None, None


def titolari_e_panchinari2(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None,
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
    i = 0
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    dizionario_per_modulo = {f: {} for f in formazioni}
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte]
        lista_esclusi = non_schierabili_default + esclusioni
        sub_dfs = [df.query(f"""Nome not in {to_string_list(lista_esclusi)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = [df.query(f"""Nome not in {to_string_list(non_schierabili_default)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
    else:
        sub_dfs = [df.query(f"""Nome in {to_string_list(lista_giocatori_titolari)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale"], ascending=(False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = sub_dfs
    for formazione in formazioni:
        punteggi = []
        for df in sub_dfs:
            i += 1
            n_dif, n_cen, n_att, squadra_prescelta = ottieniTitolari(formazione, df)
            if n_dif < 4:
                punteggio = squadra_prescelta.FantaVoto.sum()
            else:
                punteggio = squadra_prescelta.FantaVoto.sum() + modificatore(squadra_prescelta.head(4).Voto.mean())
            punteggi.append(punteggio)
            dizionario_titolari_per_modulo[formazione].append(squadra_prescelta)
        tit_formazione = [sq[["R", "Nome", "Squadra"]] for sq in dizionario_titolari_per_modulo[formazione]]
        dubbi, squadra_titolare = unicita(tit_formazione)
        n = 11 - len(squadra_titolare)
        t = pd.concat(sub_dfs_complete)
        if lista_giocatori_titolari is None:
            listone = t.groupby(["R", "Nome"])[["FantaVotoPotenziale", "VotoPotenziale"]].mean().query(
                f"Nome not in {to_string_list(non_schierabili_default)}").reset_index()
            listone["FantaVotoTroncato"] = listone.FantaVotoPotenziale.apply(troncato)
            listone["VotoTroncato"] = listone.VotoPotenziale.apply(troncato)
            listone = listone.sort_values(
                ["FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"],
                ascending=(False, False, False, False))
            if n != 0:
                merge = listone.merge(dubbi, on=["R", "Nome"])[
                    ["R", "Nome", "Squadra", "counts", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale",
                     "VotoPotenziale"]]
                merge = merge.sort_values(
                    by=['R', 'counts', 'FantaVotoTroncato', 'VotoTroncato', 'FantaVotoPotenziale', 'VotoPotenziale'],
                    ascending=(False, False, False, False, False, False))
                d_p_r = dubbi_per_ruolo(squadra_titolare, formazione)
                ultimi_titolari = pd.DataFrame()
                for ruolo in d_p_r:
                    ultimi_titolari = pd.concat(
                        [ultimi_titolari, merge[merge.R == ruolo][:d_p_r[ruolo]][["R", "Nome", "Squadra", "counts"]]])
                squadra_titolare = pd.concat([squadra_titolare, ultimi_titolari]).sort_values("R", ascending=False)
            merged = pd.merge(listone, squadra_titolare, how='outer', indicator=True)
            merged = merged[merged['_merge'] == 'left_only'][
                ["R", "Nome", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"]]
            merged.sort_values(
                ["FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"],
                ascending=(False, False, False, False))
        squadra_titolare_merged = pd.merge(squadra_titolare, listone, how='inner', indicator=True)[
            ['R', 'Nome', 'Squadra', 'FantaVotoPotenziale', 'VotoPotenziale', 'FantaVotoTroncato', 'VotoTroncato',
             'counts']]
        squadra_titolare_merged = squadra_titolare_merged.sort_values(
            ["R", "FantaVotoTroncato", "VotoTroncato", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False))
        dizionario_per_modulo[formazione]["dfs"] = [squadra_titolare_merged[['R', 'Nome', 'Squadra', 'counts']], merged,
                                                    listone]
        dizionario_per_modulo[formazione]["media"] = \
            squadra_titolare_merged.FantaVotoTroncato.sum() if n_dif < 4 \
                else squadra_titolare_merged.FantaVotoTroncato.sum() + modificatore(
                squadra_titolare_merged.head(4).VotoTroncato.mean())
    medie = [dizionario_per_modulo[mod]["media"] for mod in dizionario_per_modulo]
    massimo = max(medie)
    valore_massimo = [m for m in medie if m == massimo]
    modulo_valore_massimo = [mod for mod in dizionario_per_modulo if
                             dizionario_per_modulo[mod]["media"] == valore_massimo[0]]
    if len(valore_massimo) > 1:
        print(f"scegli un modulo tra {', '.join(modulo_valore_massimo)}")
        return None, None, None
    print(modulo_valore_massimo[0], massimo)
    return dizionario_per_modulo[modulo_valore_massimo[0]]["dfs"]


def titolari_e_panchinari3(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None,
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
    i = 0
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    non_schierabili_default = [""]
    lista_esclusi = [""]
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte]
        lista_esclusi = non_schierabili_default + esclusioni
        sub_dfs_complete = [df.query(f"""Nome not in {to_string_list(non_schierabili_default)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
    else:
        sub_dfs_complete = [df.query(f"""Nome in {to_string_list(lista_giocatori_titolari)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale"], ascending=(False, False, False)) for df in dfs[:num_df]]
    t = pd.concat(sub_dfs_complete)
    listone = t.groupby(["R", "Nome", "Squadra"])[["FantaVotoPotenziale", "VotoPotenziale"]].mean().query(
        f"Nome not in {to_string_list(non_schierabili_default)}").reset_index()
    listone["FantaVoto"] = listone.FantaVotoPotenziale.apply(troncato)
    listone["Voto"] = listone.VotoPotenziale.apply(troncato)
    listone = listone.sort_values(["FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
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
        medie_punteggi.append([media(punteggi), inv_varianza(punteggi, media(punteggi)), formazione])
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
        merged = merged[merged['_merge'] == 'left_only'][listone.columns.tolist()]
        return squadra_titolare, merged, listone
    return squadra_titolare, None, None


def titolari_e_panchinari4(dfs, num_df=None, esclusioni=None, aggiunte=None, lista_giocatori_titolari=None,
                           modulo=None):
    if aggiunte is None:
        aggiunte = []
    if esclusioni is None:
        esclusioni = []
    formazioni_prescelte = []
    formazioni_nomi_prescelti = []
    tit = []
    formazioni = [
        "3-5-2",
        "3-4-3",
        "4-5-1",
        "4-4-2",
        "4-3-3",
        "5-3-2",
        "5-4-1"
    ] if modulo is None else modulo
    i = 0
    medie_punteggi = []
    dizionario_titolari_per_modulo = {f: [] for f in formazioni}
    if lista_giocatori_titolari is None:
        squalificati, indisponibili, in_dubbio = non_schierabili()
        non_schierabili_default = [giocatore for giocatore in squalificati + indisponibili if giocatore not in aggiunte]
        lista_esclusi = non_schierabili_default + esclusioni
        sub_dfs = [df.query(f"""Nome not in {to_string_list(lista_esclusi)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = [df.query(f"""Nome not in {to_string_list(non_schierabili_default)}""").sort_values(
            ["R", "FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
            ascending=(False, False, False, False, False)) for df in dfs[:num_df]]
    else:
        sub_dfs = [df.query(f"""Nome in {to_string_list(lista_giocatori_titolari)}""").sort_values(
            ["R", "FantaVoto", "FantaVotoPotenziale"], ascending=(False, False, False)) for df in dfs[:num_df]]
        sub_dfs_complete = sub_dfs
    t = pd.concat(sub_dfs_complete)
    listone = t.groupby(["R", "Nome", "Squadra"])[["FantaVotoPotenziale", "VotoPotenziale"]].mean().query(
        f"Nome not in {to_string_list(non_schierabili_default)}").reset_index()
    listone["FantaVoto"] = listone.FantaVotoPotenziale.apply(troncato)
    listone["Voto"] = listone.VotoPotenziale.apply(troncato)
    listone = listone.sort_values(["FantaVoto", "Voto", "FantaVotoPotenziale", "VotoPotenziale"],
                                  ascending=(False, False, False, False))
    listone_per_squadra_titolare = listone.query(f"""Nome not in {to_string_list(lista_esclusi)}""")
    for formazione in formazioni:
        punteggi = []
        # for df in sub_dfs:
        #     i += 1
        n_dif, n_cen, n_att, squadra_prescelta = ottieniTitolari(formazione, listone_per_squadra_titolare)
        if n_dif < 4:
            punteggio = squadra_prescelta.FantaVoto.sum()
        else:
            punteggio = squadra_prescelta.FantaVoto.sum() + modificatore(squadra_prescelta.head(4).Voto.mean())
        punteggi.append(punteggio)
        dizionario_titolari_per_modulo[formazione].append(squadra_prescelta)
        medie_punteggi.append([media(punteggi), inv_varianza(punteggi, media(punteggi)), formazione])
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
        merged = merged[merged['_merge'] == 'left_only'][listone.columns.tolist()]
        return squadra_titolare, merged, listone
    return squadra_titolare, None, None
