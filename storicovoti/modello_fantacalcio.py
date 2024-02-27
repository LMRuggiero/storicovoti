import os

import duckdb

from utils.metodi import *
from root import ROOT_DIR

pd.options.mode.chained_assignment = None


def modello_fantacalcio(
        giornata_esaminata,
        numero_giornate,
        dataframe_filtrato,
        salva_excel=False,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    statistiche = duckdb.query("""
        select
            Cod as Cod,
            Nome as Nome,
            ruolo as R,
            count(1) as Partite,
            avg(Voto) as Media,
            avg(FantaVoto) as FantaMedia,
            first(Squadra) as Squadra,
            list(voto) as Voti,  
            list(fantavoto) as FantaVoti
        from dataframe_filtrato
        group by Cod, Nome, R
        """).df()
    statistiche["VotoCentrale"] = statistiche.Voti.apply(voto_centrale)
    statistiche["FantaVotoCentrale"] = statistiche.FantaVoti.apply(voto_centrale)
    statistiche["VotoTroncato"] = statistiche.Media.apply(voto_troncato)
    statistiche["FantaVotoTroncato"] = statistiche.FantaMedia.apply(voto_troncato)

    modello_fantacalcio = duckdb.query(f"""
    select
        Cod,
        R,
        Nome,
        Squadra,
        Partite,
        Media,
        FantaMedia,
        VotoCentrale,
        FantaVotoCentrale,
        dense_rank() over (partition by R order by FantaMedia desc, Media desc, Nome) as Posizione
    from statistiche
    where partite >= {percentuale_presenze} * {numero_giornate}
    order by R desc, FantaMedia desc, Media desc, Nome
    """).df()


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
        modello_fantacalcio[modello_fantacalcio.R == 'P'].to_excel(writer, index=False, sheet_name='PORTIERI')
        modello_fantacalcio[modello_fantacalcio.R == 'D'].to_excel(writer, index=False, sheet_name='DIFENSORI')
        modello_fantacalcio[modello_fantacalcio.R == 'C'].to_excel(writer, index=False, sheet_name='CENTROCAMPISTI')
        modello_fantacalcio[modello_fantacalcio.R == 'A'].to_excel(writer, index=False, sheet_name='ATTACCANTI')

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        print(
            f"salvato modello fantacalcio {giornata_esaminata} considerando le precedenti {numero_giornate} in {path_finale_modello_fantacalcio}")

    return modello_fantacalcio


if __name__ == "__main__":
    modello_fantacalcio(
        giornata_esaminata=19,
        numero_giornate=4,
        salva_excel=True,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
    )
