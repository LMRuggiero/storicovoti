from storicovoti.modello_fantacalcio import *
from storicovoti.titolari_e_panchinari import *

create = True
stagione = 23
ultima_giornata = 21
# l = range(min(ultima_giornata, 3), min(ultima_giornata + 1, 9))
l = range(3, 9)
if create:
    [modello_fantacalcio(ultima_giornata,
                         n_giornate,
                         stagione,
                         salva_excel=create
                         )
     for n_giornate in l]


def modello_fantacalcio_formazione(ultima_giornata, n_giornate, lega, team='Io'):
    listone = pd.read_excel("sorgenti/Listone_produzione.xlsx")

    team = listone[(listone.Lega == lega) & (listone.Proprietario == team)].Nome.tolist()
    lista_nomi = '("' + '", "'.join(team) + '")'
    path = f"{ROOT_DIR}/estrazioni/modello_fantacalcio/giornata_{ultima_giornata}/modello_fantacalcio_ultime_{n_giornate}.xlsx"
    print(f"letto il file {path}")
    return pd.read_excel(path).query(f'Nome in {lista_nomi}').sort_values(
        ["FantaMedia", "Media"], ascending=(False, False))


dfs = [pd.read_excel(
    f"{ROOT_DIR}/estrazioni/modello_fantacalcio/giornata_{ultima_giornata}/modello_fantacalcio_ultime_{n}.xlsx") for n
       in l]

dfs = [modello_fantacalcio_formazione(ultima_giornata, n, "Fantacalcio Massa", "Io") for n in l]
# dfs = [modello_fantacalcio_formazione(ultima_giornata, n, "FantaRoars", "GliScappatiDiCasa") for n in l]

squadra_titolare, panchinari, listone = titolari_e_panchinari_modello3(
    dfs,
    num_df=6,
    # modulo=["3-4-3"],
    # modulo=["3-5-2"],
    # modulo=["4-3-3"],
    # modulo=["4-4-2"],
    # modulo=["5-3-2"],
    # lista_giocatori_titolari=["MERET", "SKRINIAR", "UDOGIE", "KIM", "PASALIC", "LUIS ALBERTO", "PESSINA", "CANDREVA",
    #                           "LOZANO", "ARNAUTOVIC", "MARTINEZ L."]
)
print(squadra_titolare, '\n')
print(panchinari, '\n')
print(listone)
