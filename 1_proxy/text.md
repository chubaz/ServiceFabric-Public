# Bypass di Django. 

## Nginx deve rimanere al di fuori della logica Django e Backend. 

**Perché l'autenticazione deve avvenire senza bypass da parte di Nginx.**

Nginx non deve intromettersi e unicamente servire i due lati:
- Django
- cliente

Nginx rappresenta l'ultimo sportello interno di cio che le macchine e gli utenti esterni possono vedere. 

I seguenti elementi non sono esposti a Nginx in un formato che non sia criptico:
- informazioni confidenziali degli utenti, del server e di altro
- i comandi che possono rivelare informazioni, strutture, scripts, logiche, macchine e networks delicati e di proprietà. 

La dinamica principale sono l'accesso diretto di Nginx ai file, i protocolli di comunicazione fra Nginx e Django, e Nginx con la rete e i clienti. 

Ci deve perciò essere un ultima separazione fra Django e le Applicazioni Flask, per evitare di esporre i software e i dati di proprietà e confidenziali, e la separazione fra le applicazioni di Flask e gli scripts fondamentali del loro funzionamento. Questa separazione avviene in maniera sempra piu marcata per evitare una realizzazione definitiva. Tali logiche rendono la presa di controllo del sistema sempe piu complicato.

Quella che inizia come una separazione formale puo divenire in effetti una separazione definitiva, che pero ha un fulcro fisico in dispositivi adeguati. Come rendere dei dispositivi appositi per visualizzare l'intero ecosistema di riferimento diventa percio la chiave proteggerli da vulnerabilità.

Mantenere una separazione digitale fra le componenti diventa fondamentale per poter attuare una separazione fisica efficace da vulnerabilità del sistema, di chi lo gestisce, etc.

Possedere almeno una chiave del ecosistema perciò rende le persone immuni da attacchi di chi lo vuole hackerare.

Come si possono creare delle chiavi in un ecosistema soft che pero mantiene la sua sicurezza attraverso i dispositivi?

La domanda si volge al contrario come possono i dispositivi con degli accessi integrati riuscire a proteggere le persone? Percio quali caratteristiche rendono le persone importanti da difendere? Come si permette a una difesa di essere efficace attraverso i dispositivi?

- Quali persone?
- Quali dispositivi?
- Con quali visualizzazioni complessive?
- Con quali protocolli di comunicazione fra visualizzazioni?
- Quali procedure di salvaguardie delle visualizzazioni?
- Quali procedure di separazione da ulteriori unioni fra visualizzazioni?
- Come si puo evitare che qualcuno ristabilisca lo sviluppo di tali visualizzazioni?

In che maniera una difesa cyber-fisica in via di sviluppo può compromettere l'efficacia e l'autorità di quella esistente?
Come e chi può determinare l'efficacia, l'estensione e la composizione di questa difesa cyber-fisica?

- Il sistema di difesa dovrebbe riuscire a sovrapporsi in tempo a qualunque forma di preparazione ed organizzazione di come attaccare la persona? 
- Come può il sistema anticipare tale atto? 
- Quali falle del sistema di difesa creano i presupposti per degli attacchi spontanei, casuali?

Quale modo puo prevenire tale atto di violenza, di imposizione, di ostacolazione, di torto o di sinistro nei confronti delle persone? Un modo che può far parte dell'ecosistema soft?

Protezione Soft, Protezione Cyber-Fisica.




Rendere un file eseguibile nel network, permette agli altri build di eseguirlo, ma non di modificarlo (a meno di Linux security vulnerability), questo permette agli altri servizi di usare lo script a proprio piacimento, che crea durante lo sleep una connessione (UDP e non TCP), inoltre crea le migrazioni e l'upload di file statici. E la creazione senza sosta (in un network acceso) di un server wsgi di Django. Delle infiltrazioni nel network potrebbe creare i presupposti per approcciare il source code di Django e i dati annessi ad esso.

Questo richiede sicurezza presenziale per la gestione di Django, e il controllo dei movimento nei dati e l'accesso a file confidenziali.



