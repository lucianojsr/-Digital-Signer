from flask import Flask, redirect, url_for, render_template, request, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
from PyPDF2 import PdfFileWriter, PdfFileReader
import io, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm
from reportlab.lib import colors 
import zlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from pathlib import Path
from hashlib import md5
import random
from flask_mysqldb import MySQL

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Frame


UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#Configurações do Banco de Dados
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '' 
app.config['MYSQL_DB'] = 'Assinador'

@app.route('/verifypdf', methods=['POST'])
def verify_pdf():
    # Verifica se esta enviando um arquivo
    if 'file' not in request.files:
        return "Nenhum Arquivo Enviado", 400
    file = request.files['file']

    # Se o usuário não enviar um arquivo, ele vai ta enviando um arquivo vazio
    if file.filename == '':
        flash('No selected file')
        return "Arquivo Vazio", 400

    #Se existe um arquivo e é um PDF, ele executa
    if file and allowed_file(file.filename):
        filename = secure_filename("temp.pdf")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        Hash = HashPdf(os.path.join(app.config['UPLOAD_FOLDER'], filename),IgnoreLastPage=1)
        ExtractTextFromLastpage(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template("Verificadorfinal.html",hash = Hash)

@app.route('/Verificador', methods=['GET'])
def Verificadorpage():
    return render_template("Verificador.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/Assinador', methods=['POST'])
def assinadorpage():
    print(request.form)
    return render_template("Assinador.html",name = request.form['name'],email = request.form['email'])

@app.route('/uploadpdf', methods=['POST'])
def upload_pdf():
    # Verifica se esta enviando um arquivo
    if 'file' not in request.files:
        return "Nenhum Arquivo Enviado", 400
    file = request.files['file']

    # Se o usuário não enviar um arquivo, ele vai ta enviando um arquivo vazio
    if file.filename == '':
        flash('No selected file')
        return "Arquivo Vazio", 400

    #Se existe um arquivo e é um PDF, ele executa
    if file and allowed_file(file.filename):
        filename = secure_filename("temp.pdf")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #Insere um novo usuário no BD
        UserId = GetUserId(request.form['name'],request.form['email'])
        #Recupera Chave Publica e Privada do Usuario(Criar caso não exista)
        #Gera Hash do PDF
        Hash = HashPdf(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #Criptografa o Hash
        encrypted_msg = encrypt(Hash,UserId) 
        #Assinar o PDF com o Hash Criptografado
        CriarAssinatura(os.path.join(app.config['UPLOAD_FOLDER'], filename),request.form['name'],request.form['email'],encrypted_msg)
        return render_template("Download_file.html", hash= Hash, pdf_name = file.filename)

        #return redirect(url_for('download_file', name=filename))

def CriarAssinatura(filepath,name, email,Hash):
    #Cria um PDF com Assinatura
    packet = io.BytesIO()
    # cria um novo PDF usando a bib Reportlab
    can = canvas.Canvas(packet, pagesize=A4)
    can.drawString(200, 800, "Assinado Digitalmente por:")
    can.drawString(200, 780, name)
    can.drawString(200, 770, email)
    can.drawString(200, 755, time.strftime('%d/%m/%Y às %H:%M:%S', time.localtime()))
    #can.drawString(100, 700, "Hash Criptografado:")
    #can.drawCentredString(A4[1]/2,690,Hash)
    yourStyle = ParagraphStyle('yourtitle',
                           fontName="Helvetica-Bold",
                           fontSize=9,
                           alignment=1,
                           spaceAfter=14)
    yourStyle2 = ParagraphStyle('yourtitle2',
                           fontName="Helvetica",
                           fontSize=9,
                           alignment=1,
                           spaceAfter=14)
    para2 = Paragraph("Hash Criptografado:", yourStyle2)
    para1 = Paragraph(Hash, yourStyle)
    frame = Frame(
                    200,     # x
                    400,     # y at bottom
                    200,     # width
                    300,     # height
                    showBoundary = 1  # helps us see what's going on
                    )
    #frame.add(para1,can)
    frame.addFromList([para2,para1],can)
    #can.drawString(100, 30, Hash)
    #Finalizou a pagina, Salvou
    can.save()
    #Movo para o inicio do arquivo
    packet.seek(0)
    #Ler o PDF criado usando a bib PdfFileReader
    new_pdf = PdfFileReader(packet)
    # Ler o PDF Existente
    existing_pdf = PdfFileReader(open(filepath, "rb"))
    #Criando o PDF resultante
    output = PdfFileWriter()
    #Copia as pags do pdf original para o pdf resultante 
    for i in range(0,existing_pdf.getNumPages()):
        output.addPage(existing_pdf.getPage(i))
    #Adiciona a pagina da assinatura
    output.addPage(new_pdf.getPage(0))
    # Salva o Arquivo
    outputStream = open(UPLOAD_FOLDER + "temp2.pdf" , "wb")
    output.write(outputStream)
    outputStream.close()
    return UPLOAD_FOLDER + "temp2.pdf" 

def generate_new_key_pair(UserId):
    #Gera chaves (publica/ privada) usando 4096 bits (512 bytes)
    new_key = RSA.generate(4096, e=65537)

    #Chave privada em formato PEM 
    private_key = new_key.exportKey("PEM")

    #Chave publica em formato PEM 
    public_key = new_key.publickey().exportKey("PEM")

    private_key_path = Path("UsersKeys/" + str(UserId) + '_private.pem')
    private_key_path.touch(mode=0o600)
    private_key_path.write_bytes(private_key)

    public_key_path = Path("UsersKeys/" + str(UserId) + '_public.pem')
    public_key_path.touch(mode=0o664)
    public_key_path.write_bytes(public_key)

    #Função de encriptação 
def encrypt_blob(blob, public_key):
    #Importa a Chave Publica e usa para encriptação usando PKCS1_OAEP
    rsa_key = RSA.importKey(public_key)
    rsa_key = PKCS1_OAEP.new(rsa_key)

    #comprime o dado primeiro
    blob = zlib.compress(blob)
    #Ao determinar o tamanho do bloco, determine o comprimento da chave privada usada em bytes
    #e subtrai 42 bytes (ao usar PKCS1_OAEP). Os dados serão criptografados
    #em blocos
    chunk_size = 470
    offset = 0
    end_loop = False
    encrypted = bytearray()

    while not end_loop:
        #O bloco
        chunk = blob[offset:offset + chunk_size]

        #Se o bloco de dados for menor que o tamanho do bloco, então precisamos adicionar
        #um preenchimento com "". Isso indica que chegamos ao final do arquivo
        #então terminamos o loop aqui
        if len(chunk) % chunk_size != 0:
            end_loop = True
            #chunk += b" " * (chunk_size - len(chunk))
            chunk += bytes(chunk_size - len(chunk))
        #Anexa o fragmento criptografado ao arquivo criptografado geral
        encrypted += rsa_key.encrypt(chunk)

        #Aumenta o deslocamento pelo tamanho do bloco
        offset += chunk_size

    #Codifica o arquivo criptografado em Base 64
    return base64.b64encode(encrypted)

#Função de Decriptação
def decrypt_blob(encrypted_blob, private_key):

    #Importa a Chave Publica e usa para decriptação usando PKCS1_OAEP
    rsakey = RSA.importKey(private_key)
    rsakey = PKCS1_OAEP.new(rsakey)

    #Decodifica da Base 64
    encrypted_blob = base64.b64decode(encrypted_blob)

    #Ao determinar o tamanho do bloco, determina-se o comprimento da chave privada usada, em bytes.
    #Os dados serão descriptografados em blocos
    chunk_size = 512
    offset = 0
    decrypted = bytearray()

    #Continua o loop enquanto tivermos blocos para decifrar
    while offset < len(encrypted_blob):
        #O Bloco
        chunk = encrypted_blob[offset: offset + chunk_size]

        #Anexa o bloco descriptografado ao arquivo descriptografado geral
        decrypted += rsakey.decrypt(chunk)

        #Aumenta o deslocamento pelo tamanho do bloco
        offset += chunk_size

    #retorna os dados descriptografados descompactados
    return zlib.decompress(decrypted)

#Criptografa o Hash salvando cada chave para cada usuário
def encrypt(hash, UserId):
    
    private_key = Path("UsersKeys/" + str(UserId) + '_private.pem')
    public_key = Path("UsersKeys/" + str(UserId) + '_public.pem')

    encrypted_msg = encrypt_blob(str.encode(hash), public_key.read_bytes())
    decrypted_msg = decrypt_blob(encrypted_msg, private_key.read_bytes())
    print (decrypted_msg)

    return encrypted_msg

#Gera ID para cada usuário e salva no BD
def GetUserId(Nome, Email):
    mysql = MySQL(app)
    cur = mysql.connection.cursor()
    cur.execute("SELECT Id FROM Users WHERE Nome = %s and Email = %s",(Nome,Email))
    data = cur.fetchone()
    cur.close()
    if not data:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Users(Nome, Email) VALUES (%s, %s)", (request.form['name'], request.form['email']))
        mysql.connection.commit()
        cur.close()
        cur = mysql.connection.cursor()
        cur.execute("SELECT Id FROM Users WHERE Nome = %s and Email = %s",(Nome,Email))
        data = cur.fetchone()
        generate_new_key_pair(data[0])
        cur.close()
    id = data[0]
    return id

#Gera o Hash para um arquivo 
def HashData(data):
    Hash=md5(str(data).encode('utf-8')).hexdigest()
    return Hash

#gera o Hash resultante do PDF  
def HashPdf(file,IgnoreLastPage = 0):
    existing_pdf = PdfFileReader(open(file, "rb"))
    #Criando o PDF resultante
    output = PdfFileWriter()
    #Copia as pags do pdf original para o pdf resultante 
    for i in range(0,existing_pdf.getNumPages()-IgnoreLastPage):
        output.addPage(existing_pdf.getPage(i))
    outputStream = open(UPLOAD_FOLDER + "StreamCript.pdf" , "wb")
    output.write(outputStream)
    outputStream.close()
    f=open(UPLOAD_FOLDER + "StreamCript.pdf" ,"rb")
    data=f.read()
    f.close()
    return HashData(data)

@app.route('/download_file/<pdf_name>', methods=['GET'])
def download_file(pdf_name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], "temp2.pdf", attachment_filename= os.path.splitext(pdf_name)[0] +'_Assinado.pdf', as_attachment=True)

def ExtractTextFromLastpage(filename):
    pdf_file = open(filename, 'rb')
    read_pdf = PdfFileReader(pdf_file)
    number_of_pages = read_pdf.getNumPages()-1
    page = read_pdf.getPage(number_of_pages)
    page_content = page.extractText()
    print (page_content.encode('utf-8'))

if __name__ == "__main__" :
    app.run()