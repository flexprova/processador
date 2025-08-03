# **************************************************************************
# *                                                                        *
# *                            EuCorrijo.com                               *
# *                                                                        *
# *                        Software Processador OLAP                       *
# *                                                                        *
# *                     Versao CEM404 / 2o Bim / 2016                      *
# *                                                                        *
# **************************************************************************
# * $Id: Conversor_OLAP_CEM404.py 461 2016-07-10 00:06:19Z tiago.ventura $ *
# **************************************************************************

import sys
import csv
import argparse as ap


# **********************************************************************
# *  Variaveis Globais                                                 *
# **********************************************************************

# Parametros
qtd_questoes = 92

# Arrays
keylst = []
output_data = []
input_data = []


# **********************************************************************
# *  Tratamento dos parametros passados na linha de comando            *
# **********************************************************************

p = ap.ArgumentParser( description='Conversor OLAP - Eucorrijo.com' )

p.add_argument('-i',      '--input-file',     help='arquivo de entrada (.csv)' )
p.add_argument('-o',      '--output-file',    help='arquivo de saida (.csv)', default='-' )
p.add_argument('-ihdr',   '--ignore-header',  help='ignora header do arquivo de entrada (.csv)', action='store_true', default=0 )
p.add_argument('-addhdr', '--add-header',     help='inclui header no arquivo de saida (.csv)', action='store_true', default=0 )

args = p.parse_args()

g_input_file = args.input_file
g_output_file = args.output_file
g_ignore_input_hdr = args.ignore_header
g_add_output_hdr = args.add_header


# **********************************************************************
# * Leitura e carga do arquivo de entrada                              *
# **********************************************************************

try:
	fin = open( g_input_file , 'r' )
except IOError:
	sys.stderr.write( "FATAL: Erro abrindo arquivo de entrada para leitura: %s\n" % g_input_file );
	sys.exit(1)

# Cria um leitor de arquivos CSV
reader = csv.reader( fin, delimiter=';' )

# Ignora header do arquivo de entrada
if( g_ignore_input_hdr == 1 ):
	next(reader)

# Copia conteudo do arquivo de entrada para uma array
for reg in reader:
	input_data.append( reg ) 

# Fecha arquivo de entrada
fin.close()


# **********************************************************************
# * Processamento e Conversao dos dados                                *
# **********************************************************************

# Para cada registro no CSV de entrada 
for reg in input_data:
	img, tmpl = reg[:2]
	keylst.append( ( img, tmpl )  )

# garante unicidade da chave 
uniqlst = set(keylst)

# Para cada chave...
for key in uniqlst:

	# Atomos
	atoms = []
	for i in range( qtd_questoes + 2 ):
		atoms.append('?')

	# Para cada registro no CSV de entrada...
	for reg in input_data:
	
		img, tmpl, nstr, tp, _, m = reg
	
		# Recupera as n questoes, o clock e o ID de cada chave  
		if( key == ( img, tmpl ) ):
			
			try: 
				n = int(nstr)
			except ValueError:
				continue;
			
			if( n == 0 ):
				if( tp == 'CLK' ) : atoms[ 0 ] = m
				if( tp == 'ID' ) : atoms[ 1 ] = m
			else:
				atoms[ n + 1 ] = m
	
	# monta array de saida
	output_data.append( key + tuple(atoms) )


# **********************************************************************
# * Geracao do Arquivo de Saida                                        *
# **********************************************************************

# Abre arquivo de saida para gravacao
fout = sys.stdout
if ( g_output_file and g_output_file != '-' ) :
	try:
		fout = open( g_output_file , 'wt' )
	except IOError:
		sys.stderr.write( "FATAL: Erro abrindo arquivo de saida para gravacao: %s\n" % g_output_file );
		sys.exit(1)

# Constroi um gravador de CSV
wrtr = csv.writer( fout, delimiter=';', lineterminator='\n' )

# Monta cabecalho
if( g_add_output_hdr == 1 ):
	hdr = [ 'IMAGEM','TEMPLATE','CLOCK', 'ID' ]

	for i in range( qtd_questoes ):
		hdr.append( 'Q' + str(i+1) )

	wrtr.writerow(  hdr );

# Grava os registros das array de saida em formato CSV
for reg in output_data :
	wrtr.writerow( reg )

# Fecha arquivo de saida
fout.close()

# ******************************************************************************
# $Id: Conversor_OLAP_CEM404.py 461 2016-07-10 00:06:19Z tiago.ventura $
