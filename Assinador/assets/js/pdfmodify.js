var filename = 'novodocumento'

function ParseURLParams(url) {
    var queryStart = url.indexOf("?") + 1,
        queryEnd   = url.indexOf("#") + 1 || url.length + 1,
        query = url.slice(queryStart, queryEnd - 1),
        pairs = query.replace(/\+/g, " ").split("&"),
        parms = {}, i, n, v, nv;

    if (query === url || query === "") return;

    for (i = 0; i < pairs.length; i++) {
        nv = pairs[i].split("=", 2);
        n = decodeURIComponent(nv[0]);
        v = decodeURIComponent(nv[1]);

        if (!parms.hasOwnProperty(n)) parms[n] = [];
        parms[n].push(nv.length === 2 ? v : null);
    }
    return parms;
}

function GetCurrentDate(){
    var data = new Date(),
        dia  = data.getDate().toString(),
        diaF = (dia.length == 1) ? '0'+dia : dia,
        mes  = (data.getMonth()+1).toString(), //+1 pois no getMonth Janeiro começa com zero.
        mesF = (mes.length == 1) ? '0'+mes : mes,
        anoF = data.getFullYear();
    return diaF+"/"+mesF+"/"+anoF + " as " + data.getHours() + ":" + data.getMinutes() + ":" + data.getSeconds() ;
}

function SavePdf(pdfBytes){

  var bytes = new Uint8Array(pdfBytes); // pass your byte response to this constructor

  var blob=new Blob([bytes], {type: "application/pdf"});// change resultByte to bytes

  var link=document.createElement('a');
  link.href=window.URL.createObjectURL(blob);
  link.download=filename;
  link.click();
}

function OnPdfLibLoadFonts(font, pdfDoc){
  const page = pdfDoc.addPage()
  const { width, height } = page.getSize()
  const fontSize = 25

  page.drawText('Assinado Digitalmente por:', {
    x: 40,
    y: height - 4 * fontSize,
    size: fontSize,
    font: font,
    color: PDFLib.rgb(0, 0, 0),
  })

  page.drawText('Nome:', {
    x: 40,
    y: height - 5 * fontSize,
    size: fontSize,
    font: font,
    color: PDFLib.rgb(0, 0, 0),
  })

  page.drawText('Email:', {
    x: 40,
    y: height - 6 * fontSize,
    size: fontSize,
    font: font,
    color: PDFLib.rgb(0, 0, 0),
  })

page.drawText('Em:'+ GetCurrentDate(), {
    x: 40,
    y: height - 7 * fontSize,
    size: fontSize,
    font: font,
    color: PDFLib.rgb(0, 0, 0),
  })
  pdfDoc.save().then((pdfBytes)=>SavePdf(pdfBytes)) 

}

function OnPdfLibLoad(pdfDoc){
  pdfDoc.embedFont(PDFLib.StandardFonts.Helvetica).then((font)=>OnPdfLibLoadFonts(font,pdfDoc))
  

}

// Executada quando o FileReader estiver com um arquivo carregado
function OnReaderReady(){
  // Recupera o array de buffer 
  var arrayBuffer = this.result

  console.log(arrayBuffer)

  PDFLib.PDFDocument.load(arrayBuffer).then((pdfDoc)=>OnPdfLibLoad(pdfDoc))
}

// Executada quando um arquivo é carregado
function OnLoadFile (){
	//Inicializa um leitor de arquivo
	var reader = new FileReader();
	//Quando o leitor de arquivo estiver pronto, faça:
	reader.onload = OnReaderReady

	//Ler o arquivo recebido
	reader.readAsArrayBuffer(this.files[0]);
}

//Cadastro de eventos
//Quando um arquivo for enviado, execute OnLoadFile()
$("input[type=file]").on("change",OnLoadFile);

console.log(window.location.href)
console.log(ParseURLParams(window.location.href))