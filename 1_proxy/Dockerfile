# Costruisce l'immagine Nignx con la nostra config, Istruzioni per costruire l'immagine.

# 1. Immagine Nginx ufficiale, leggera (alpine)
FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

# 4. (Nota) Non copiamo la cartella 'conf.d'
#    perché quella cartella è gestita da un VOLUME in docker-compose.yml.
#    Questo permette al "Generatore" (T5) di aggiungervi file
#    *a runtime*, senza dover ricostruire l'immagine. Essenzialmente creare un immagine secondaria parallela al resto.