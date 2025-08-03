# cli_parser.py
import argparse

def parse_arguments():
    """Analisa os argumentos passados na linha de comando."""
    parser = argparse.ArgumentParser(description='Processador de Formularios OMR - Eucorrijo.com')
    parser.add_argument('-o', '--output-file', help='arquivo de saida (.csv)', default='-')
    parser.add_argument('-img', '--input-image', help='arquivo de imagem', default='')
    parser.add_argument('-dir', '--image-directory', help='diretorio contendo multiplas imagens', default='')
    parser.add_argument('-tmpl', '--template-file', help='arquivo de gabarito em formato .csv', default='')
    parser.add_argument('-hdr', '--add-csv-header', help='inclusao de cabecalho no arquivo de saida (.csv)', action='store_true', default=False)
    parser.add_argument('-mth', '--mark-threshold', help='porcentagem do preenchimento necessario para deteccao de uma marcacao (default: 50%%)', default=50, type=int)
    parser.add_argument('-dbg', '--enable-debug', help='habilita o modo de debug', action='store_true', default=False)
    return parser.parse_args()

