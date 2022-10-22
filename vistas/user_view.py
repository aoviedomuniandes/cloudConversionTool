import http
from flask import request
from modelos import User, db
from flask_jwt_extended import create_access_token
from flask import Blueprint


user_view = Blueprint("user_view", __name__,  url_prefix="/api/auth")


@user_view.route('/signup', methods=['POST'])
def signup():
    try:
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
       
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@user_view.route('/login', methods=['POST'])
def login():
        user = User.query.filter(User.username == request.json["username"]).first()
        if user is None or not user.check_password(request.json["password"]):
            return {"mensaje": "Usuario o Contraseña incorrectos."}, http.HTTPStatus.UNAUTHORIZED.value

        access_token = create_access_token(identity=user.id)
        return {"mensaje": "Inicio de sesión exitoso.", "token": access_token}

 
