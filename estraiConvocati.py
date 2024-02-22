from root import ROOT_DIR
from storicovoti.consigli_di_giornata import *
from storicovoti.titolari_e_panchinari import *

create = True
stagione = 23
ultima_giornata = 25
# l = range(min(ultima_giornata, 3), min(ultima_giornata + 1, 9))
l = range(3, 9)
if create:
    leggi(stagione, create=True)
    [consigli_di_giornata(ultima_giornata,
                          n_giornate,
                          stagione,
                          salva_consigli=create,
                          salva_modello=create,
                          # file_quotazioni=f"{ROOT_DIR}/sorgenti/Quotazioni_Fantacalcio_Stagione_2023_24_15_09_23.xlsx"
                          )
     for n_giornate in l]


def consigli_di_giornata_formazione(ultima_giornata, n_giornate, lega, team='Io'):
    listone = pd.read_excel("sorgenti/Listone_produzione.xlsx")

    team = listone[(listone.Lega == lega) & (listone.Proprietario == team)].Nome.tolist()
    lista_nomi = '("' + '", "'.join(team) + '")'
    path = f"{ROOT_DIR}/estrazioni/consigli_giornata/giornata_{ultima_giornata + 1}/consigli_ultime_{n_giornate}.xlsx"
    print(f"letto il file {path}")
    return pd.read_excel(path).query(f'Nome in {lista_nomi}').sort_values(
        ["FantaVoto", "FantaVotoPotenziale", "Voto", "VotoPotenziale"], ascending=(False, False, False, False))


dfs = [pd.read_excel(f"estrazioni/consigli_giornata/giornata_{ultima_giornata + 1}/consigli_ultime_{n}.xlsx") for n in
       l]

dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "Fantacalcio Massa", "Io") for n in l]
# dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "FantaRoars", "Io") for n in l]

squadra_titolare, panchinari, listone = titolari_e_panchinari3(
    dfs,
    num_df=6,
    # esclusioni=["SCAMACCA"],
    # aggiunte=["IBRAHIMOVIC"],
    # modulo=["3-4-3"],
    # modulo=["3-5-2"],
    modulo=["4-3-3"],
    # modulo=["4-4-2"],
    # modulo=["4-5-1-"],
    # lista_giocatori_titolari=["MERET", "SKRINIAR", "UDOGIE", "KIM", "PASALIC", "LUIS ALBERTO", "PESSINA", "CANDREVA",
    #                           "LOZANO", "ARNAUTOVIC", "MARTINEZ L."]
)
print(squadra_titolare)
print(panchinari)
print(listone)
