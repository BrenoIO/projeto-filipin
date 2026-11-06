from flask import Flask, request, jsonify, render_template
from database import engine, Base, get_db
from models import Aluno
from sqlalchemy.orm import Session

# Cria as tabelas no banco de dados automaticamente ao iniciar
Base.metadata.create_all(bind=engine)

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/alunos", methods=["POST"])
def cadastrar_aluno():
    dados = request.json
    db: Session = next(get_db())
    try:
        novo_aluno = Aluno(
            nome=dados.get("nome"),
            faixa=dados.get("faixa"),
            idade=dados.get("idade"),
            responsavel=dados.get("responsavel"),
            observacao=dados.get("observacao", "")
        )
        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_aluno)
        return jsonify({"message": "Aluno cadastrado com sucesso!", "id": novo_aluno.id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()

@app.route("/api/alunos", methods=["GET"])
def listar_alunos():
    db: Session = next(get_db())
    try:
        alunos = db.query(Aluno).all()
        resultado = [{
            "id": a.id,
            "nome": a.nome,
            "faixa": a.faixa,
            "idade": a.idade,
            "responsavel": a.responsavel,
            "observacao": a.observacao
        } for a in alunos]
        return jsonify(resultado)
    finally:
        db.close()

if __name__ == "__main__":
    app.run(debug=True)