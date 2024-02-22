import os

import pandas as pd

from utils.metodi import *
from root import ROOT_DIR

pd.options.mode.chained_assignment = None


def modello_fantacalcio(
        giornata_esaminata,
        numero_giornate,
        stagione,
        salva_excel=False,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    root = ROOT_DIR
    percorso = f"{ROOT_DIR}/Voti_Fantacalcio"
    nomi_excel: list = [file for (root, dirs, file) in os.walk(percorso)][0]
    nomi_excel.reverse()
    # indiceMax = nomi_excel.index(
    #     f"Voti_Fantacalcio_Stagione_20{stagione}_{stagione + 1}_Giornata_{f'0{giornata_esaminata}' if giornata_esaminata < 10 else giornata_esaminata}.xlsx")
    # percorsi_excel = [f"{ROOT_DIR}/Voti_Fantacalcio/{n}" for n in nomi_excel[indiceMax:indiceMax + numero_giornate]]

    percorsi_excel = [f"{ROOT_DIR}/Voti_Fantacalcio/{n}" for n in nomi_excel]

    lista_dataframe = [dataframe_corretto(ex) for ex in percorsi_excel]
    season_df = pd.concat([leggi(s, create=False) for s in range(stagione - 1, stagione + 1)]) \
        if giornata_esaminata < numero_giornate else leggi(stagione, create=False)
    season = sqldf("""
    select
        data,
        team,
        giornata,
        stagione,
        dense_rank() over (partition by team order by stagione desc, data desc) as GIORNATA_CALCOLATA                
    from (
        select
            Data,
            HomeTeam as TEAM,
            giornata,
            stagione
        from season_df
        union all
        select
            Data,
            AwayTeam as TEAM,
            giornata,
            stagione
        from season_df
    )
    """)
    lista_dataframe_filtrati = []
    for df in lista_dataframe:
        dataframe = sqldf(f"""
        select
            df.COD,
            df.RUOLO,
            df.NOME,
            CAST(df.VOTO AS FLOAT) AS VOTO,
            df.GOL_FATTI,
            df.GOL_SUBITI,
            df.RIGORI_PARATI,
            df.RIGORI_SBAGLIATI,
            df.RIGORI_FATTI,
            df.AUTOGOL,
            df.AMMONIZIONI,
            df.ESPULSIONI,
            df.ASSIST,
            df.FANTAVOTO,
            df.SQUADRA
        from df
        join season s
         on df.squadra = s.team
        and df.giornata = s.giornata
        and df.stagione = s.stagione
        where GIORNATA_CALCOLATA <= {numero_giornate}
        """)
        if len(dataframe) > 0:
            lista_dataframe_filtrati.append(dataframe)
    dizionario_statistiche = {}
    for dataframe in lista_dataframe_filtrati:
        for cod, ruolo, nome, voto, gol_fatti, gol_subiti, rigori_parati, rigori_sbagliati, rigori_fatti, autogol, ammonizioni, espulsione, assist, fanta_voto, squadra in dataframe.values:
            # line = ndarray.tolist()
            try:
                dizionario_statistiche[cod]["GolFatti"].append(gol_fatti + rigori_fatti)
                dizionario_statistiche[cod]["Assist"].append(assist)
                dizionario_statistiche[cod]["GolSubiti"].append(gol_subiti)
                dizionario_statistiche[cod]["RigoriParati"].append(rigori_parati)
                dizionario_statistiche[cod]["RigoriSbagliati"].append(rigori_sbagliati)
                dizionario_statistiche[cod]["Autogol"].append(autogol)
                dizionario_statistiche[cod]["Gialli"].append(ammonizioni)
                dizionario_statistiche[cod]["Rossi"].append(espulsione)
                dizionario_statistiche[cod]["Voti"].append(voto)
                dizionario_statistiche[cod]["FantaVoti"].append(fanta_voto)
                dizionario_statistiche[cod]["Partite"] += 1
            except KeyError:
                dizionario_statistiche[cod] = {"Nome": nome,
                                               "R": ruolo,
                                               "GolFatti": [gol_fatti + rigori_fatti],
                                               "Assist": [assist],
                                               "GolSubiti": [gol_subiti],
                                               "RigoriParati": [rigori_parati],
                                               "RigoriSbagliati": [rigori_sbagliati],
                                               "Autogol": [autogol],
                                               "Gialli": [ammonizioni],
                                               "Rossi": [espulsione],
                                               "Voti": [voto],
                                               "FantaVoti": [fanta_voto],
                                               "Partite": 1,
                                               "Squadra": squadra}

    statistiche = pd.DataFrame.from_dict(dizionario_statistiche).transpose()
    statistiche["Media"] = statistiche.Voti.apply(media)
    statistiche["FantaMedia"] = statistiche.FantaVoti.apply(media)
    statistiche["VotoCentrale"] = statistiche.Voti.apply(voto_centrale)
    statistiche["FantaVotoCentrale"] = statistiche.FantaVoti.apply(voto_centrale)
    statistiche["VotoTroncato"] = statistiche.Media.apply(voto_troncato)
    statistiche["FantaVotoTroncato"] = statistiche.FantaMedia.apply(voto_troncato)

    statistiche = statistiche[
        ["Nome", "R", "Partite", "Media", "FantaMedia", "VotoCentrale", "FantaVotoCentrale", "VotoTroncato",
         "FantaVotoTroncato", "Squadra"]
    ]

    # quotazioni = pd.read_excel(file_quotazioni, header=1)
    # quotazioni["Nome"] = quotazioni["Nome"].str.upper()

    statistiche['Cod'] = statistiche.index

    # statistiche = pd.merge(quotazioni, statistiche, on="Nome", how='inner')
    statistiche = statistiche.loc[(statistiche.Partite >= percentuale_presenze * numero_giornate)]

    porta = statistiche.loc[statistiche.R == "P"]
    porta = porta.sort_values(["FantaMedia", "Media"], ascending=(False, False))
    porta["Posizione"] = range(1, len(porta) + 1)

    difesa = statistiche.loc[statistiche.R == "D"]
    difesa = difesa.sort_values(["FantaMedia", "Media"], ascending=(False, False))
    difesa["Posizione"] = range(1, len(difesa) + 1)

    centrocampo = statistiche.loc[statistiche.R == "C"]
    centrocampo = centrocampo.sort_values(["FantaMedia", "Media"], ascending=(False, False))
    centrocampo["Posizione"] = range(1, len(centrocampo) + 1)

    attacco = statistiche.loc[statistiche.R == "A"]
    attacco = attacco.sort_values(["FantaMedia", "Media"], ascending=(False, False))
    attacco["Posizione"] = range(1, len(attacco) + 1)

    colonne = ["Cod", "R", "Nome", "Squadra", "Partite", "Media", "FantaMedia", "VotoCentrale", "FantaVotoCentrale",
               "Posizione"]

    modello_fantacalcio = pd.concat([porta, difesa, centrocampo, attacco])[colonne]

    if salva_excel:
        path_modello_fantacalcio = f"{ROOT_DIR}/estrazioni/modello_fantacalcio/giornata_{giornata_esaminata}"
        file_modello_fantacalcio = f"modello_fantacalcio_ultime_{numero_giornate}.xlsx"
        if not os.path.exists(path_modello_fantacalcio):
            os.makedirs(path_modello_fantacalcio)

        path_finale_modello_fantacalcio = os.path.join(path_modello_fantacalcio, file_modello_fantacalcio)

        # Create statistiche Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(path_finale_modello_fantacalcio, engine='xlsxwriter')

        # Write each dataframe to statistiche different worksheet.
        modello_fantacalcio.to_excel(writer, index=False, sheet_name='modello_fantacalcio')
        porta[colonne].to_excel(writer, index=False, sheet_name='PORTIERI')
        difesa[colonne].to_excel(writer, index=False, sheet_name='DIFENSORI')
        centrocampo[colonne].to_excel(writer, index=False, sheet_name='CENTROCAMPISTI')
        attacco[colonne].to_excel(writer, index=False, sheet_name='ATTACCANTI')

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        print(
            f"salvato modello fantacalcio {giornata_esaminata} considerando le precedenti {numero_giornate} in {path_finale_modello_fantacalcio}")

    return percorsi_excel, modello_fantacalcio


if __name__ == "__main__":
    modello_fantacalcio(
        giornata_esaminata=19,
        numero_giornate=4,
        salva_excel=True,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
    )
