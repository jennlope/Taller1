# #Actividad 5 - Aplicacion Template Method 2/2
from .db import get_col_clients
colClients = get_col_clients()

class RegistroUsuarioTemplate:
    def registrar(self, data):
        if not self.validar(data):
            return self.on_error(data)
        if self.existe_usuario(data):
            return self.on_usuario_existente(data)
        self.guardar(data)
        return self.on_success(data)

    def validar(self, data):
        raise NotImplementedError

    def existe_usuario(self, data):
        raise NotImplementedError

    def guardar(self, data):
        raise NotImplementedError

    def on_error(self, data):
        return {"registered": False, "error": True}

    def on_usuario_existente(self, data):
        return {"registered": False, "user_exists": True}

    def on_success(self, data):
        return {"registered": True}

class RegistroConMongo(RegistroUsuarioTemplate):
    def validar(self, data):
        # Validar campos (Basico)
        self.errores = {}
        campos = ["name", "surnames", "cedula", "phoneNumber", "email", "userName", "password"]
        for campo in campos:
            if not data.get(campo):
                self.errores[campo] = f"Por favor ingrese {campo}"
        return not self.errores

    def existe_usuario(self, data):
        for client in colClients.find():
            if (client['userName'] == data['userName'] or
                client['email'] == data['email'] or
                client['cedula'] == data['cedula']):
                return True
        return False

    def guardar(self, data):
        colClients.insert_one(data)

    def on_error(self, data):
        return {"registered": False, "error": True, "errores": self.errores}

    def on_usuario_existente(self, data):
        return {
            "registered": False,
            "user_exists": True,
            "errores": {
                "userName": "El usuario ya existe",
                "email": "El correo ya está registrado",
                "cedula": "La cédula ya está registrada"
            }
        }

class SignInTemplate:
    def autenticar(self, userName, password):
        user = self.buscar_usuario(userName)
        if not user:
            return self.on_user_not_found()

        if not self.validar_password(user, password):
            return self.on_password_incorrecta()

        self.registrar_usuario(user)
        return self.on_success(user)

    def buscar_usuario(self, userName): raise NotImplementedError
    def validar_password(self, user, password): raise NotImplementedError
    def registrar_usuario(self, user): pass  # opcional
    def on_user_not_found(self): return {"existAccount": False, "correctPassword": False, "inSignIn": False}
    def on_password_incorrecta(self): return {"existAccount": True, "correctPassword": False, "inSignIn": False}
    def on_success(self, user): return {"existAccount": True, "correctPassword": True, "inSignIn": True, "user": user}


colClients = get_col_clients()
userOnline = {}  # solo si no estás usando request.session aún

class SignInMongo(SignInTemplate):
    def buscar_usuario(self, userName):
        for user in colClients.find():
            if userName == user['userName'] or userName == user['email']:
                return user
        return None

    def validar_password(self, user, password):
        return password == user['password']

    def registrar_usuario(self, user):
        global userOnline
        userOnline = user  # si luego migras a session, aquí lo puedes cambiar

    def on_success(self, user):
        user["_id"] = str(user["_id"])  # Convertir ObjectId
        return {
            "existAccount": True,
            "correctPassword": True,
            "inSignIn": True,
            "user": user
        }