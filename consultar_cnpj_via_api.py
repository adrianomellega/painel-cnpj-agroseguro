import requests

API_URL = "http://localhost:5000/api/consulta"
API_TOKEN = "AGROSEGURO123TOKEN"

def consultar_cnpj(cnpj):
    payload = {"cnpj": cnpj}
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        dados = response.json()

        if response.status_code == 200:
            print("\n=== Resultado da Consulta ===")
            print("Empresa:", dados["nome"])
            print("CNPJ:", dados["cnpj"])
            print("Situação:", dados["situacao"])
            print("CNAE:", dados["cnae"], "-", dados["atividade_principal"])
            print("Endereço:", dados["endereco"])
            if dados["alerta"]:
                print("** ALERTA **", dados["alerta"])
        else:
            print("Erro:", dados.get("erro", "Erro desconhecido."))

    except Exception as e:
        print("Erro na conexão:", str(e))

if __name__ == "__main__":
    cnpj_input = input("Digite o CNPJ: ")
    consultar_cnpj(cnpj_input)
