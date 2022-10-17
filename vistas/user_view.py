import http

from app import app
from flask import request
from flask_inputs import Inputs
from modelos import User, db
from flask_inputs.validators import JsonSchema
from flask_jwt_extended import create_access_token

signup_schema = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'password1': {'type': 'string'},
        'password2': {'type': 'string'},
        'email': {'type': 'string'},
    },
    'required': ['username', 'password1', 'password2', 'email']
}

login_schema = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['username', 'password']
}


class SignupInputs(Inputs):
    json = [JsonSchema(schema=signup_schema)]


class LoginInputs(Inputs):
    json = [JsonSchema(schema=login_schema)]


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        inputs = SignupInputs(request)
        if inputs.validate():
            user = User.query.filter(User.email == request.json["email"]).first()
            if user is not None:
                return "El email ya se encuentra registrado. ", http.HTTPStatus.BAD_REQUEST.value

            if request.json["password1"] != request.json["password2"]:
                return "Las contraseñas no coinciden.", http.HTTPStatus.BAD_REQUEST.value

            new_user = User(email=request.json["email"], username=request.json["username"])
            new_user.set_password(request.json["password1"])
            db.session.add(new_user)
            db.session.commit()
            access_token = create_access_token(identity=new_user.id)
            return {"mensaje": "usuario creado exitosamente. ", "token": access_token}
        else:
            return {"mensaje": "\n".join(inputs.errors)}, http.HTTPStatus.BAD_REQUEST.value
    except Exception as e:
        return {"mensaje": e}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@app.route('/api/auth/login', methods=['POST'])
def login():
    inputs = LoginInputs(request)
    if inputs.validate():
        user = User.query.filter(User.username == request.json["username"]).first()
        if user is None or not user.check_password(request.json["password"]):
            return "Usuario o Contraseña incorrectos. ", http.HTTPStatus.UNAUTHORIZED.value

        access_token = create_access_token(identity=user.id)
        return {"mensaje": "Inicio de sesión exitoso. ", "token": access_token}

    else:
        return {"mensaje": "\n".join(inputs.errors)}, http.HTTPStatus.BAD_REQUEST.value

