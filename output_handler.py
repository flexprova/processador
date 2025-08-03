# output_handler.py
import csv

def write_output_csv(file_handle, data, add_header):
    """
    Grava o arquivo CSV de Saida.
    """
    # Ordena os dados pelo ID do objeto (coluna 2, convertida para int)
    try:
        data_sorted = sorted(data, key=lambda z: int(z[2]))
    except ValueError:
        # Se nao for possivel converter para int, ordena como string
        data_sorted = sorted(data, key=lambda z: z[2])

    writer = csv.writer(file_handle, delimiter=';', lineterminator='\n')
    if add_header:
        writer.writerow(['IMAGEM', 'GABARITO', 'ID_OBJETO', 'TIPO_OBJETO', 'ACERTO', 'LEITURA/STATUS'])

    for row in data_sorted:
        writer.writerow(row)

