from functools import wraps
from flask import request, jsonify, current_app, g
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 1. Cerca PRIMA nel Cookie (La via maestra se usi HttpOnly cookies)
        token = request.cookies.get('sf_access_token')

        # 2. Fallback sull'Header (per chiamate HTMX o API dirette)
        auth_header = request.headers.get('Authorization')
        if not token and auth_header:
            # L'header arriva tipicamente come "Bearer eyJhbGciOi..."
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                print(f"DEBUG AUTH: Token estratto dall'header Authorization")
            else:
                print(f"DEBUG AUTH: Formato Authorization header non valido: {auth_header}")

        if not token:
            print("DEBUG AUTH: Nessun token trovato (né cookie né header).")
            # Se sei in un browser, reindirizza al login di Django o mostra errore
            if 'text/html' in request.accept_mimetypes:
                 return "<h1>Accesso Negato</h1><p>Esegui il login dalla Home Page.</p>", 401
            return jsonify({'message': 'Token mancante'}), 401

        try:
            # Recupera la SECRET_KEY condivisa con Django
            secret_key = current_app.config.get('DJANGO_SECRET_KEY')
            
            if not secret_key:
                print("ERRORE CRITICO: DJANGO_SECRET_KEY non configurata su Flask!")
                return jsonify({'message': 'Errore di configurazione del server'}), 500

            # Decodifica e validazione standard
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            g.user_id = payload.get('user_id')
            
            print(f"DEBUG AUTH: Autenticazione riuscita per user_id: {g.user_id}")
        
        except jwt.ExpiredSignatureError:
            print("DEBUG AUTH: Il token è scaduto.")
            return jsonify({'message': 'Token scaduto'}), 401
            
        except jwt.InvalidTokenError as e:
            print(f"DEBUG AUTH: Token non valido. Motivo: {str(e)}")
            return jsonify({'message': f'Token non valido: {str(e)}'}), 401
            
        except Exception as e:
            print(f"DEBUG AUTH: Errore imprevisto durante la validazione: {str(e)}")
            return jsonify({'message': f'Errore Token: {str(e)}'}), 401

        return f(*args, **kwargs)

    return decorated