# config.py

# ******************************************************************************
# *                          Variaveis Globais                                 *
# ******************************************************************************
# Pixels por celula da ROI
PPC = 60
# Dimensoes da ROI ENEM
ROI_HEIGHT = 25 # Original: 34
ROI_WIDTH = 43  # Original: 33
# Tamanho da borda da celula que sera ignorada pelo detector
CBRD = int(PPC * 0.17)

# ******************************************************************************
# *                               Constantes                                   *
# ******************************************************************************
# Cores (BGR format for OpenCV)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (127, 127, 127)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_PINK = (255, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_LIGHT_GRAY = (192, 192, 192)

