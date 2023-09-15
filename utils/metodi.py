import pandas as pd


def estrai_voto(x):
    return x not in ["Voto", "6*"]


def voto_troncato(x):
    return 0.5 * round(int(x * 100 / 25) / 2 + 0.1)


def dataframe_corretto(file):
    dataframe = pd.DataFrame([])
    colonne = ["Cod.", "Ruolo", "Nome", "Voto", "Gf", "Gs", "Rp", "Rs", "Rf", "Au", "Amm", "Esp", "Ass"]
    dataframe[colonne] = pd.read_excel(file).dropna().iloc[:, :13]
    dataframe = dataframe.loc[dataframe.Ruolo != 'ALL']
    dataframe = dataframe.loc[dataframe.Voto.apply(estrai_voto)]
    fantavoti = [voto + 3 * (Gf + Rp - Rs + Rf) - 2 * Au - Gs - Esp + Ass - 0.5 * Amm for
                 _, _, _, voto, Gf, Gs, Rp, Rs, Rf, Au, Amm, Esp, Ass in dataframe.values]
    dataframe["FantaVoto"] = fantavoti
    dataframe["Nome"] = dataframe.Nome.str.upper()
    return dataframe


def coefficiente_binomiale(n, k):
    if n < k or k < 0:
        raise ValueError(f"n deve essere maggiore o uguale a k ed entrambi non possono essere negativi"
                         f":\nn = {n}, k = {k}")
    delta = n - k
    k = min(delta, k)
    if k == 0:
        return 1
    return int(n / k * coefficiente_binomiale(n - 1, k - 1))


def binomiale(n, k, p):
    return coefficiente_binomiale(n, k) * p ** k * (1 - p) ** (n - k)


def estrai_probabilita(numero_possibili_voti, voto, voto_minimo, media):
    k = 2 * (voto - voto_minimo)
    p = 2 * (media - voto_minimo) / numero_possibili_voti
    return binomiale(numero_possibili_voti, k, p)


def voto_centrale(lista):
    media = sum(lista) / len(lista)
    minimo, massimo = min(lista), max(lista)
    numero_possibili_voti = int(2 * (massimo - minimo)) + 1
    voti_possibili = [minimo + 0.5 * i for i in range(numero_possibili_voti)]
    probabilita = [estrai_probabilita(numero_possibili_voti, voto_possibile, minimo, media) for voto_possibile in
                   voti_possibili]
    occorrenze = [probabilita.count(x) for x in probabilita]
    z = list(zip(probabilita, voti_possibili, occorrenze))
    z.sort(reverse=True)
    voto_centrale = sum(list(map(lambda x: x[1], z[:z[0][2]]))) / z[0][2]
    return voto_centrale


def media(lista):
    return sum(lista) / len(lista)


def maiuscolo(el):
    return el.upper()


def estrai_sfidante(df, squadra):
    if df.HomeTeam.apply(maiuscolo).values[0] == squadra:
        return df.AwayTeam.apply(maiuscolo).values[0]
    return df.HomeTeam.apply(maiuscolo).values[0]


def estrai_voti(df, squadra):
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


def inserisci(diz, col_media, squadra, media_voto):
    try:
        diz[col_media][squadra] += media_voto
    except KeyError:
        diz[col_media][squadra] = media_voto


def voto_con_modificatore(lista_v_fv):
    a = 2
    b = -21
    c = 55
    return [(a * v ** 2 + b * v + c) / 4 + fv for v, fv in lista_v_fv]


def voto_potenziale(voto, fanta_voto, ruolo):
    if ruolo in ["D", "P"]:
        return (2 * voto ** 2 - 21 * voto + 55) / 4 + fanta_voto
    return fanta_voto
