import pandas as pd

from root import ROOT_DIR
from storicovoti.consigli_di_giornata_test import *
from storicovoti.titolari_e_panchinari import *

create = False
stagione = 23
ultima_giornata = 34
# l = range(min(ultima_giornata, 3), min(ultima_giornata + 1, 9))
l = range(3, 9)
if create:
    leggi(stagione, create=True)
    root = ROOT_DIR
    percorso = f"{ROOT_DIR}/Voti_Fantacalcio"
    nomi_excel: list = [file for (_, _, file) in os.walk(percorso)][0]
    nomi_excel.reverse()

    percorsi_excel = [f"{ROOT_DIR}/Voti_Fantacalcio/{n}" for n in nomi_excel if
                      f"20{stagione}_{stagione + 1}" in n or f"20{stagione - 1}_{stagione}" in n]

    lista_dataframe = [dataframe_corretto(ex) for ex in percorsi_excel]
    season_df = pd.concat([leggi(s, create=False) for s in range(stagione - 1, stagione + 1)])
    season = duckdb.query(f"""
        select
            *,
            --dense_rank() over (partition by squadra order by stagione desc, data desc) as GIORNATA_CALCOLATA,
            dense_rank() over (partition by avversario order by stagione desc, data desc) as GIORNATA_CALCOLATA_AVVERSARI
        from (
            select Data, HomeTeam as SQUADRA, AwayTeam as AVVERSARIO, giornata, stagione
            from season_df
            union all
            select Data, AwayTeam as SQUADRA, HomeTeam as AVVERSARIO, giornata, stagione
            from season_df
        )
        where stagione = '{stagione - 1}{stagione}'
        or giornata <= {ultima_giornata}
        """).df()

    dataframe_arricchito = pd.concat([
        duckdb.query(f"""
            select *
            from df
            join season s
             on df.squadra = s.squadra
            and df.giornata = s.giornata
            and df.stagione = s.stagione
            """).df() for df in lista_dataframe])

    dataframe_arricchito_finale = duckdb.query("""
        select
            *,
            dense_rank() over (partition by nome order by stagione desc, giornata desc) giornata_giocatore
        from dataframe_arricchito
    """)
    [consigli_di_giornata_test(ultima_giornata,
                          n_giornate,
                          stagione,
                          dataframe_arricchito_finale,
                          salva_consigli=create,
                          salva_modello=create,
                          # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2023_24_15_09_23.xlsx"
                          )
     for n_giornate in l]


def consigli_di_giornata_formazione(ultima_giornata, n_giornate, lega, team='Io'):
    listone = pd.read_excel("sorgenti/Listone_produzione.xlsx")

    team = listone[(listone.Lega == lega) & (listone.Proprietario == team)].Nome.tolist()
    lista_nomi = '("' + '", "'.join(team) + '")'
    path = f"{ROOT_DIR}/estrazioni/consigli_giornata_test/giornata_{ultima_giornata + 1}/consigli_ultime_{n_giornate}.xlsx"
    print(f"letto il file {path}")
    return pd.read_excel(path).query(f'Nome in {lista_nomi}').sort_values(
        ["FantaVoto", "FantaVotoPotenziale", "Voto", "VotoPotenziale"], ascending=(False, False, False, False))


dfs = [pd.read_excel(f"estrazioni/consigli_giornata_test/giornata_{ultima_giornata + 1}/consigli_ultime_{n}.xlsx") for n in
       l]

dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "Fantacalcio Massa", "Io") for n in l]
# dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "FantaRoars", "Io") for n in l]

squadra_titolare, panchinari, listone = titolari_e_panchinari3(
    dfs,
    num_df=6,
    esclusioni=["DIA"],
    # aggiunte=["DYBALA"],
    # modulo=["3-4-3"],
    # modulo=["3-5-2"],
    # modulo=["4-3-3"],
    # modulo=["4-4-2"],
    # modulo=["4-5-1-"],
    # lista_giocatori_titolari=["MERET", "SKRINIAR", "UDOGIE", "KIM", "PASALIC", "LUIS ALBERTO", "PESSINA", "CANDREVA",
    #                           "LOZANO", "ARNAUTOVIC", "MARTINEZ L."]
)
print(squadra_titolare)
print(panchinari)
print(listone)
