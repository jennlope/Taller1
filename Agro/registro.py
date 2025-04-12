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