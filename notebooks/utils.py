import re
import pandas as pd

def procesar_span(span):
    span = re.sub("\s","",span[1:-1])
    if span:
        lista = span.split(",")
        lista = [int(index) for index in lista]
    else:
        lista = []
    return lista

def leer_csv(path):
    df = pd.read_csv(path)
    df["spans"] = df["spans"].apply(procesar_span)
    return df

def obtener_texto_toxico(row):
    toxico = []
    if row.spans: # Hay texto marcado como toxico
        diffs = np.diff(row.spans, prepend=row.spans[0]-1) #prepend para que el primer diff sea uno
        toxico = []
        indices_inicios = np.argwhere(diffs != 1).ravel() # indices de los inicios de las sigs palabras

        i = row.spans[0]
        for indice_next in indices_inicios:
            j = row.spans[indice_next-1] # fin de la anterior
            parte_toxica = row.text[i:j+1]
            toxico.append(parte_toxica)
            i = row.spans[indice_next]
            
        # Última parte
        j = row.spans[-1]
        parte_toxica = row.text[i:j+1]
        toxico.append(parte_toxica)

    return toxico

def quitar_espacios_de_spans(row):
    toxico = obtener_texto_toxico(row)
    toxic_span = "".join(toxico) # juntar texto tóxico
    toxic_match = set(re.findall(r"\W", toxic_span)) # encontrar cosas que no son letras, números o guión bajo
    # Inicialización
    buenos = row.spans
    indices = []
    
    for extraño in toxic_match: # Si no hay nada en toxic_match, no se itera
        extraño = re.escape(extraño) # escapando posibles caracteres con interpretación RegEx
        if extraño == "\ ":
            indice = re.finditer(extraño, toxic_span) 
            indices = [i.start() for i in indice] # Índices de espacios en el texto
    if indices:
        por_quitar = [row.spans[i] for i in indices] # spans tóxicos que son espacios
        buenos = [i for i in row.spans if i not in por_quitar] # filtrando
            
    return buenos

def separar_spans_toxicos(row):
    lists = []
    if row.spans:
        start = row.spans[0]
        end = row.spans[0]
        for i in range(1, len(row.spans)):
            #print(row.spans[i])
            end = row.spans[i]
            previous = row.spans[i-1] 
            if (end - previous) != 1: # Terminó un span, inició el otro
                lists.append(list(range(start,previous+1)))
                start = end

        # Agregando último span
        lists.append(list( range(start, end+1) ))
            
    return lists


def starts_ends_tokens(text):
    tokens = text.split()
    starts, ends = [], []
    start, end = 0, -2
    for idx, palabra in enumerate(tokens):
        starts.append(start) # start actual
        start += len(palabra) + 1 # start para la siguiente
        end   += len(palabra) + 1 # end actual
        ends.append(end)
    
    return starts, ends
    
    
def corregir_spans(row, umbral):
    starts, ends = starts_ends_tokens(row.text)
    
    toxicos = []
    if row.spans:
        indices_separados = separar_spans_toxicos(row)
        for separado in indices_separados: # iterando partes tóxicas 
            indices = separado
            for s, e in zip(starts, ends): # iterando "texto" por medio de los índices de palabras
                if separado[0] in range(s,e+1): # span está en una palabra
                    if separado != list(range(s, e+1)): # los spans no abarca toda la palabra
                        if len(separado)/(len(list(range(s, e+1)))) <= umbral:
                            indices = [] # mejor ni lo marques
                        else:
                            indices = list(range(s, e+1)) # ya márcate todo mejor
                    else:
                        break # la palabra está bien marcada, pasa a la siguiente parte tóxica
            toxicos.extend(indices)
    return toxicos


huevos = "si"