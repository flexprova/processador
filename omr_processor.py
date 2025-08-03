# omr_processor.py
import cv2
import csv
from config import PPC, COLOR_RED, COLOR_GREEN, COLOR_BLUE, COLOR_YELLOW, COLOR_PINK
from image_utils import process_cells

# Mapeamento de cores para tipos de objeto (usado no debug)
TYPE_COLORS = {
    'A': COLOR_RED,
    'B': COLOR_GREEN,
    'C': COLOR_BLUE,
    'ID': COLOR_YELLOW,
    'CLK': COLOR_PINK
}

def parse_object(cells, obj_type):
    """
    Identifica cada tipo de Objeto com base nas celulas marcadas.
    Retorna o valor interpretado ou um codigo de status (NP, INV, ERR).
    """
    # Inicializa variaveis locais
    n = 0
    binary_id = ''

    # Verificando o Identificador de Cartao
    if obj_type == 'ID':
        # Recupera identificador do cartao (ignora a primeira coluna x=0)
        for x, y, value in cells:
            if x > 0:
                binary_id += str(int(value > 0))
        # Converte String binaria para Inteiro
        try:
            return int(binary_id, 2)
        except ValueError:
            return 'ERR' # Caso a string binaria seja invalida

    # Verificando o Objeto de Clock
    if obj_type == 'CLK':
        # Verifica integridade da barra de clock (todas devem estar marcadas)
        for x, y, value in cells:
            if value == 0:
                return 'INV'
        return 'OK'

    # Tratamento de Respostas do tipo 'A'
    if obj_type == 'A':
        # Conta marcacoes (ignora a primeira coluna x=0)
        for x, y, value in cells:
            if value:
                if x > 0:
                    n += 1
        # Verifica o nao preenchimento
        if n == 0:
            return 'NP'
        # Verifica o preenchimento incorreto
        if n > 1:
            return 'INV'
        # Le o preenchimento
        for x, y, value in cells:
            if value:
                if (x, y) == (1, 0):
                    return 'C'
                if (x, y) == (2, 0):
                    return 'E'
        # Se chegou aqui e tinha uma marcacao, mas nao nas posicoes esperadas
        return 'INV'

    # Tratamento de Respostas do tipo 'B'
    if obj_type == 'B':
        c, d, u = 0, 0, 0
        # Verifica Integridade da resposta de tipo B
        # Espera-se uma marcacao em cada coluna (1, 2, 3) nas linhas 2-11
        for x, y, value in cells:
            if value:
                for i in range(10): # i de 0 a 9 -> y de 2 a 11
                    if (x, y) == (1, i + 2):
                        c += 1
                    if (x, y) == (2, i + 2):
                        d += 1
                    if (x, y) == (3, i + 2):
                        u += 1
        # Verifica o nao preenchimento
        if (c == 0) and (d == 0) and (u == 0):
            return 'NP'
        # Verifica o preenchimento invalido (alguma coluna sem marcacao ou com mais de uma)
        if (c == 0) or (d == 0) or (u == 0) or (c > 1) or (d > 1) or (u > 1):
            return 'INV'
        # Le o numero preenchido
        c_val, d_val, u_val = 0, 0, 0
        for x, y, value in cells:
            if value:
                for i in range(10):
                    if (x, y) == (1, i + 2):
                        c_val = i * 100
                    if (x, y) == (2, i + 2):
                        d_val = i * 10
                    if (x, y) == (3, i + 2):
                        u_val = i
        # Retorna valor lido como string
        return str(c_val + d_val + u_val)

    # Tratamento de Respostas do tipo 'C'
    if obj_type == 'C':
        # Conta marcacoes (ignora a primeira coluna x=0)
        for x, y, value in cells:
            if value:
                if x > 0:
                    n += 1
        # Verifica o nao preenchimento
        if n == 0:
            return 'NP'
        # Verifica o preenchimento incorreto
        if n > 1:
            return 'INV'
        # Le a resposta marcada
        for x, y, value in cells:
            if value:
                if (x, y) == (1, 0):
                    return 'A'
                if (x, y) == (2, 0):
                    return 'B'
                if (x, y) == (3, 0):
                    return 'C'
                if (x, y) == (4, 0):
                    return 'D'
                if (x, y) == (5, 0):
                    return 'E'
        # Se chegou aqui e tinha uma marcacao, mas nao nas posicoes esperadas
        return 'INV'

    # Tipo de Objeto Desconhecido
    return 'ERR'

def process_roi_object(roi_segmented, x, y, obj_type, mark_threshold, debug_enabled=False, debug_img=None):
    """
    Processa um objeto de um determinado tipo em uma das coordenadas da ROI.
    Retorna o valor interpretado.
    """
    # Calcula dimensao em celulas da ROI conforme o tipo de questao
    dimensions = {
        'A': (3, 1),
        'B': (4, 12),
        'C': (6, 1),
        'ID': (16, 1),
        'CLK': (1, 3)
    }

    if obj_type not in dimensions:
        return 'ERR'

    w, h = dimensions[obj_type]
    color = TYPE_COLORS.get(obj_type, (0, 0, 0))

    # Converte Coordenadas da ROI para coordenadas da Imagem
    x1 = x * PPC
    y1 = y * PPC
    x2 = x1 + (w * PPC)
    y2 = y1 + (h * PPC)

    # Recorta da ROI apenas a regiao onde esta a questao a ser processada
    obj_roi = roi_segmented[y1:y2, x1:x2]

    # Exibe Retangulo de Trabalho (DEBUG)
    if debug_enabled and debug_img is not None:
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 3)

    # Transforma o Retangulo com a ROI da questao em uma lista contendo os resultados processados
    cells = process_cells(obj_roi, w, h, mark_threshold, debug_enabled)

    # Efetua o parser de um objeto ROI
    data = parse_object(cells, obj_type)
    return data

def start_processor(roi, template_file, image_file, mark_threshold, debug_enabled=False, debug_img=None):
    """
    Processa a ROI de acordo com os objetos contidos no arquivo CSV.
    Retorna uma lista de resultados.
    """
    results = []
    if debug_enabled:
        print(f"Processando imagem/template: imagem='{image_file}', template='{template_file}'")

    # Aplica Threshold na imagem corrigida (ROI)
    _, roi_segmented = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY_INV)

    # Abre o arquivo CSV contendo a lista de objetos
    try:
        with open(template_file, 'rt') as f:
            template_reader = csv.reader(f, delimiter=';')
            # Para cada objeto contido no CSV...
            for obj in template_reader:
                if len(obj) < 5:
                     # Ignora linhas incompletas
                     continue
                n, tp, ca, x, y = obj
                if debug_enabled:
                    print(f"    Processando Objeto: n={n}, tp={tp}, x={x}, y={y}")
                # Processa o objeto
                parsed_value = process_roi_object(roi_segmented, int(x), int(y), tp, mark_threshold, debug_enabled, debug_img)
                # Adiciona resultado (imagem, template, id_objeto, tipo_objeto, acerto, leitura/status)
                results.append((image_file, template_file, n, tp, int(parsed_value == ca), parsed_value))
    except IOError as e:
        print(f"FATAL: Erro lendo arquivo de template: {e}", file=sys.stderr)
        raise

    return results

