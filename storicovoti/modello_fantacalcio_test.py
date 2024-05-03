import os

import duckdb
from duckdb.typing import *

from utils.metodi import *
from root import ROOT_DIR

pd.options.mode.chained_assignment = None


def modello_fantacalcio_test(
        giornata_esaminata,
        numero_giornate,
        dataframe_filtrato,
        salva_excel=False,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
):
    duckdb.create_function(
        "voto_centrale",
        voto_centrale,
        [DOUBLE, DOUBLE, DOUBLE],
        DOUBLE
    )

    dataframe_finale = duckdb.query(f"""
        select
            Cod as Cod,
            ruolo as R,
            Nome as Nome,
            first(Squadra) as Squadra,
            count(1) as Partite,
            avg(Voto) as Media,
            avg(FantaVoto) as FantaMedia,
            voto_centrale(Media, min(Voto), max(Voto)) as VotoCentrale,
            voto_centrale(FantaMedia, min(FantaVoto), max(FantaVoto)) as FantaVotoCentrale,
            dense_rank() over (partition by R order by FantaMedia desc, Media desc, Nome) as Posizione
        from dataframe_filtrato
        group by Cod, Nome, R
        having partite >= {percentuale_presenze} * {numero_giornate}
        order by R desc, Posizione
        """).df()
    duckdb.remove_function("voto_centrale")
    if salva_excel:
        path_modello_fantacalcio = f"{ROOT_DIR}/estrazioni/modello_fantacalcio_test/giornata_{giornata_esaminata}"
        file_modello_fantacalcio = f"modello_fantacalcio_ultime_{numero_giornate}.xlsx"
        if not os.path.exists(path_modello_fantacalcio):
            os.makedirs(path_modello_fantacalcio)

        path_finale_modello_fantacalcio = os.path.join(path_modello_fantacalcio, file_modello_fantacalcio)

        # Create statistiche Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(path_finale_modello_fantacalcio, engine='xlsxwriter')

        # Write each dataframe to statistiche different worksheet.
        dataframe_finale.to_excel(writer, index=False, sheet_name='dataframe_finale')
        dataframe_finale[dataframe_finale.R == 'P'].to_excel(writer, index=False, sheet_name='PORTIERI')
        dataframe_finale[dataframe_finale.R == 'D'].to_excel(writer, index=False, sheet_name='DIFENSORI')
        dataframe_finale[dataframe_finale.R == 'C'].to_excel(writer, index=False, sheet_name='CENTROCAMPISTI')
        dataframe_finale[dataframe_finale.R == 'A'].to_excel(writer, index=False, sheet_name='ATTACCANTI')

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()

        print(
            f"salvato modello fantacalcio {giornata_esaminata} considerando le precedenti {numero_giornate} in {path_finale_modello_fantacalcio}")

    return dataframe_finale


if __name__ == "__main__":
    modello_fantacalcio_test(
        giornata_esaminata=19,
        numero_giornate=4,
        salva_excel=True,
        percentuale_presenze=0.375,
        # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2022_23.xlsx"
    )
