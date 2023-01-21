from consigli_di_giornata import *
from titolari_e_panchinari import *

create = True

ultima_giornata = 17

l = range(min(ultima_giornata, 3), min(ultima_giornata + 1, 9))
if create:
    [consigli_di_giornata(ultima_giornata, n_giornate, salva_consigli=create, salva_modello=create, file_quotazioni="Quotazioni_Fantacalcio_Stagione_2022_23_01_11.xlsx") for n_giornate in l]


def consigli_di_giornata_formazione(ultima_giornata, n_giornate, lega, team='Io'):
    listone = pd.read_excel("Listone_produzione.xlsx")

    team = listone[(listone.Lega == lega) & (listone.Proprietario == team)].Nome.tolist()
    lista_nomi = '("' + '", "'.join(team) + '")'
    path = f"consigli_giornata/giornata_{ultima_giornata + 1}/consigli_ultime_{n_giornate}.xlsx"
    print(f"letto il file {path}")
    return pd.read_excel(path).query(f'Nome in {lista_nomi}').sort_values(
        ["FantaVoto", "FantaVotoPotenziale", "Voto", "VotoPotenziale"], ascending=(False, False, False, False))


dfs = [pd.read_excel(f"consigli_giornata/giornata_{ultima_giornata + 1}/consigli_ultime_{n}.xlsx") for n in l]

# dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "Fantacalcio Massa", "Io") for n in l]
# dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "Lega dei Cojon", "Io") for n in l]
dfs = [consigli_di_giornata_formazione(ultima_giornata, n, "FANTABERTEBOOM", "Io") for n in l]


squadra_titolare, panchinari, listone = titolari_e_panchinari3(
    dfs,
    num_df=6,
    esclusioni=["LOBOTKA"],
    # aggiunte=["TONALI"],
    # modulo=["3-4-3"],
    # modulo=["4-3-3"],
    # modulo=["4-4-2"],
    # modulo=["4-5-1"],
    # lista_giocatori_titolari=["MERET", "SKRINIAR", "UDOGIE", "KIM", "PASALIC", "LUIS ALBERTO", "PESSINA", "CANDREVA",
    #                           "LOZANO", "ARNAUTOVIC", "MARTINEZ L."]
)
print(squadra_titolare)
print(panchinari)
print(listone)
