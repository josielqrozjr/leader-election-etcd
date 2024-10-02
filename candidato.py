#!/usr/bin/env python3

#---------------------------------------------------
# Sistemas Distribuídos
# Code by Josiel Queiroz, Jr
# BCC - Noite
# Curitiba, 02 de outubro de 2024
#---------------------------------------------------


import etcd3
import sys
import random

import etcd3.events

# Conectar ao etcd
etcd = etcd3.client()

# Variáveis
lider_key = '/eleicao_lider'  # Chave para identificar o líder
lock_key = '/lock_lideranca'  # Lock para evitar condição de corrida
tempo_vida = 5  # Variável para armazenar o tempo usado no lock


def gerarIdCandidato():
    id = random.randint(10, 99)
    return str(id)


def tentarSerLider():
    print(f"Candidato {nome_candidato} --> Tentando a liderança...")
    
    # Tentar adquirir um lock antes de se tornar líder
    with etcd.lock(lock_key, ttl=tempo_vida):

        # Criar um tempo de expiração para a liderança
        tempo_lease = etcd.lease(tempo_vida) 

        # Armazenar o líder atual
        lider_atual = etcd.get(lider_key)[0]

        # Verificar se já existe um líder
        if lider_atual is not None:
            lider_atual = lider_atual.decode('utf-8')  # Decodificar o valor de bytes para string
            print(f"O candidato {lider_atual} é o LÍDER...\n")
            
            # Escutar as mudanças na eleição do líder
            escutarLider()
        else:
            # Não há líder, então o candidato atual se torna o líder
            etcd.put(lider_key, nome_candidato, lease=tempo_lease) # Eleger candidato como líder
            print(f"\nCandidato {nome_candidato} --> Eu sou o LÍDER!")
            tempo_lease.refresh()
            aguardarTerminar()
        


def aguardarTerminar():
    # Aguarda até que o usuário pressione qualquer tecla ou CTRL+C
    try:
        input(f"Candidato {nome_candidato} --> Pressione qualquer tecla para terminar\n")

    except KeyboardInterrupt:
        pass

    finally:
        # Deleta a chave de líder ao terminar, permitindo que outro candidato assuma
        etcd.delete(lider_key)
        print(f"Candidato {nome_candidato} --> Fim da liderança!")


def escutarLider():
    # Usa o watch para monitorar a chave
    print(f"Candidato {nome_candidato} --> Verificando mudanças na liderança...")
    eventos, parar_escuta = etcd.watch(lider_key)

    for evento in eventos:
        if isinstance(evento, etcd3.events.DeleteEvent):
            print(f"Candidato {nome_candidato} --> O líder atual saiu.")
            tentarSerLider()


# Nome único do candidato (passado como argumento do script)
nome_candidato = sys.argv[1] if len(sys.argv) > 1 else gerarIdCandidato()

if __name__ == "__main__":
    # Executa a tentativa de ser líder inicialmente
    tentarSerLider()

    # Aguarda indefinidamente para manter o processo ativo
    try:
        while True:
            tentarSerLider()
    except KeyboardInterrupt:
        print(f"{nome_candidato}: Encerrando processo.")
