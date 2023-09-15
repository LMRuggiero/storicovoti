import pandas as pd
import os

import utils.metodi as me
from root import ROOT_DIR

pd.options.mode.chained_assignment = None


def modello_fantacalcio(
        giornata_esaminata,
        numero_giornate,
        salva_excel=False,
        percentuale_presenze=0.375,
        file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    root = ROOT_DIR
    percorso = f"{ROOT_DIR}/Voti_Fantacalcio"
    nomi_excel = [file for (root, dirs, file) in os.walk(percorso)][0]
    nomi_excel.reverse()
    ultima_file_scaricato = nomi_excel[0]
    ultima_giornata_scaricata = int(ultima_file_scaricato.split("_")[-1].split(".xlsx")[0])
    if ultima_giornata_scaricata < giornata_esaminata:
        raise Exception(f"non è presente file Voti_Fantacalcio per la giornata {giornata_esaminata}")
    indice_file = ultima_giornata_scaricata - giornata_esaminata
    percorsi_excel = [f"{ROOT_DIR}/Voti_Fantacalcio/{ex}" for ex in nomi_excel][
                     indice_file:indice_file + numero_giornate]

    lista_dataframe = [me.dataframe_corretto(ex) for ex in percorsi_excel]

    dizionario_statistiche = {}
    for dataframe in lista_dataframe:
        for _, ruolo, nome, voto, gol_fatti, gol_subiti, rigori_parati, rigori_sbagliati, rigori_fatti, autogol, ammonizioni, espulsione, assist, fanta_voto in dataframe.values:
            # line = ndarray.tolist()
            try:
                dizionario_statistiche[nome]["GolFatti"].append(gol_fatti + rigori_fatti)
                dizionario_statistiche[nome]["Assist"].append(assist)
                dizionario_statistiche[nome]["GolSubiti"].append(gol_subiti)
                dizionario_statistiche[nome]["RigoriParati"].append(rigori_parati)
                dizionario_statistiche[nome]["RigoriSbagliati"].append(rigori_sbagliati)
                dizionario_statistiche[nome]["Autogol"].append(autogol)
                dizionario_statistiche[nome]["Gialli"].append(ammonizioni)
                dizionario_statistiche[nome]["Rossi"].append(espulsione)
                dizionario_statistiche[nome]["Voti"].append(voto)
                dizionario_statistiche[nome]["FantaVoti"].append(fanta_voto)
                dizionario_statistiche[nome]["Partite"] += 1
            except KeyError:
                dizionario_statistiche[nome] = {"R": ruolo,
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
                                                "Partite": 1}

    statistiche = pd.DataFrame.from_dict(dizionario_statistiche).transpose()
    statistiche["Media"] = statistiche.Voti.apply(me.media)
    statistiche["FantaMedia"] = statistiche.FantaVoti.apply(me.media)
    statistiche["VotoCentrale"] = statistiche.Voti.apply(me.voto_centrale)
    statistiche["FantaVotoCentrale"] = statistiche.FantaVoti.apply(me.voto_centrale)
    statistiche["VotoTroncato"] = statistiche.Media.apply(me.voto_troncato)
    statistiche["FantaVotoTroncato"] = statistiche.FantaMedia.apply(me.voto_troncato)

    statistiche = statistiche[
        ["Partite", "Media", "FantaMedia", "VotoCentrale", "FantaVotoCentrale", "VotoTroncato", "FantaVotoTroncato"]
    ]

    quotazioni = pd.read_excel(file_quotazioni, header=1)
    quotazioni["Nome"] = quotazioni["Nome"].str.upper()

    statistiche['Nome'] = statistiche.index

    statistiche = pd.merge(quotazioni, statistiche, on="Nome", how='inner')
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

    colonne = ["R", "Nome", "Squadra", "Partite", "Media", "FantaMedia", "VotoCentrale", "FantaVotoCentrale",
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
        writer.save()

        print(
            f"salvato modello fantacalcio {giornata_esaminata} considerando le precedenti {numero_giornate} in {path_finale_modello_fantacalcio}")

    return percorsi_excel, modello_fantacalcio


if __name__ == "__main__":
    modello_fantacalcio(
        giornata_esaminata=19,
        numero_giornate=4,
        salva_excel=True,
        percentuale_presenze=0.375,
        file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
    )
