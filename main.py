# main.py
import sys
import os
import cv2
from matplotlib import pyplot as plt
from cli_parser import parse_arguments
from config import PPC, ROI_HEIGHT, ROI_WIDTH
from image_utils import get_roi_from_image, draw_roi_grid
from omr_processor import start_processor
from output_handler import write_output_csv

def main():
    # Inicializa variaveis globais atraves dos argumentos passados na linha de comando
    args = parse_arguments()

    # Verifica se o arquivo de template eh valido
    try:
        with open(args.template_file, 'r'):
            pass # Apenas verifica se consegue abrir
    except IOError:
        print(f"FATAL: Erro abrindo arquivo de template para leitura: {args.template_file}", file=sys.stderr)
        sys.exit(1)

    # Determina o stream que sera usado pelo arquivo de saida
    output_stream = sys.stdout
    if args.output_file and args.output_file != '-':
        try:
            output_stream = open(args.output_file, 'w')
        except IOError:
            print(f"FATAL: Erro abrindo arquivo de saida para gravacao: {args.output_file}", file=sys.stderr)
            sys.exit(1)

    # Flag para controlar se o cabecalho ja foi adicionado (importante para batch processing)
    header_added = args.add_csv_header

    # Processando um Arquivo isolado
    if args.input_image:
        # Carrega imagem original em tons de cinza
        img_input = cv2.imread(args.input_image, cv2.IMREAD_GRAYSCALE)
        # Verifica se a imagem foi carregada
        if img_input is None:
            print(f"FATAL: Erro abrindo arquivo de imagem para leitura: {args.input_image}", file=sys.stderr)
            sys.exit(1)

        try:
            # Detecta e Recupera a ROI contida na imagem
            img_roi = get_roi_from_image(img_input)
        except ValueError as e:
            print(f"FATAL: Erro ao detectar ROI na imagem {args.input_image}: {e}", file=sys.stderr)
            sys.exit(1)

        # DEBUG
        debug_img = None
        if args.enable_debug:
            # Converte ROI de GRAYSCALE para RGB (DEBUG)
            debug_img = cv2.cvtColor(img_roi, cv2.COLOR_GRAY2BGR)
            cv2.bitwise_not(debug_img, debug_img) # Inverte cores para melhor visualizacao
            draw_roi_grid(debug_img, ROI_WIDTH, ROI_HEIGHT)

        # Processa imagem
        results = start_processor(img_roi, args.template_file, args.input_image, args.mark_threshold, args.enable_debug, debug_img)

        # Gera Saida
        write_output_csv(output_stream, results, header_added)
        header_added = False # Desabilita header depois do primeiro registro

    # Processando diretorio (Batch Processing - NAO RECURSIVO!!!)
    elif args.image_directory:
        # Processa Diretorio de Imagens
        supported_extensions = ('.tif', '.png', '.jpeg', '.JPG', '.jpg')
        image_files = [f for f in os.listdir(args.image_directory) if f.endswith(supported_extensions)]

        if not image_files:
             print(f"WARNING: Nenhum arquivo de imagem suportado encontrado em: {args.image_directory}", file=sys.stderr)

        for fname in image_files:
            # Monta o path da imagem
            imgpath = os.path.join(args.image_directory, fname) # Usa os.path.join para compatibilidade
            # Carrega imagem original em tons de cinza
            img_input = cv2.imread(imgpath, cv2.IMREAD_GRAYSCALE)
            # Verifica se a imagem foi carregada
            if img_input is None:
                print(f"WARNING: Erro carregando arquivo de imagem: {imgpath}", file=sys.stderr)
                continue

            try:
                # Detecta e Recupera a ROI contida na imagem
                img_roi = get_roi_from_image(img_input)
            except ValueError as e:
                 print(f"WARNING: Erro ao detectar ROI na imagem {imgpath}: {e}", file=sys.stderr)
                 continue # Pula para a proxima imagem em caso de erro

            # Processa imagem (sem debug_img para batch)
            results = start_processor(img_roi, args.template_file, imgpath, args.mark_threshold, False, None)

            # Gera Saida
            write_output_csv(output_stream, results, header_added)
            header_added = False # Desabilita header depois do primeiro registro

    # Fecha arquivo CSV de saida se nao for stdout
    if output_stream != sys.stdout:
        output_stream.close()

    # DEBUG - somente para imagens isoladas
    if not args.enable_debug or args.image_directory:
        sys.exit(0)

    # ******************************************************************************
    # *                                      DEBUG                                 *
    # ******************************************************************************
    # DEBUG - Exibe Processamento passo-a-passo
    # tit = plt.figure()
    # tit.canvas.set_window_title('DEBUGGER')

    # DEBUG - Monta array com as imagens e suas respectivas descricoes
    images = [
        ('INPUT IMAGE', img_input),
        ('ROI', img_roi),
        ('DEBUG IMAGE', debug_img)
    ]

    # DEBUG - Monta grid com as imagens
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('DEBUGGER')

    for i, (title, img) in enumerate(images):
        if img is not None:
            # Converte BGR para RGB se necessario para matplotlib
            if len(img.shape) == 3 and img.shape[2] == 3:
                 img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                 img_rgb = img
            axes[i].imshow(img_rgb, cmap='gray' if len(img.shape) == 2 else None)
            axes[i].set_title(title)
            axes[i].axis('off') # Remove eixos para melhor visualizacao
        else:
             axes[i].text(0.5, 0.5, 'Imagem nao disponivel', ha='center', va='center')
             axes[i].set_title(title)
             axes[i].axis('off')

    # DEBUG - Exibe janela com as imagens
    plt.tight_layout(rect=[0, 0, 1, 0.95]) # Ajusta layout para caber o titulo
    plt.show()

if __name__ == "__main__":
    main()

