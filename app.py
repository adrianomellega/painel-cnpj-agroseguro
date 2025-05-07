from flask import Flask, render_template, request
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "dados.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cnpj TEXT,
            nome TEXT,
            situacao TEXT,
            cnae TEXT,
            atividade TEXT,
            endereco TEXT,
            alerta TEXT,
            data_consulta TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_consulta(info):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO consultas (cnpj, nome, situacao, cnae, atividade, endereco, alerta, data_consulta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        info["cnpj"], info["nome"], info["situacao"], info["cnae"],
        info["atividade_principal"], info["endereco"], info["alerta"],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    conn.commit()
    conn.close()

def consultar_cnpj(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200 and data.get("status") != "ERROR":
            atividade = data.get("atividade_principal", [{}])[0].get("text", "").lower()
            alerta = ""
            if "açougue" in atividade or "carnes" in atividade:
                alerta = "Atividade incompatível com agrotóxicos."
            elif data.get("situacao") != "ATIVA":
                alerta = "CNPJ não está ativo na Receita Federal."

            resultado = {
                "nome": data.get("nome"),
                "cnpj": data.get("cnpj"),
                "situacao": data.get("situacao"),
                "atividade_principal": data.get("atividade_principal", [{}])[0].get("text"),
                "cnae": data.get("atividade_principal", [{}])[0].get("code"),
                "endereco": f"{data.get('logradouro')}, {data.get('bairro')}, {data.get('municipio')}-{data.get('uf')}, CEP {data.get('cep')}",
                "alerta": alerta
            }
            salvar_consulta(resultado)
            return resultado
        else:
            return {"erro": data.get("message", "Erro desconhecido.")}
    except Exception as e:
        return {"erro": str(e)}

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        cnpj = ''.join(filter(str.isdigit, request.form["cnpj"]))
        resultado = consultar_cnpj(cnpj)
    return render_template("index.html", resultado=resultado)

@app.route("/historico")
def historico():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consultas ORDER BY data_consulta DESC")
    consultas = cursor.fetchall()
    conn.close()
    return render_template("historico.html", consultas=consultas)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)


from flask import jsonify

@app.route("/api/consulta", methods=["POST"])
def api_consulta():
    data = request.get_json()
    cnpj = ''.join(filter(str.isdigit, data.get("cnpj", "")))
    if not cnpj:
        return jsonify({"erro": "CNPJ inválido ou ausente"}), 400

    resultado = consultar_cnpj(cnpj)
    return jsonify(resultado), 200 if "erro" not in resultado else 500


API_TOKEN = "AGROSEGURO123TOKEN"

@app.route("/api/consulta", methods=["POST"])
def api_consulta():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token != API_TOKEN:
        return jsonify({"erro": "Token inválido ou ausente"}), 401

    data = request.get_json()
    cnpj = ''.join(filter(str.isdigit, data.get("cnpj", "")))
    if not cnpj:
        return jsonify({"erro": "CNPJ inválido ou ausente"}), 400

    resultado = consultar_cnpj(cnpj)
    return jsonify(resultado), 200 if "erro" not in resultado else 500
