from hashlib import md5
import random

f=open("file.txt","r",encoding = "utf-8")
data=f.read()
f.close()
Hash=md5(str("maria").encode('utf-8')).hexdigest()
out=open("out.txt","w")
out.write(Hash)
out.close()