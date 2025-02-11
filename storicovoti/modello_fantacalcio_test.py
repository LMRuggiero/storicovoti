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
):
    duckdb.create_function(
        "voto_centrale",
        voto_centrale,
        [DOUBLE, DOUBLE, DOUBLE],
        DOUBLE
    )

    dataframe_finale = duckdb.query(f"""
            select
                *,
                dense_rank() over (partition by R order by FantaMedia desc, Media desc, Nome) as Posizione
            from (
                select distinct
                    Cod as Cod,
                    first(ruolo) over (partition by Cod order by stagione desc, giornata desc) as R,
                    first(Nome) over (partition by Cod order by stagione desc, giornata desc) as Nome,
                    first(Squadra) over (partition by Cod order by stagione desc, giornata desc) as Squadra,
                    count(1) over (partition by Cod) as Partite,
                    avg(Voto) over (partition by Cod) as Media,
                    avg(FantaVoto) over (partition by Cod) as FantaMedia,
                    avg(FantaVotoModP) over (partition by Cod) as FantaMediaModP
                from dataframe_filtrato
            )
            where partite >= {percentuale_presenze} * {numero_giornate}
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
