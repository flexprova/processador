# ***********************************************************************
# *                                                                     *
# *                         EuCorrijo.com                               *
# *                                                                     *
# *                     Software Processador OMR                        *
# *                                                                     *
# *                      Versao UnB / 2017 0.1                          *
# *                                                                     *
# ***********************************************************************

from __future__ import print_function
import os
import sys
import csv
import cv2
import argparse as ap
import numpy as np
from matplotlib import pyplot as plt


# ******************************************************************************
# *                          Variaveis Globais                                 *
# ******************************************************************************

# Pixels por celula da ROI
ppc = 60

# Dimensoes da ROI ENEM
# roi_height = 34
# roi_width = 33

roi_height = 25
roi_width = 43

# Tamanho da borda da celula que sera ignorada pelo detector
cbrd = int( ppc * .17 )


# ******************************************************************************
# *                               Constantes                                   *
# ******************************************************************************

# Cores
color_black = (0,0,0)
color_white = (255,255,255)
color_gray = (127,127,127)
color_red = (255,0,0)
color_green = (0,255,0)
color_blue = (0,0,255)
color_pink = (255,0,255)
color_yellow = (255,255,0)
color_dark_gray = (64,64,64)
color_light_gray = (192,192,192)


# ******************************************************************************
# *            Controle de argumentos passados na linha de comando             *
# ******************************************************************************
def parseArguments():

    p = ap.ArgumentParser( description='Processador de Formularios OMR - Eucorrijo.com' )
    
    p.add_argument('-o',    '--output-file',     help='arquivo de saida (.csv)', default='-' )
    p.add_argument('-img',  '--input-image',     help='arquivo de imagem', default='' )
    p.add_argument('-dir',  '--image-directory', help='diretorio contendo multiplas imagens', default='' )
    p.add_argument('-tmpl', '--template-file',   help='arquivo de gabarito em formato .csv', default='' )
    p.add_argument('-hdr',  '--add-csv-header',  help='inclusao de cabecalho no arquivo de saida (.csv)', action='store_true', default=0 )
    p.add_argument('-mth',  '--mark-threshold',  help='porcentagem do preenchimento necessario para deteccao de uma marcacao (default: 50%%)', default=50 )
    p.add_argument('-dbg',  '--enable-debug',    help='habilita o modo de debug', action='store_true', default=0 )
    
    args = p.parse_args()

    return args    


# ******************************************************************************
# *                Plota Grid Imaginario da ROI (MODO DEBUG)                   *
# ******************************************************************************
def drawROIGrid( roi, x, y, w, h ):
    
    for y in range(h):
    
        for x in range(w):
    
            x1 = (ppc * x)
            y1 = (ppc * y)
            x2 = x1 + ppc
            y2 = y1 + ppc
    
            # Celula Imaginaria
            cv2.rectangle( roi, (x1,y1), (x2,y2), color_dark_gray, 1 )
            
            # Celula usada na Deteccao
            cv2.rectangle( roi, (x1 + cbrd,y1 + cbrd), (x2 - cbrd, y2 - cbrd), color_light_gray, 1 )


# ******************************************************************************
# *                      Grava o arquivo CSV de Saida                          *
# ******************************************************************************
def writeOutputCSV( f, data, hdr ):

    data = sorted( data, key=lambda z:int(z[2]) )

    wrtr = csv.writer( f, delimiter=';', lineterminator='\n' )

    if( hdr ):
        wrtr.writerow( [ 'IMAGEM', 'GABARITO', 'ID_OBJETO', 'TIPO_OBJETO', 'ACERTO', 'LEITURA/STATUS' ] );

    for d in data :
        wrtr.writerow( d )


# ******************************************************************************
# * Processa as Celulas Contidas em um Retangulo e                             *
# * retorna uma array bidimensional de booleanos                               *
# ******************************************************************************
def proccessCells( rect, w, h ):

    cells = []

    for y in range(h):

        for x in range(w):

            x1 = (x * ppc) + cbrd
            y1 = (y * ppc) + cbrd

            x2 = ((x * ppc) + ppc) - cbrd
            y2 = ((y * ppc) + ppc) - cbrd

            c = rect[ y1:y2, x1:x2 ]

            sz = c.size
            nz = np.count_nonzero( c )

            fl = (nz * 100) / sz

            if( g_debug_enabled ) :
                sys.stderr.write( "        Celula: x=%d y=%d nonzero=%d total=%d fill=%d%% threshold=%d%%\n" % (x, y, nz, sz, fl, g_mark_threshold) )

            cells.append( (x, y, int( fl > g_mark_threshold ) ) )

    return cells;


# ******************************************************************************
# *                       Identifica cada tipo de Objeto                       *
# ******************************************************************************
def parseObject( cells, tp ):

    n = 0;
    Id = '';

    #
    # Verificando o Identificador de Cartao
    #
    if ( tp == 'ID' ) :

        # Recupera identificador do cartao
        for x, y, value in cells :
            if ( x > 0 ) :
                Id = Id + str(int( value > 0 ))

        # Converte String para Inteiro usando base2
        return int( Id, 2 );

    #
    # Verificando o Objeto de Clock
    #
    if( tp == 'CLK' ) :

        # Verifica integridade da barra de clock
        for x, y, value in cells :
            if ( value == 0 ) :
                return 'INV'

        return 'OK'

    #
    # Tratamento de Respostas do tipo 'A'
    #
    if( tp == 'A' ) :

        # Verifica Integridade da resposta de tipo A
        for x, y, value in cells :
            if( value ):
                if ( x > 0 ) :
                    n = n + 1;

        # Verifica o nao preenchimento
        if( n == 0 ): return 'NP';

        # Verifica o preenchimento incorreto
        if( n > 1 ): return 'INV'

        # Le o preenchimento
        for x, y, value in cells :
            if ( value ) :
                if( (x,y) == (1,0) ): return 'C'
                if( (x,y) == (2,0) ): return 'E'

    #
    # Tratamento de Respostas do tipo 'B'
    #
    if( tp == 'B' ) :

        c = 0; d = 0; u = 0;

        # Verifica Integridade da resposta de tipo B
        for x, y, value in cells :
            if( value ) :
                for i in range( 10 ):
                    if( (x,y) == (1,i+2) ) : c = c + 1
                    if( (x,y) == (2,i+2) ) : d = d + 1
                    if( (x,y) == (3,i+2) ) : u = u + 1

        # Verifica o nao preenchimento
        if( (c == 0) and (d == 0) and (u == 0) ): return 'NP'

        # Verifica o preenchimento invalido
        if( (c == 0) or (d == 0) or (u == 0) ): return 'INV'

        # Verifica o preenchimento invalido
        if( (c > 1) or (d > 1) or (u > 1) ): return 'INV'

        # Le o numero preenchido
        for x, y, value in cells :
            if( value ):
                for i in range( 10 ):
                    if( (x,y) == (1,i+2) ) : c = i * 100
                    if( (x,y) == (2,i+2) ) : d = i * 10
                    if( (x,y) == (3,i+2) ) : u = i

        # Retorna valor lido
        return str( c + d + u )

    #
    # Tratamento de Respostas do tipo C
    #
    if( tp == 'C' ):

        # Verifica Integridade do preenchimento da resposta de tipo C
        for x, y, value in cells :
            if ( value ) :
                if( x > 0 ) :
                    n = n + 1

        # Verifica o nao preenchimeto
        if( n == 0 ): return 'NP'

        # Verifica o preenchimento incorreto
        if( n > 1 ): return 'INV'

        # Le a resposta marcada
        for x, y, value in cells :
            if( value ):
                if( (x,y) == (1,0) ): return 'A'
                if( (x,y) == (2,0) ): return 'B'
                if( (x,y) == (3,0) ): return 'C'
                if( (x,y) == (4,0) ): return 'D'
                if( (x,y) == (5,0) ): return 'E'

    # Tipo de Objeto Desconhecido
    return 'ERR'


# ******************************************************************************
# *   Processa um objeto de um determindado tipo em uma                        *
# *   das coordenadas da ROI                                                   *
# ******************************************************************************
def proccessROIObject( roi, x, y, tp ):

    # Calcula dimensao em celulas da ROI conforme o tipo de questao
    if   ( tp == 'A'   ) : w = 3; h = 1;  cl = color_red
    elif ( tp == 'B'   ) : w = 4; h = 12; cl = color_green
    elif ( tp == 'C'   ) : w = 6; h = 1;  cl = color_blue
    elif ( tp == 'ID'  ) : w = 16; h = 1; cl = color_yellow
    elif ( tp == 'CLK' ) : w = 1; h = 3; cl = color_pink
    else:
        return 'ERR';

    # Converte Coordenadas da ROI para coordenadas da Imagem
    x1 = (x * ppc)
    y1 = (y * ppc)
    x2 = x1 + (w * ppc)
    y2 = y1 + (h * ppc)

    # Recorta da ROI apenas a regiao onde esta a questao a ser processada
    obj = roi[ y1:y2, x1:x2 ]

    # Exibe Retangulo de Trabalho (DEBUG)
    if( g_debug_enabled and g_input_file ):
        cv2.rectangle( roi_debug, (x1,y1), (x2,y2), cl, 3 )

    # Transforma o Retangulo com a ROI da questao em uma array contendo os resultados processados
    cells = proccessCells( obj, w, h );

    # Efetua o parser de um objeto ROI
    data = parseObject( cells, tp )

    return data;


# ******************************************************************************
# * Processa a ROI de acordo com os objetos contido no arquivo CSV             *
# ******************************************************************************
def startProcessor( roi, csvfile, imgfile ):

    res = []

    if( g_debug_enabled ) :
        sys.stderr.write("Processando imagem/template: imagem='%s', template='%s'\n" % ( imgfile, csvfile ))

    # Aplica Threshold na imagem corrigida
    _,roi_seg = cv2.threshold( roi, 127, 255, cv2.THRESH_BINARY_INV )

    # Abre o arquivo CSV contendo a lista de objetos
    f = open( csvfile , 'rt' )

    # Carrega Dados do arquivo de Gabarito
    template = csv.reader( f, delimiter=';' )

    # Para cada objeto contido no CSV...
    for obj in template:

        n, tp, ca, x, y = obj;

        if( g_debug_enabled ) :
            sys.stderr.write("    Processando Objeto: n=%s, tp=%s, x=%s, y=%s\n" % ( n, tp, x, y ))

        a = proccessROIObject( roi_seg, int(x), int(y), tp )

        res.append( ( imgfile, csvfile, n, tp, int( a == ca ), a ) )

    # Fecha Arquivo CSV
    f.close()

    return res;


# ******************************************************************************
# *                     Detecta e recorta a ROI de uma Imagem                  *
# ******************************************************************************
def getROIFromImage( img_gray ):

    # Aplica Median Blur (Smoothing)
#    img_blur = cv2.blur( img_gray, (3,3) )
        # Aplica Gaussian blur
        img_blur = cv2.GaussianBlur( img_gray, (7,7), 0 )

    # Aplica Threshold na imagem
#    ret,img_threshold = cv2.threshold( img_blur, 127, 255, cv2.THRESH_TOZERO_INV )

# Como houve significativas diferencas de luminosidade em regioes de uma mesma foto, optou-se por outro Threshold.
# 15 (sempre impar!) Representa o tamanho da vizinhanca de cada pixel a analisar
# 3 representa quanto abaixo da media calculada na vizinhanca devera ser considerado 0 apos treshold.
#threshold = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
        img_threshold = cv2.adaptiveThreshold( img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
                

    # Encontra os contornos da imagem
        contours,hierarchy = cv2.findContours( img_threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE )

    # Recupera todos os contornos que podem ser representados como poligonos de 4 lados (Quadrilateros)
        area_array = []
        approx_array = []

    # Para cada contorno detectado...
        for cnt in contours:

        # Aproxima contorno
            perim = 0.1 * cv2.arcLength( cnt, True )
            approx = cv2.approxPolyDP( cnt, perim, True )

        # Se a aproximacao do contorno possuir 4 vertices inclui na array
            if len(approx) == 4:
                area_array.append(cv2.contourArea(approx))
                approx_array.append(approx)

    # Ordena array de quadrilateros pela area (da maior para a menor)
        srt = sorted( zip( area_array, contours, approx_array ), key=lambda x:x[0], reverse=True )

    # Recupera o quadrilatero da ROI [Isso precisa ser melhorado!]
        area,cnt,approx = srt[0]

    # Corrige perspectiva do Quadrilatero da ROI
        pts = approx.reshape( 4, 2 )
        src_quad = np.zeros( (4, 2), dtype = "float32" )

        s = pts.sum(axis = 1)
        src_quad[0] = pts[ np.argmin(s) ]
        src_quad[2] = pts[ np.argmax(s) ]

        diff = np.diff(pts, axis = 1)
        src_quad[1] = pts[ np.argmin(diff) ]
        src_quad[3] = pts[ np.argmax(diff) ]

    # Constroi array de destino
        wmax = ppc * roi_width
        hmax = ppc * roi_height

        dst_array = np.array( [ [0, 0], [wmax - 1, 0], [wmax - 1, hmax - 1], [0, hmax - 1] ], dtype = "float32" )

    # Calcula array de transformacao
        trnsfrm_array = cv2.getPerspectiveTransform( src_quad, dst_array )

    # Corrige a deformacao perspectiva a partir da array de transformacao
        img_roi = cv2.warpPerspective( img_gray, trnsfrm_array, (wmax, hmax) )

        return img_roi;


# ******************************************************************************
# *                                      MAIN                                  *
# ******************************************************************************

# Inicializa variaveis globais atraves dos argumentos passados na linha de comado
args = parseArguments()

g_debug_enabled = args.enable_debug
g_template_file = args.template_file 
g_input_file = args.input_image
g_input_directory = args.image_directory
g_output_file = args.output_file
g_add_csv_header = args.add_csv_header
g_mark_threshold = int(args.mark_threshold)


# Verifica se o arquivo de template eh valido
try:
    open( g_template_file, 'r' ).close()
except IOError:
    sys.stderr.write( "FATAL: Erro abrindo arquivo de template para leitura: %s\n" % g_template_file );
    sys.exit(1)


# Determina o stream que sera usado pelo arquivo de saida
f = sys.stdout
if ( g_output_file and g_output_file != '-' ) :
    try:
        f = open( g_output_file, 'w' )
    except IOError:
        sys.stderr.write( "FATAL: Erro abrindo arquivo de saida para gravacao: %s\n" % g_output_file );
        sys.exit(1)


# Processando um Arquivo isolado
if( g_input_file ):

    # Carrega imagem original em tons de cinza (novo formato)
#        img_input = cv2.cvtColor( g_input_file, cv2.COLOR_BGR2GRAY)
    
    # Carrega imagem original em tons de cinza
    img_input = cv2.imread( g_input_file, cv2.IMREAD_GRAYSCALE )
#        img_input = cv2.cvtColor( img_input_, cv2.COLOR_BGR2GRAY)

    
    # Verifica se a imagem foi carregada
    if( img_input is None ) :
        sys.stderr.write( "FATAL: Erro abrindo arquivo de imagem para leitura: %s\n" % g_input_file );
        sys.exit(1)

    # Detecta e Recupera a ROI contida na imagem
    img_roi = getROIFromImage( img_input );

    # DEBUG
    if ( g_debug_enabled ):
        # Converte ROI de GRAYSCALE para RGB (DEBUG)
        roi_debug = cv2.cvtColor( img_roi, cv2.COLOR_GRAY2BGR )
        cv2.bitwise_not( roi_debug, roi_debug )
        drawROIGrid( roi_debug, 0, 0, roi_width, roi_height );

    # Processa imagem
    res = startProcessor( img_roi, g_template_file, g_input_file )

    # Gera Saida
    writeOutputCSV( f, res, g_add_csv_header )

# Processando diretorio (Batch Processing - NAO RECURSIVO!!!)
elif( g_input_directory ):
    
    # Processa Diretorio de Imagens
    for fname in os.listdir( g_input_directory ): 
    
        # Verifica se o arquivo nao eh uma imagem suportada
        if( not( fname.endswith(".tif") or fname.endswith(".png") or fname.endswith(".jpeg") or fname.endswith(".JPG") or fname.endswith(".jpg") ) ):
            continue

        # Monta o path da imagem
        imgpath = g_input_directory + '/' + fname
    
        #  Carrega imagem original em tons de cinza
        img_input = cv2.imread( imgpath, cv2.IMREAD_GRAYSCALE )

        # Verifica se a imagem foi carregada
        if( img_input is None ) :
            sys.stderr.write( "WARNING: Erro carregando arquivo de imagem: %s\n" % imgpath );
            continue;

        # Detecta e Recupera a ROI contida na imagem
        img_roi = getROIFromImage( img_input );

        # Processa imagem
        res = startProcessor( img_roi, g_template_file, imgpath )

        # Gera Saida
        writeOutputCSV( f, res, g_add_csv_header )
        
        # Desabilita header depois do primeiro registro
        g_add_csv_header = 0;


# Fecha arquivo CSV de saida
f.close()

# DEBUG - somente para imagens isoladas
if ( (not g_debug_enabled) or (g_input_directory) ):
    sys.exit(0)


# ******************************************************************************
# *                                      DEBUG                                 *
# ******************************************************************************

# DEBUG - Exibe Processamento passo-a-passo
tit = plt.figure()
# tit.canvas.set_window_title('DEBUGGER')

# DEBUG - Monta array com as imagens e suas respectivas descricoes
images = [ ('INPUT IMAGE',img_input),
           ('ROI',img_roi),
           ('DEBUG IMAGE',roi_debug) ]

# DEBUG - Monta grid com as imagens
i = 0
for title,img in images:
    plt.subplot( 1, 3, i + 1 )
    plt.imshow( img,'gray' )
    plt.title( title )
    i = i + 1

# DEBUG - Exibe janela com as imagens
plt.show()

# ******************************************************************************
# $Id: Processador_CEM404.py 464 2016-07-10 03:12:49Z tiago.ventura $
