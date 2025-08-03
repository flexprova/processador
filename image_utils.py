# image_utils.py
import cv2
import numpy as np
from config import PPC, CBRD, ROI_HEIGHT, ROI_WIDTH, COLOR_DARK_GRAY, COLOR_LIGHT_GRAY

def draw_roi_grid(roi, width, height):
    """Plota Grid Imaginario da ROI (MODO DEBUG)."""
    for y in range(height):
        for x in range(width):
            x1 = PPC * x
            y1 = PPC * y
            x2 = x1 + PPC
            y2 = y1 + PPC
            # Celula Imaginaria
            cv2.rectangle(roi, (x1, y1), (x2, y2), COLOR_DARK_GRAY, 1)
            # Celula usada na Deteccao
            cv2.rectangle(roi, (x1 + CBRD, y1 + CBRD), (x2 - CBRD, y2 - CBRD), COLOR_LIGHT_GRAY, 1)

def process_cells(rect, width, height, mark_threshold, debug_enabled=False):
    """
    Processa as Celulas Contidas em um Retangulo e
    retorna uma lista de tuplas (x, y, marcada).
    """
    cells = []
    for y in range(height):
        for x in range(width):
            x1 = (x * PPC) + CBRD
            y1 = (y * PPC) + CBRD
            x2 = ((x * PPC) + PPC) - CBRD
            y2 = ((y * PPC) + PPC) - CBRD
            c = rect[y1:y2, x1:x2]
            sz = c.size
            nz = np.count_nonzero(c)
            fill_percentage = (nz * 100) / sz if sz > 0 else 0
            is_marked = int(fill_percentage > mark_threshold)
            if debug_enabled:
                print(f"        Celula: x={x} y={y} nonzero={nz} total={sz} fill={fill_percentage:.2f}% threshold={mark_threshold}%")
            cells.append((x, y, is_marked))
    return cells

def get_roi_from_image(img_gray):
    """
    Detecta e recorta a ROI de uma Imagem.
    Retorna a imagem da ROI corrigida em perspectiva.
    """
    # Aplica Gaussian blur
    img_blur = cv2.GaussianBlur(img_gray, (7, 7), 0)
    # Aplica Threshold adaptativo
    img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
    # Encontra os contornos da imagem
    contours, _ = cv2.findContours(img_threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Recupera todos os contornos que podem ser representados como poligonos de 4 lados (Quadrilateros)
    area_array = []
    approx_array = []

    # Para cada contorno detectado...
    for cnt in contours:
        # Aproxima contorno
        perim = 0.1 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, perim, True)
        # Se a aproximacao do contorno possuir 4 vertices inclui na array
        if len(approx) == 4:
            area_array.append(cv2.contourArea(approx))
            approx_array.append(approx)

    # Verifica se algum quadrilatero foi encontrado
    if not area_array:
        raise ValueError("Nenhum quadrilatero encontrado na imagem.")

    # Ordena array de quadrilateros pela area (da maior para a menor)
    sorted_data = sorted(zip(area_array, contours, approx_array), key=lambda x: x[0], reverse=True)

    # Recupera o quadrilatero da ROI [Isso precisa ser melhorado!]
    area, cnt, approx = sorted_data[0]

    # Corrige perspectiva do Quadrilatero da ROI
    pts = approx.reshape(4, 2)
    src_quad = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    src_quad[0] = pts[np.argmin(s)]
    src_quad[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    src_quad[1] = pts[np.argmin(diff)]
    src_quad[3] = pts[np.argmax(diff)]

    # Constroi array de destino
    wmax = PPC * ROI_WIDTH
    hmax = PPC * ROI_HEIGHT
    dst_array = np.array([[0, 0], [wmax - 1, 0], [wmax - 1, hmax - 1], [0, hmax - 1]], dtype="float32")

    # Calcula array de transformacao
    transform_array = cv2.getPerspectiveTransform(src_quad, dst_array)

    # Corrige a deformacao perspectiva a partir da array de transformacao
    img_roi = cv2.warpPerspective(img_gray, transform_array, (wmax, hmax))
    return img_roi

