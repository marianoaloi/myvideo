# For MIME types
import magic
import os


mime = magic.Magic(mime=True)

ll = set()
base = '/mnt/huge/WhatsApp Video/L'
for f in  os.listdir(base):
    ll.add(mime.from_file(os.path.join(base,f)))

print(ll)