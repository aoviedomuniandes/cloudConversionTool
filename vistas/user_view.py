import http
from flask import request
from flask_inputs import Inputs
from app import app
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


class SignupInputs(Inputs):
    json = [JsonSchema(schema=signup_schema)]


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        inputs = SignupInputs(request)
        if inputs.validate():
            user = User.query.filter(User.email == request.json["email"]).first()
            if user is not None:
                return {"mensaje": "El email ya se encuentra registrado."}, http.HTTPStatus.BAD_REQUEST.value

            if request.json["password1"] != request.json["password2"]:
                return {"mensaje": "Las contraseñas no coinciden."}, http.HTTPStatus.BAD_REQUEST.value

            new_user = User(email=request.json["email"], username=request.json["username"])
            new_user.set_password(request.json["password1"])
            db.session.add(new_user)
            db.session.commit()
            access_token = create_access_token(identity=new_user.id)
            return {"mensaje": "usuario creado exitosamente.", "token": access_token}
        else:
            return {"mensaje": "\n".join(inputs.errors)}, http.HTTPStatus.BAD_REQUEST.value
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value
