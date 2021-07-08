from PyPDF2 import PdfFileWriter, PdfFileReader
import io, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4

packet = io.BytesIO()
# create a new PDF with Reportlab
can = canvas.Canvas(packet, pagesize=A4)
can.drawString(100, 250, "Assinado Digitalmente por:")
can.drawString(100, 200, "Anderson Silva Fonseca")
can.drawString(100, 150, "email")
can.drawString(100, 100, time.strftime('%d/%m/%Y às %H:%M:%S', time.localtime()))
can.save()
#move to the beginning of the StringIO buffer
packet.seek(0)
new_pdf = PdfFileReader(packet)
# read your existing PDF
existing_pdf = PdfFileReader(open("original.pdf", "rb"))
output = PdfFileWriter()
# add the "watermark" (which is the new pdf) on the existing page
page = existing_pdf.getPage(0)
#page.mergePage(new_pdf.getPage(0))
for i in range(0,existing_pdf.getNumPages()):
    output.addPage(existing_pdf.getPage(i))
output.addPage(new_pdf.getPage(0))
# finally, write "output" to a real file
outputStream = open("destination.pdf", "wb")
output.write(outputStream)
outputStream.close()